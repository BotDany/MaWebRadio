import argparse
import contextlib
import io
import json
import re
import ssl
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Optional, Tuple
from urllib.parse import urlparse
from urllib.parse import quote
import xml.etree.ElementTree as ET

import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


RADIOS = [
    ("100% Radio 80", "http://100radio-80.ice.infomaniak.ch/100radio-80-128.mp3"),
    ("Bide Et Musique", "https://relay1.bide-et-musique.com:9300/bm.mp3"),
    ("Chansons Oubliées Où Presque", "https://manager7.streamradio.fr:2850/stream"),
    ("Chante France-80s", "https://chantefrance80s.ice.infomaniak.ch/chantefrance80s-128.mp3"),
    ("Flash 80 Radio", "http://manager7.streamradio.fr:1985/stream"),
    ("Génération Dorothée", "https://stream.votreradiosurlenet.eu/generationdorothee.mp3"),
    ("Générikds", "https://www.radioking.com/play/generikids"),
    ("Made In 80", "https://listen.radioking.com/radio/260719/stream/305509"),
    ("Mega Hits", "https://playerservices.streamtheworld.com/api/livestream-redirect/MEGA_HITSAAC.aac"),
    ("Nostalgie-Les 80 Plus Grand Tubes", "https://streaming.nrjaudio.fm/ouwg8usk6j4d"),
    ("Nostalgie-Les Tubes 80 N1", "https://streaming.nrjaudio.fm/ouo6im7nfibk"),
    ("Radio Comercial", "https://stream-icy.bauermedia.pt/comercial.mp3"),
    ("Radio Gérard", "https://radiosurle.net:8765/radiogerard"),
    ("RTL", "http://streaming.radio.rtl.fr/rtl-1-44-128"),
    ("Superloustic", "https://radio6.pro-fhi.net/live/SUPERLOUSTIC"),
    ("Supernana", "https://radiosurle.net:8765/showsupernana"),
    ("Top 80 Radio", "https://securestreams6.autopo.st:2321/"),
]


def _normalize_text(value: str) -> str:
    if not isinstance(value, str):
        return ""
    s = value.strip()
    if not s:
        return ""
    if "Ã" in s or "Â" in s:
        try:
            return s.encode("latin-1", errors="ignore").decode("utf-8", errors="ignore").strip()
        except Exception:
            return s
    return s


@dataclass
class RadioMetadata:
    station: str
    title: str
    artist: str
    cover_url: str = ""


class CustomHttpAdapter(requests.adapters.HTTPAdapter):
    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=self.ssl_context,
        )


def _parse_centpourcent_metas_payload(text: str) -> Optional[Tuple[str, str, str]]:
    if not isinstance(text, str) or not text:
        return None

    s = text.strip()
    if s.startswith("data:"):
        for line in s.splitlines():
            line = line.strip()
            if not line.startswith("data:"):
                continue
            payload = line[len("data:") :].strip()
            if not payload:
                continue
            try:
                obj = json.loads(payload)
            except Exception:
                return None
            if not isinstance(obj, dict):
                return None
            artist = _normalize_text(str(obj.get("artist") or ""))
            title = _normalize_text(str(obj.get("title") or ""))
            cover = _normalize_text(str(obj.get("cover") or obj.get("coverUrl") or ""))
            if not cover:
                cover_id = _normalize_text(str(obj.get("coverId") or ""))
                # Observé dans l'app : coverId = "330.../m/.../170290..."
                # La forme exacte de l'URL image peut varier; on renvoie une URL plausible.
                if cover_id:
                    cover_id = "".join(cover_id.split())
                    cover = f"https://www.centpourcent.com/ws/cover/{quote(cover_id, safe='/')}"
            if title and artist:
                return title, artist, cover
        return None

    if s.startswith("{"):
        try:
            obj = json.loads(s)
        except Exception:
            return None
        if not isinstance(obj, dict):
            return None
        artist = _normalize_text(str(obj.get("artist") or ""))
        title = _normalize_text(str(obj.get("title") or ""))
        cover = _normalize_text(str(obj.get("cover") or obj.get("coverUrl") or ""))
        if not cover:
            cover_id = _normalize_text(str(obj.get("coverId") or ""))
            if cover_id:
                cover_id = "".join(cover_id.split())
                cover = f"https://www.centpourcent.com/ws/cover/{quote(cover_id, safe='/')}"
        if title and artist:
            return title, artist, cover

    return None


def _parse_radiocomercial_radioinfo_xml(text: str) -> Optional[Tuple[str, str, str]]:
    s = _normalize_text(text)
    if not s:
        return None
    if not (s.startswith("<?xml") or s.startswith("<RadioInfo")):
        return None
    try:
        root = ET.fromstring(s)
    except Exception:
        return None

    # Extraire les informations de la table (musique)
    table = root.find(".//Table")
    song = ""
    artist = ""
    
    if table is not None:
        song_el = table.find(".//DB_SONG_NAME")
        title_el = table.find(".//DB_DALET_TITLE_NAME")
        artist_el = table.find(".//DB_DALET_ARTIST_NAME")
        
        # Priorité: DB_SONG_NAME > DB_DALET_TITLE_NAME
        if song_el is not None and song_el.text:
            song = _normalize_text(song_el.text)
        elif title_el is not None and title_el.text:
            song = _normalize_text(title_el.text)
            
        if artist_el is not None and artist_el.text:
            artist = _normalize_text(artist_el.text)
    
    # Si pas de musique, extraire les infos de l'animateur
    if not song or not artist:
        animador = root.find(".//AnimadorInfo")
        if animador is not None:
            host_el = animador.find(".//TITLE")
            show_el = animador.find(".//SHOW_NAME")
            
            if host_el is not None and host_el.text:
                artist = _normalize_text(host_el.text)
            if show_el is not None and show_el.text:
                song = _normalize_text(show_el.text)
            else:
                song = "En direct"
    
    cover_url = ""
    # Essayer de récupérer l'image de l'animateur
    animador = root.find(".//AnimadorInfo")
    if animador is not None:
        img_el = animador.find(".//IMAGE")
        if img_el is not None and img_el.text:
            img = _normalize_text(img_el.text)
            if img and not img.startswith("http"):
                img = f"https://radiocomercial.pt{img}"
            cover_url = img
    
    if not artist:
        artist = "Radio Comercial"
    if not song:
        song = "En direct"
    
    return song, artist, cover_url


def _fetch_nrjaudio_wr_api3_tracklist_metadata(session: requests.Session, radio_id: str, station_name: str) -> Optional[RadioMetadata]:
    try:
        headers = {
            "Accept": "application/json",
            "Accept-Language": "fr-FR,fr;q=0.9",
            "User-Agent": "NostalgieApp/9490 CFNetwork/3826.500.131 Darwin/24.5.0",
            "X-Device-Category": "mobile",
            "X-App-Id": "fr_nosta_ios",
        }
        r = session.get(
            f"https://players.nrjaudio.fm/wr_api3/v1/webradios/{radio_id}/tracklist",
            params={"timeshift_slot": 1},
            timeout=6,
            headers=headers,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        if not isinstance(data, dict):
            return None
        data2 = data.get("data")
        if not isinstance(data2, dict):
            return None
        current = data2.get("current")
        if not isinstance(current, dict):
            return None
        title = _normalize_text(str(current.get("title") or ""))
        artist = _normalize_text(str(current.get("artist") or ""))
        cover_url = _normalize_text(str(current.get("artwork_image") or ""))
        if not title or not artist:
            return None
        return RadioMetadata(station=station_name, title=title, artist=artist, cover_url=cover_url)
    except Exception:
        return None


def _parse_icecast_title(title: str) -> Optional[Tuple[str, str]]:
    t = _normalize_text(title)
    if not t:
        return None
    if " - " in t:
        a, s = t.split(" - ", 1)
        a = _normalize_text(a)
        s = _normalize_text(s)
        if a and s:
            return s, a
    return None


def _fetch_infomaniak_icecast_status(session: requests.Session, stream_url: str, station_name: str) -> Optional[RadioMetadata]:
    try:
        if "ice.infomaniak.ch" not in (stream_url or ""):
            return None

        try:
            parsed = urlparse(stream_url)
            host = parsed.netloc or ""
        except Exception:
            host = ""
        if not host:
            return None

        bases = [
            f"https://{host}",
            f"http://{host}",
        ]
        candidates = []
        for base in bases:
            candidates.extend([
                f"{base}/status-json.xsl",
                f"{base}/status.xsl",
                f"{base}/7.html",
            ])

        headers = {
            "User-Agent": "AIM",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "fr-FR,fr;q=0.9",
            "Accept-Encoding": "identity",
            "Connection": "close",
            "Referer": "apli",
        }

        for url in candidates:
            try:
                r = session.get(url, timeout=(3, 3), headers=headers)
            except Exception:
                continue

            if r.status_code != 200:
                continue

            ct = str(r.headers.get("content-type") or "").lower()

            # status-json.xsl
            if "json" in ct or (r.text or "").lstrip().startswith("{"):
                try:
                    data = r.json()
                except Exception:
                    continue

                if not isinstance(data, dict):
                    continue
                icestats = data.get("icestats")
                if not isinstance(icestats, dict):
                    continue
                source = icestats.get("source")

                source_obj = None
                if isinstance(source, dict):
                    source_obj = source
                elif isinstance(source, list) and source:
                    for s in source:
                        if isinstance(s, dict) and s.get("listenurl") and "100radio-80" in str(s.get("listenurl")):
                            source_obj = s
                            break
                    if source_obj is None:
                        for s in source:
                            if isinstance(s, dict) and "title" in s:
                                source_obj = s
                                break

                if not isinstance(source_obj, dict):
                    continue

                title_field = source_obj.get("title") or source_obj.get("server_name") or ""
                parsed = _parse_icecast_title(str(title_field))
                if parsed:
                    title, artist = parsed
                    return RadioMetadata(station=station_name, title=title, artist=artist, cover_url="")

            # 7.html (Shoutcast-like) : often "<body>Artist - Title,StreamName</body>"
            if url.endswith("/7.html") and isinstance(r.text, str):
                raw = r.text
                raw = raw.replace("\r", " ").replace("\n", " ")
                raw = raw.split("<body>")[-1].split("</body>")[0]
                raw = raw.split(",")[0]
                parsed = _parse_icecast_title(raw)
                if parsed:
                    title, artist = parsed
                    return RadioMetadata(station=station_name, title=title, artist=artist, cover_url="")

        return None
    except Exception:
        return None


def _fetch_100radio_ws_metas(session: requests.Session, station_name: str) -> Optional[RadioMetadata]:
    try:
        ids = [
            "3301185310276687502",
        ]
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/plain, */*",
            "Connection": "close",
        }

        for id_ in ids:
            url = f"https://www.centpourcent.com/ws/metas?id={id_}"
            try:
                r = session.get(url, timeout=(3, 6), headers=headers, stream=True)
            except Exception:
                continue

            if r.status_code != 200:
                continue

            ct = str(r.headers.get("content-type") or "").lower()

            # ws/metas renvoie souvent du SSE (text/event-stream) : `data: {...}`
            if "event-stream" in ct:
                try:
                    for _ in range(50):
                        line_b = next(r.iter_lines(decode_unicode=False), None)
                        if not line_b:
                            continue
                        line = line_b.decode("utf-8", errors="ignore").strip()
                        parsed = _parse_centpourcent_metas_payload(line)
                        if not parsed:
                            continue
                        title, artist, cover_url = parsed
                        return RadioMetadata(station=station_name, title=title, artist=artist, cover_url=cover_url)
                except Exception:
                    pass
                finally:
                    try:
                        r.close()
                    except Exception:
                        pass
                continue

            # JSON/texte classique
            try:
                text = r.text or ""
            finally:
                try:
                    r.close()
                except Exception:
                    pass

            parsed = _parse_centpourcent_metas_payload(text)
            if not parsed:
                continue

            title, artist, cover_url = parsed
            return RadioMetadata(station=station_name, title=title, artist=artist, cover_url=cover_url)

        return None
    except Exception:
        return None


class RadioFetcher:
    def __init__(self):
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.options |= 0x4

        self.session = requests.Session()
        self.session.trust_env = False
        self.session.verify = False

        adapter = CustomHttpAdapter(ctx)
        self.session.mount("https://", adapter)

        retry_strategy = Retry(
            total=2,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
        )
        self.session.mount("http://", HTTPAdapter(max_retries=retry_strategy))
        self.session.mount("https://", HTTPAdapter(max_retries=retry_strategy))

        self.cache = {}
        self.cache_timeout_s = 10

    def _parse_hls_metadata(self, content: str, station_name: str) -> Optional[RadioMetadata]:
        """Parse les métadonnées XML depuis un flux HLS"""
        try:
            # Chercher les métadonnées XML dans les segments EXTINF
            xml_pattern = r'#EXTINF:.*?(<\?xml.*?</RadioInfo>)'
            xml_matches = re.findall(xml_pattern, content, re.DOTALL)
            
            if xml_matches:
                # Prendre le premier XML trouvé
                xml_content = xml_matches[0]
                
                # Parser le XML
                try:
                    root = ET.fromstring(xml_content)
                    metadata = {}
                    
                    # Extraire les informations de la table
                    table = root.find('.//Table')
                    if table is not None:
                        metadata['song'] = table.findtext('.//DB_SONG_NAME', '').strip()
                        metadata['artist'] = table.findtext('.//DB_DALET_ARTIST_NAME', '').strip()
                        metadata['album'] = table.findtext('.//DB_ALBUM_NAME', '').strip()
                    
                    # Extraire les informations de l'animateur
                    animador = root.find('.//AnimadorInfo')
                    if animador is not None:
                        metadata['host'] = animador.findtext('.//TITLE', '').strip()
                        metadata['show'] = animador.findtext('.//SHOW_NAME', '').strip()
                    
                    # Créer l'objet RadioMetadata
                    if metadata.get('song') and metadata.get('artist'):
                        return RadioMetadata(
                            station=station_name,
                            title=metadata['song'],
                            artist=metadata['artist'],
                            cover_url=self._get_album_cover(metadata['artist'], metadata['song'])
                        )
                    elif metadata.get('host'):
                        return RadioMetadata(
                            station=station_name,
                            title=metadata.get('show', 'En direct'),
                            artist=metadata['host'],
                            cover_url="https://radiocomercial.pt/wp-content/uploads/2020/06/cropped-rc-favicon-192x192.png"
                        )
                        
                except ET.ParseError as e:
                    print(f"Erreur parsing XML HLS: {e}")
                    # Fallback: extraire avec des regex
                    try:
                        song_match = re.search(r'<DB_SONG_NAME>(.*?)</DB_SONG_NAME>', xml_content)
                        artist_match = re.search(r'<DB_DALET_ARTIST_NAME>(.*?)</DB_DALET_ARTIST_NAME>', xml_content)
                        host_match = re.search(r'<TITLE>(.*?)</TITLE>', xml_content)
                        
                        if song_match and artist_match:
                            return RadioMetadata(
                                station=station_name,
                                title=song_match.group(1).strip(),
                                artist=artist_match.group(1).strip(),
                                cover_url=self._get_album_cover(artist_match.group(1).strip(), song_match.group(1).strip())
                            )
                        elif host_match:
                            return RadioMetadata(
                                station=station_name,
                                title="En direct",
                                artist=host_match.group(1).strip(),
                                cover_url="https://radiocomercial.pt/wp-content/uploads/2020/06/cropped-rc-favicon-192x192.png"
                            )
                    except Exception:
                        pass
                        
            return None
            
        except Exception as e:
            print(f"Erreur parsing HLS: {e}")
            return None

    def _get_album_cover(self, artist: str, title: str) -> str:
        """Récupère la pochette d'album via iTunes API"""
        try:
            import urllib.parse
            query = urllib.parse.quote_plus(f"{artist} {title}")
            url = f"https://itunes.apple.com/search?term={query}&entity=song&limit=1"
            response = self.session.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    return data['results'][0].get('artworkUrl100', '').replace('100x100', '600x600')
        except Exception:
            pass
        return ""

    def _get_icy_metadata(self, url: str, station_name: str) -> RadioMetadata:
        try:
            headers = {
                "Icy-MetaData": "1",
                "Accept": "*/*",
            }

            # Certains flux Infomaniak renvoient/formatent mieux les métadonnées ICY
            # quand on imite le client officiel.
            if "ice.infomaniak.ch" in (url or ""):
                headers.update({
                    "User-Agent": "AIM",
                    "Referer": "apli",
                    "Accept-Encoding": "identity",
                    "Accept-Language": "fr-FR,fr;q=0.9",
                    "Connection": "keep-alive",
                    "icy-metadata": "1",
                })
            else:
                headers.update({
                    "User-Agent": "VLC/3.0.18",
                    "Connection": "close",
                })

            r = self.session.get(url, stream=True, timeout=6, headers=headers)
            title = "En direct"
            artist = station_name
            cover_url = ""

            if "icy-metaint" in r.headers:
                meta_int = int(r.headers["icy-metaint"])
                for _ in range(6):
                    r.raw.read(meta_int)
                    meta_len_b = r.raw.read(1)
                    if not meta_len_b:
                        break
                    meta_len = ord(meta_len_b) * 16
                    if meta_len <= 0:
                        continue
                    meta = r.raw.read(meta_len).rstrip(b"\x00").decode("utf-8", errors="ignore")
                    if "StreamTitle=" not in meta:
                        continue
                    stream_title = meta.split("StreamTitle=")[1].split(";")[0].strip("'\"")
                    stream_title = _normalize_text(stream_title)
                    if not stream_title:
                        continue
                    if " - " in stream_title:
                        a, t = stream_title.split(" - ", 1)
                        artist = _normalize_text(a)
                        title = _normalize_text(t)
                    else:
                        # Certains flux renvoient un XML complet dans StreamTitle (ex: Radio Comercial)
                        parsed_xml = _parse_radiocomercial_radioinfo_xml(stream_title)
                        if parsed_xml:
                            title, artist, cover_url2 = parsed_xml
                            if cover_url2:
                                cover_url = cover_url2
                        else:
                            title = stream_title
                    if title and title.lower() != "en direct":
                        break

            r.close()
            return RadioMetadata(station=station_name, title=title or "En direct", artist=artist or station_name, cover_url=cover_url)
        except Exception:
            return RadioMetadata(station=station_name, title="En direct", artist=station_name, cover_url="")

    def get_metadata(self, station_name: str, url: str) -> RadioMetadata:
        cache_key = f"{station_name}:{url}"
        now = time.time()
        hit = self.cache.get(cache_key)
        if hit and now - hit[1] < self.cache_timeout_s:
            return hit[0]

        md: Optional[RadioMetadata] = None

        # Spécial: Radio Comercial - essayer d'abord le parsing HLS
        if "radio comercial" in station_name.lower() or "comercial" in station_name.lower():
            # Si c'est une URL HLS, essayer de parser le contenu
            if ".m3u8" in url:
                try:
                    response = self.session.get(url, timeout=10)
                    if response.status_code == 200:
                        hls_content = response.text
                        md = self._parse_hls_metadata(hls_content, station_name)
                        if md:
                            self.cache[cache_key] = (md, now)
                            return md
                except Exception:
                    pass
            
            # Sinon, essayer avec le flux ICY standard qui contient déjà les métadonnées XML
            md = self._get_icy_metadata(url, station_name)
            self.cache[cache_key] = (md, now)
            return md

        if station_name.strip().lower() == "100% radio 80":
            md = _fetch_100radio_ws_metas(self.session, station_name)
            if md:
                self.cache[cache_key] = (md, now)
                return md

            md = _fetch_infomaniak_icecast_status(self.session, url, station_name)
            if md:
                self.cache[cache_key] = (md, now)
                return md

        if "nostalgie" in station_name.lower():
            mapping = {
                "Nostalgie-Les 80 Plus Grand Tubes": "1640",
                "Nostalgie-Les Tubes 80 N1": "1283",
            }
            rid = mapping.get(station_name)
            if rid:
                md = _fetch_nrjaudio_wr_api3_tracklist_metadata(self.session, rid, station_name)
                if md:
                    self.cache[cache_key] = (md, now)
                    return md

        md = self._get_icy_metadata(url, station_name)
        self.cache[cache_key] = (md, now)
        return md


def _cli_json_once(station_name: str, url: str) -> int:
    try:
        fetcher = RadioFetcher()

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            md = fetcher.get_metadata(station_name, url)

        noisy = buf.getvalue()
        if noisy:
            sys.stderr.write(noisy)

        payload = {
            "station": md.station,
            "title": md.title,
            "artist": md.artist,
            "cover_url": md.cover_url,
        }
        print(json.dumps(payload, ensure_ascii=False))
        return 0
    except Exception as e:
        sys.stderr.write(str(e))
        sys.stderr.write("\n")
        return 1


def _print_supported_stations() -> None:
    # Stations avec traitement spécifique (API temps réel)
    print("100% Radio 80")
    print("Nostalgie-Les 80 Plus Grand Tubes")
    print("Nostalgie-Les Tubes 80 N1")


def _print_all_radios() -> None:
    for name, url in RADIOS:
        print(f"{name} | {url}")


def _run_all_radios() -> int:
    fetcher = RadioFetcher()

    def _one(item: Tuple[str, str]) -> Tuple[str, str, RadioMetadata]:
        name, url = item
        md = fetcher.get_metadata(name, url)
        return name, url, md

    max_workers = min(8, max(1, len(RADIOS)))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_one, item) for item in RADIOS]
        for fut in as_completed(futures):
            try:
                name, url, md = fut.result()
                print(f"{name} | {url}")
                title = _normalize_text(md.title)
                artist = _normalize_text(md.artist)

                if not title or title.lower() == "en direct":
                    print("  En direct")
                elif artist and artist.lower() != _normalize_text(name).lower():
                    print(f"  {artist} - {title}")
                else:
                    print(f"  {title}")
                if md.cover_url:
                    print(f"  {md.cover_url}")
            except Exception as e:
                print(f"ERROR | {str(e)[:200]}")

    return 0


def _entrypoint() -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--list-all", action="store_true")
    parser.add_argument("--run-all", action="store_true")
    parser.add_argument("--station", type=str, default="")
    parser.add_argument("--url", type=str, default="")
    args, _ = parser.parse_known_args()

    if args.list:
        _print_supported_stations()
        return 0

    if args.list_all:
        _print_all_radios()
        return 0

    if args.run_all:
        return _run_all_radios()

    if args.json:
        if not args.station or not args.url:
            sys.stderr.write("Missing --station or --url\n")
            return 2
        return _cli_json_once(args.station, args.url)

    sys.stderr.write("Use --json --station <name> --url <stream_url>\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(_entrypoint())
