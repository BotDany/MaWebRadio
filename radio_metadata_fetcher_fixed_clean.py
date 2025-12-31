import argparse
import contextlib
import io
import json
import re
import ssl
import sys
import time
import os
import signal
import threading
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

# Import BeautifulSoup pour parser le HTML de Bide Et Musique
try:
    from bs4 import BeautifulSoup
except ImportError:
    print("BeautifulSoup non installé. Pour Bide Et Musique: pip install beautifulsoup4")
    BeautifulSoup = None

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Fichier de cache pour l'historique
HISTORY_CACHE_FILE = "radio_history_cache.json"

# Variable globale pour arrêter proprement le monitoring
stop_monitoring = False


RADIOS = [
    ("100% Radio 80", "http://100radio-80.ice.infomaniak.ch/100radio-80-128.mp3"),
    ("Bide Et Musique", "https://relay1.bide-et-musique.com:9300/bm.mp3"),
    ("Chansons Oubliées Où Presque", "https://manager7.streamradio.fr:2850/stream"),
    ("Chante France-80s", "https://chantefrance80s.ice.infomaniak.ch/chantefrance80s-128.mp3"),
    ("Top 80 Radio", "https://securestreams6.autopo.st:2321/stream.mp3"),
    ("Rádio São Miguel", "https://nl.digitalrm.pt:8140/stream"),
    ("RFM Portugal", "https://29043.live.streamtheworld.com/RFMAAC.aac?dist=triton-widget&tdsdk=js-2.9&swm=false&pname=tdwidgets&pversion=2.9&banners=300x250%2C728x90&gdpr=1&gdpr_consent=CQdTAsAQdTAsAAKA9APTCLFgAAAAAAAAAB6YAAAXsgLAA4AGaAZ8BHgCVQHbAQUAjSBIgCSgEowJkgUWAo4BVICrIFYAK5gV9AtWBbwC9gAA.IAAA.YAAAAAAAAAAA&burst-time=15"),
    ("Génération Dorothée", "https://stream.votreradiosurlenet.eu/generationdorothee.mp3"),
    ("Générikds", "https://listen.radioking.com/radio/497599/stream/554719"),
    ("Made In 80", "https://listen.radioking.com/radio/260719/stream/305509"),
    ("Mega Hits", "https://playerservices.streamtheworld.com/api/livestream-redirect/MEGA_HITSAAC_SC?csegid=2&dist=rmultimedia_apps&gdpr=1&bundle-id=pt.megahits.ios"),
    ("Nostalgie-Les 80 Plus Grand Tubes", "https://streaming.nrjaudio.fm/ouwg8usk6j4d"),
    ("Nostalgie-Les Tubes 80 N1", "https://streaming.nrjaudio.fm/ouo6im7nfibk"),
    ("Radio Comercial", "https://stream-icy.bauermedia.pt/comercial.mp3"),
    ("Radio Gérard", "https://radiosurle.net:8765/radiogerard"),
    ("RFM", "https://29043.live.streamtheworld.com/RFMAAC.aac?dist=triton-widget&tdsdk=js-2.9&swm=false&pname=tdwidgets&pversion=2.9&banners=300x250%2C728x90&gdpr=1&gdpr_consent=CQdTAsAQdTAsAAKA9APTCLFgAAAAAAAAAB6YAAAXsgLAA4AGaAZ8BHgCVQHbAQUAjSBIgCSgEowJkgUWAo4BVICrIFYAK5gV9AtWBbwC9gAA.IAAA.YAAAAAAAAAAA&burst-time=15"),
    ("RTL", "http://streaming.radio.rtl.fr/rtl-1-44-128"),
    ("Superloustic", "https://radio6.pro-fhi.net/live/SUPERLOUSTIC"),
    ("Supernana", "https://radiosurle.net:8765/showsupernana"),
    ("Top 80 Radio", "https://top80.ice.infomaniak.ch/top80-128.mp3"),
]

# Dictionnaire des logos par défaut pour chaque radio
RADIO_LOGOS = {
    "100% Radio 80": "https://www.centpourcent.com/img/logo-100radio80.png",
    "Bide Et Musique": "https://www.bide-et-musique.com/wp-content/uploads/2021/05/logo-bm-2021.png",
    "Chansons Oubliées Où Presque": "https://www.radio.net/images/broadcasts/4b/6b/14164/1/c300.png",
    "Chante France-80s": "https://chantefrance80s.ice.infomaniak.ch/chantefrance80s-128.jpg",
    "Flash 80 Radio": "https://www.flash80.com/images/logo/2024/logo-flash80-2024.png",
    "Génération Dorothée": "https://generationdoree.fr/wp-content/uploads/2020/06/logo-generation-doree-2020.png",
    "Générikds": "https://www.radioking.com/api/v2/radio/play/logo/1b8d4f5f-9e5f-4f3d-8e5f-1b8d4f5f9e5f/300/300",
    "Made In 80": "https://i.ibb.co/4pD4X0x/madein80.png",
    "Mega Hits": "https://megahits.sapo.pt/wp-content/uploads/2020/06/logo-megahits.png",
    "Nostalgie-Les 80 Plus Grand Tubes": "https://cdn.nrjaudio.fm/radio/200/nostalgie-1.png",
    "Nostalgie-Les Tubes 80 N1": "https://cdn.nrjaudio.fm/radio/200/nostalgie-1.png",
    "Radio Comercial": "https://radiocomercial.pt/wp-content/uploads/2020/06/cropped-rc-favicon-192x192.png",
    "Radio Gérard": "https://radiosurle.net:8765/radiogerard/cover.jpg",
    "RFM": "https://cdn.radiofrance.fr/s3/cruiser-production/2018/11/2b8e8d0e-0f9f-11e9-8c7d-42010aee0001/300x300_rfm_2018.jpg",
    "RFM Portugal": "https://images.rfm.pt/logo-rfm-1200x1200.png",
    "Rádio São Miguel": "https://www.radiosaomiguel.pt/images/logo-radiosaomiguel.png",
    "RTL": "https://www.rtl.fr/favicon-192x192.png",
    "Superloustic": "https://i.ibb.co/4pD4X0x/superloustic.png",
    "Supernana": "https://i.ibb.co/4pD4X0x/supernana.png",
    "Top 80 Radio": "https://i.ibb.co/4pD4X0x/top80radio.png"
}


def load_history_cache() -> dict:
    """Charge le cache de l'historique depuis le fichier"""
    try:
        if os.path.exists(HISTORY_CACHE_FILE):
            with open(HISTORY_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_history_cache(cache: dict):
    """Sauvegarde le cache de l'historique dans le fichier"""
    try:
        with open(HISTORY_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def add_to_history_cache(station_name: str, artist: str, title: str, cover_url: str = ""):
    """Ajoute une chanson à l'historique en cache"""
    cache = load_history_cache()
    
    if station_name not in cache:
        cache[station_name] = []
    
    # Vérifier si la chanson n'est pas déjà dans les 5 dernières
    recent_songs = cache[station_name][:5]
    for song in recent_songs:
        if song.get('artist') == artist and song.get('title') == title:
            return  # Déjà dans l'historique récent
    
    # Ajouter au début de l'historique
    new_song = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'artist': artist,
        'title': title,
        'cover_url': cover_url
    }
    
    cache[station_name].insert(0, new_song)
    
    # Limiter l'historique à 50 chansons par radio
    if len(cache[station_name]) > 50:
        cache[station_name] = cache[station_name][:50]
    
    save_history_cache(cache)

def get_cached_history(station_name: str, count: int = 10) -> list:
    """Récupère l'historique depuis le cache"""
    cache = load_history_cache()
    if station_name in cache:
        return cache[station_name][:count]
    return []

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
    host: str = ""  # Ajout du champ pour l'animateur


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
            timeout=3,
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
        return RadioMetadata(station=station_name, title=title, artist=artist, cover_url=cover_url, host="")
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
                r = session.get(url, timeout=(2, 3), headers=headers)
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
                    return RadioMetadata(station=station_name, title=title, artist=artist, cover_url="", host="")

            # 7.html (Shoutcast-like) : often "<body>Artist - Title,StreamName</body>"
            if url.endswith("/7.html") and isinstance(r.text, str):
                raw = r.text
                raw = raw.replace("\r", " ").replace("\n", " ")
                raw = raw.split("<body>")[-1].split("</body>")[0]
                raw = raw.split(",")[0]
                parsed = _parse_icecast_title(raw)
                if parsed:
                    title, artist = parsed
                    return RadioMetadata(station=station_name, title=title, artist=artist, cover_url="", host="")

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
                r = session.get(url, timeout=(2, 3), headers=headers, stream=True)
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
                        return RadioMetadata(station=station_name, title=title, artist=artist, cover_url=cover_url, host="")
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
            return RadioMetadata(station=station_name, title=title, artist=artist, cover_url=cover_url, host="")

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
        self.cache_timeout_s = 5

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
                            cover_url=self._get_album_cover(metadata['artist'], metadata['song']),
                            host=""  # Pas d'animateur pour les chansons
                        )
                    elif metadata.get('host'):
                        return RadioMetadata(
                            station=station_name,
                            title=metadata.get('show', 'En direct'),
                            artist=metadata['host'],
                            host=metadata['host'],  # Ajout du nom de l'animateur
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
            response = self.session.get(url, timeout=3)
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    return data['results'][0].get('artworkUrl100', '').replace('100x100', '600x600')
        except Exception:
            pass
        return ""

    def _get_bide_musique_metadata(self, station_name: str) -> Optional[RadioMetadata]:
        """Extrait les métadonnées depuis le site de Bide Et Musique"""
        if not BeautifulSoup:
            return None
            
        try:
            url = "https://www.bide-et-musique.com/player2/radio-info.php"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': 'https://www.bide-et-musique.com/player2/bideplayertest.html'
            }
            
            response = self.session.get(url, headers=headers, timeout=10, verify=False)
            response.raise_for_status()
            
            # Parser le HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extraire le titre de la chanson
            title_element = soup.find('p', class_='titre-song')
            title = ""
            if title_element:
                title_link = title_element.find('a')
                if title_link:
                    title = _normalize_text(title_link.get_text(strip=True))
            
            # Extraire l'artiste
            artist_element = soup.find('p', class_='titre-song2')
            artist = ""
            if artist_element:
                artist_link = artist_element.find('a')
                if artist_link:
                    artist = _normalize_text(artist_link.get_text(strip=True))
            
            # Extraire l'émission/programme (utilisé comme animateur)
            program_element = soup.find('td', id='requete')
            program = ""
            if program_element:
                program_link = program_element.find('a')
                if program_link:
                    program = _normalize_text(program_link.get_text(strip=True))
            
            # Extraire la pochette
            pochette_element = soup.find('td', id='pochette')
            cover_url = ""
            if pochette_element:
                img_element = pochette_element.find('img')
                if img_element:
                    pochette_src = img_element.get('src', '')
                    if pochette_src:
                        # Convertir l'URL relative en URL absolue
                        if pochette_src.startswith('/'):
                            cover_url = f"https://www.bide-et-musique.com{pochette_src}"
                        else:
                            cover_url = pochette_src
            
            # Si on a un titre et un artiste, retourner les métadonnées
            if title and artist:
                return RadioMetadata(
                    station=station_name,
                    title=title,
                    artist=artist,
                    cover_url=cover_url,
                    host=program  # Le programme est utilisé comme animateur
                )
            
        except Exception as e:
            print(f"Erreur extraction Bide Et Musique: {e}")
            
        return None

    def _get_rtl_api_metadata(self, station_name: str) -> Optional[RadioMetadata]:
        """Extrait les métadonnées depuis l'API RTL"""
        try:
            url = "https://www.rtl.fr/ws/live/live"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
                'Connection': 'keep-alive',
                'Referer': 'https://www.rtl.fr/'
            }
            
            response = self.session.get(url, headers=headers, timeout=10, verify=False)
            response.raise_for_status()
            
            # Parser le JSON
            data = response.json()
            
            # Extraire les métadonnées
            title = data.get('title', '')
            hosts = data.get('hosts', '')
            cover_url = data.get('cover', '')
            
            # Si on a un titre et un animateur, retourner les métadonnées
            if title and hosts:
                return RadioMetadata(
                    station=station_name,
                    title=title,
                    artist=hosts,  # L'animateur est traité comme artiste
                    cover_url=cover_url,
                    host=hosts
                )
            
        except Exception as e:
            print(f"Erreur extraction RTL API: {e}")
            
        return None

    def _get_chantefrance_metadata(self, station_name: str) -> Optional[RadioMetadata]:
        """Extrait les métadonnées depuis l'API Chante France"""
        try:
            # Déterminer le bon radioStreamId selon la radio
            if "80" in station_name.lower():
                # Chante France 80s
                radio_stream_id = "3120757949245428885"
            else:
                # Chante France standard
                radio_stream_id = "3120757949245428885"  # Même ID pour l'instant
            
            # URL de l'API pour les métadonnées en direct
            current_timestamp = int(time.time() * 1000)
            api_url = f"https://www.chantefrance.com/api/TitleDiffusions?size=1&radioStreamId={radio_stream_id}&date={current_timestamp}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
                'Referer': 'https://www.chantefrance.com/'
            }
            
            response = self.session.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parser le JSON
            data = response.json()
            
            if data and len(data) > 0:
                track = data[0].get('title', {})
                title = track.get('title', '').strip()
                artist = track.get('artist', '').strip()
                cover_url = track.get('coverUrl', '')
                
                if title and artist:
                    print(f"🎵 Chante France API: {artist} - {title}")
                    return RadioMetadata(
                        station=station_name,
                        title=title,
                        artist=artist,
                        cover_url=cover_url,
                        host=""
                    )
            
        except Exception as e:
            print(f"Erreur extraction Chante France: {e}")
            
        return None

    def _get_rfm_metadata(self, station_name: str) -> Optional[RadioMetadata]:
        """Extrait les métadonnées depuis l'API Triton Digital de RFM"""
        try:
            # API Triton Digital pour RFM
            timestamp = int(time.time() * 1000)
            api_url = f"https://np.tritondigital.com/public/nowplaying?mountName=RFMAAC&numberToFetch=1&eventType=track&request.preventCache={timestamp}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/xml, text/xml, */*',
                'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
                'Referer': 'https://www.rfm.fr/'
            }
            
            response = self.session.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parser le XML
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            # Extraire les métadonnées depuis le XML
            nowplaying_info = root.find('.//nowplaying-info[@type="track"]')
            if nowplaying_info is not None:
                artist_element = nowplaying_info.find('.//property[@name="track_artist_name"]')
                title_element = nowplaying_info.find('.//property[@name="cue_title"]')
                
                if artist_element is not None and title_element is not None:
                    artist = artist_element.text.strip() if artist_element.text else ""
                    title = title_element.text.strip() if title_element.text else ""
                    
                    if title and artist:
                        print(f"🎵 RFM API: {artist} - {title}")
                        return RadioMetadata(
                            station=station_name,
                            title=title,
                            artist=artist,
                            cover_url="",  # RFM ne fournit pas de cover dans cette API
                            host=""
                        )
            
        except Exception as e:
            print(f"Erreur extraction RFM API: {e}")
            
        return None

    def _get_rfm_portugal_music_metadata(self, station_name: str) -> Optional[RadioMetadata]:
        """Extrait les métadonnées depuis l'API RFM Portugal OnAir"""
        try:
            # API RFM Portugal pour les chansons
            api_url = "https://configsa01.blob.core.windows.net/rfm/rfmOnAir.xml"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/xml, text/xml, */*',
                'Referer': 'https://rfm.pt/'
            }
            
            response = self.session.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parser le XML (encodage utf-16)
            import xml.etree.ElementTree as ET
            content = response.content.decode('utf-16')
            root = ET.fromstring(content)
            
            # Extraire les métadonnées de la chanson
            song_element = root.find('.//song')
            if song_element is not None:
                name_element = song_element.find('.//name')
                artist_element = song_element.find('.//artist')
                cover_element = song_element.find('.//capa')
                
                if name_element is not None and artist_element is not None:
                    title = name_element.text.strip() if name_element.text else ""
                    artist = artist_element.text.strip() if artist_element.text else ""
                    cover_url = cover_element.text.strip() if cover_element is not None and cover_element.text else ""
                    
                    if title and artist:
                        print(f"🎵 RFM Portugal: {artist} - {title}")
                        return RadioMetadata(
                            station=station_name,
                            title=title,
                            artist=artist,
                            cover_url=cover_url,
                            host=""
                        )
            
        except Exception as e:
            print(f"Erreur extraction RFM Portugal Music API: {e}")
            
        return None

    def _get_rfm_portugal_host_metadata(self, station_name: str) -> Optional[RadioMetadata]:
        """Extrait les informations des animateurs depuis l'API RFM Portugal"""
        try:
            # API RFM Portugal pour les animateurs
            api_url = "https://rfm.pt/ajax/emissao/locutor_player.aspx"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'pt-PT,pt;q=0.9,en;q=0.8',
                'Referer': 'https://rfm.pt/',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            response = self.session.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parser le JSON
            data = response.json()
            
            # Extraire les informations de l'animateur
            locutors = data.get('locutor', [])
            if locutors:
                locutor = locutors[0]  # Prendre le premier animateur
                
                program_name = locutor.get('locutorName', 'En direct')
                schedule = locutor.get('strHorario1', '')
                image_url = locutor.get('srcImg', '')
                
                # Utiliser le nom du programme comme "artiste" et "En direct" comme titre
                print(f"🎙️ RFM Portugal: {program_name} ({schedule})")
                
                return RadioMetadata(
                    station=station_name,
                    title="En direct",
                    artist=program_name,
                    cover_url=image_url,
                    host=program_name
                )
            
        except Exception as e:
            print(f"Erreur extraction RFM Portugal Host API: {e}")
            
        return None

    def _get_rfm_portugal_metadata(self, station_name: str) -> Optional[RadioMetadata]:
        """Extrait les métadonnées depuis les APIs RFM Portugal (musique + animateurs)"""
        try:
            # 1. Essayer d'abord l'API des chansons
            music_metadata = self._get_rfm_portugal_music_metadata(station_name)
            if music_metadata:
                return music_metadata
            
            # 2. Si pas de musique, essayer l'API des animateurs
            host_metadata = self._get_rfm_portugal_host_metadata(station_name)
            if host_metadata:
                return host_metadata
            
            # 3. Fallback si aucune API ne fonctionne
            return RadioMetadata(
                station=station_name,
                title="En direct",
                artist=station_name,
                cover_url="",
                host=""
            )
            
        except Exception as e:
            print(f"Erreur extraction RFM Portugal: {e}")
            return None

    def _get_icy_metadata(self, url: str, station_name: str) -> RadioMetadata:
        try:
            headers = {
                "Icy-MetaData": "1",
                "Accept": "*/*",
            }

            # Gérer spécifiquement les flux StreamTheWorld (comme Mega Hits)
            if "streamtheworld.com" in url:
                headers.update({
                    "User-Agent": "AppleCoreMedia/1.0.0.22F76 (iPhone; U; CPU OS 18_5 like Mac OS X; fr_fr)",
                    "X-Playback-Session-Id": "2129DA7C-E1B9-43E0-8B20-0C733A266859",
                    "icy-metadata": "1",
                    "Accept": "*/*",
                    "Accept-Language": "fr-FR,fr;q=0.9",
                    "Accept-Encoding": "identity",
                    "Connection": "keep-alive"
                })
            elif "ice.infomaniak.ch" in (url or ""):
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
                metadata_found = False
                
                # Augmenter le nombre de tentatives pour les flux StreamTheWorld
                max_attempts = 12 if "streamtheworld.com" in url else 6
                
                for attempt in range(max_attempts):
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
                        metadata_found = True
                        break
                
                # Si aucune métadonnée n'est trouvée pour Mega Hits, utiliser un message plus informatif
                if not metadata_found and "streamtheworld.com" in url:
                    title = "Écoutez Mega Hits"
                    artist = "La meilleure musique des années 80, 90 et actuelles"

            r.close()
            
            # Appliquer le logo par défaut si aucune pochette n'est trouvée
            if not cover_url and station_name in RADIO_LOGOS:
                cover_url = RADIO_LOGOS[station_name]
            
            return RadioMetadata(station=station_name, title=title or "En direct", artist=artist or station_name, cover_url=cover_url, host="")
        except Exception:
            return RadioMetadata(station=station_name, title="En direct", artist=station_name, cover_url="", host="")

    def _get_radioking_metadata(self, station_name: str, url: str) -> Optional[RadioMetadata]:
        """Récupérer les métadonnées pour les radios RadioKing"""
        try:
            if "generikids" in station_name.lower():
                print(" Générikds: Test API RadioKing")
                api_url = "https://api.radioking.io/widget/radio/generikids/track/current"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json",
                    "Referer": "https://www.radioking.com/"
                }
                
                # Ajouter un petit délai pour laisser le temps à l'API de répondre
                time.sleep(0.5)
                
                response = self.session.get(api_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data and 'title' in data and 'artist' in data:
                        title = data['title'].strip()
                        artist = data['artist'].strip()
                        cover_url = data.get('cover', '')
                        
                        if title and artist:
                            print(f" RadioKing API: {artist} - {title}")
                            return RadioMetadata(
                                station=station_name,
                                title=title,
                                artist=artist,
                                cover_url=cover_url,
                                host=""
                            )
                
                # Fallback sur ICY direct
                print(" Fallback sur ICY direct")
                return self._get_icy_metadata(url, station_name)
                
        except Exception as e:
            print(f" Erreur RadioKing: {e}")
            return None

    def get_chantefrance_history(self, station_name: str, count: int = 10) -> list:
        """Récupère l'historique des musiques passées pour Chante France"""
        try:
            api_url = f"https://www.chantefrance.com/api/TitleDiffusions?size={count}&radioStreamId=3120757949245428885&date={int(time.time() * 1000)}"
            
            response = self.session.get(api_url, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            history = []
            if data:
                for item in data:
                    track = item['title']
                    artist = track.get('artist', '').title()
                    title = track.get('title', '').title()
                    cover_url = track.get('coverUrl', '')
                    timestamp = item.get('timestamp', '')
                    
                    if artist and title:
                        # Nettoyage des noms d'artistes et titres
                        artist = ' '.join(artist.split())
                        title = ' '.join(title.split())
                        
                        # Conversion du timestamp
                        if timestamp:
                            try:
                                dt = timestamp.replace('T', ' ').replace('Z', '')
                                history.append({
                                    'timestamp': dt,
                                    'artist': artist,
                                    'title': title,
                                    'cover_url': cover_url
                                })
                            except:
                                history.append({
                                    'timestamp': timestamp,
                                    'artist': artist,
                                    'title': title,
                                    'cover_url': cover_url
                                })
            
            return history
        except Exception as e:
            print(f"Erreur historique Chante France: {e}", file=sys.stderr)
            return []

    def get_nostalgie_history(self, station_name: str, radio_id: str, count: int = 10) -> list:
        """Récupère l'historique des musiques passées pour Nostalgie"""
        try:
            headers = {
                "Accept": "application/json",
                "Accept-Language": "fr-FR,fr;q=0.9",
                "User-Agent": "NostalgieApp/9490 CFNetwork/3826.500.131 Darwin/24.5.0",
                "X-Device-Category": "mobile",
                "X-App-Id": "fr_nosta_ios",
            }
            
            response = self.session.get(
                f"https://players.nrjaudio.fm/wr_api3/v1/webradios/{radio_id}/tracklist",
                params={"timeshift_slot": 1},
                timeout=6,
                headers=headers,
            )
            
            if response.status_code != 200:
                return []
                
            data = response.json()
            if not isinstance(data, dict):
                return []
                
            data2 = data.get("data")
            if not isinstance(data2, dict):
                return []
                
            tracks = data2.get("tracks", [])
            if not isinstance(tracks, list):
                return []
            
            history = []
            for track in tracks[:count]:
                if isinstance(track, dict):
                    title = _normalize_text(str(track.get("title") or ""))
                    artist = _normalize_text(str(track.get("artist") or ""))
                    cover_url = _normalize_text(str(track.get("artwork_image") or ""))
                    
                    if title and artist:
                        history.append({
                            'timestamp': '',  # Nostalgie ne fournit pas de timestamp
                            'artist': artist,
                            'title': title,
                            'cover_url': cover_url
                        })
            
            return history
        except Exception as e:
            print(f"Erreur historique Nostalgie: {e}", file=sys.stderr)
            return []

    def get_history(self, station_name: str, url: str, count: int = 10) -> list:
        """Récupère l'historique des musiques passées selon la radio"""
        station_lower = station_name.lower()
        
        # D'abord essayer les API officielles
        # Chante France
        if "chantefrance" in station_lower or "chante france" in station_lower:
            return self.get_chantefrance_history(station_name, count)
        
        # Nostalgie
        elif "nostalgie" in station_lower:
            mapping = {
                "Nostalgie-Les 80 Plus Grand Tubes": "1640",
                "Nostalgie-Les Tubes 80 N1": "1283",
            }
            radio_id = mapping.get(station_name)
            if radio_id:
                return self.get_nostalgie_history(station_name, radio_id, count)
        
        # Pour toutes les autres radios, utiliser le cache local
        return get_cached_history(station_name, count)

    def get_metadata_with_history(self, station_name: str, url: str) -> RadioMetadata:
        """Récupère les métadonnées et ajoute automatiquement à l'historique"""
        metadata = self.get_metadata(station_name, url)
        
        # Ajouter à l'historique si c'est une musique (pas "En direct")
        if metadata and metadata.title and metadata.title.lower() != "en direct":
            add_to_history_cache(station_name, metadata.artist, metadata.title, metadata.cover_url)
        
        return metadata

    def monitor_radio(self, station_name: str, url: str, interval: int = 30):
        """Surveille une radio en continu et met à jour l'historique"""
        global stop_monitoring
        
        print(f"🎵 Monitoring de {station_name} (Intervalle: {interval}s)")
        print("Appuyez sur Ctrl+C pour mettre en pause/reprendre")
        print("=" * 60)
        
        last_song = None
        
        while not stop_monitoring:
            try:
                metadata = self.get_metadata_with_history(station_name, url)
                
                current_song = f"{metadata.artist} - {metadata.title}"
                
                # Afficher seulement si la chanson a changé
                if current_song != last_song:
                    timestamp = time.strftime('%H:%M:%S')
                    print(f"[{timestamp}] 🎶 {metadata.artist} - {metadata.title}")
                    
                    if metadata.cover_url:
                        print(f"           📱 {metadata.cover_url}")
                    
                    last_song = current_song
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print(f"\n⏸️  Mise en pause - Appuyez sur Entrée pour reprendre, Ctrl+C pour arrêter")
                
                # Attendre que l'utilisateur décide
                while not stop_monitoring:
                    try:
                        # Attendre une seconde à la fois pour vérifier stop_monitoring
                        time.sleep(1)
                    except KeyboardInterrupt:
                        print("\n🛑 Arrêt du monitoring")
                        stop_monitoring = True
                        break
                
                if not stop_monitoring:
                    print("▶️  Reprise du monitoring...")
                    continue
                    
            except Exception as e:
                print(f"❌ Erreur: {e}")
                time.sleep(interval)
        
        print("✅ Monitoring terminé")

    def monitor_multiple_radios(self, stations: list, interval: int = 30):
        """Surveille plusieurs radios en continu"""
        global stop_monitoring
        
        print(f"🎵 Monitoring de {len(stations)} radios (Intervalle: {interval}s)")
        print("Appuyez sur Ctrl+C pour mettre en pause/reprendre")
        print("=" * 60)
        
        last_songs = {station: None for station, _ in stations}
        
        while not stop_monitoring:
            try:
                for station_name, url in stations:
                    try:
                        metadata = self.get_metadata_with_history(station_name, url)
                        current_song = f"{metadata.artist} - {metadata.title}"
                        
                        # Afficher seulement si la chanson a changé
                        if current_song != last_songs[station_name]:
                            timestamp = time.strftime('%H:%M:%S')
                            print(f"[{timestamp}] {station_name}: 🎶 {metadata.artist} - {metadata.title}")
                            last_songs[station_name] = current_song
                            
                    except Exception as e:
                        print(f"[{time.strftime('%H:%M:%S')}] ❌ {station_name}: Erreur {e}")
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print(f"\n⏸️  Mise en pause - Appuyez sur Entrée pour reprendre, Ctrl+C pour arrêter")
                
                # Attendre que l'utilisateur décide
                while not stop_monitoring:
                    try:
                        time.sleep(1)
                    except KeyboardInterrupt:
                        print("\n🛑 Arrêt du monitoring")
                        stop_monitoring = True
                        break
                
                if not stop_monitoring:
                    print("▶️  Reprise du monitoring...")
                    continue
        
        print("✅ Monitoring terminé")

    def get_metadata(self, station_name: str, url: str) -> RadioMetadata:
        cache_key = f"{station_name}:{url}"
        now = time.time()
        hit = self.cache.get(cache_key)
        if hit and now - hit[1] < self.cache_timeout_s:
            return hit[0]

        md: Optional[RadioMetadata] = None

        # Spécial: Bide Et Musique - essayer d'abord le parsing web
        if "bide" in station_name.lower():
            md = self._get_bide_musique_metadata(station_name)
            if md:
                self.cache[cache_key] = (md, now)
                return md

        # Spécial: Chante France 80 - essayer d'abord l'API
        if "chantefrance" in station_name.lower() or "chante france" in station_name.lower():
            md = self._get_chantefrance_metadata(station_name)
            if md:
                self.cache[cache_key] = (md, now)
                return md

        # Spécial: RFM Portugal - essayer d'abord les APIs portugaises
        if "rfm" in station_name.lower() and "portugal" in station_name.lower():
            md = self._get_rfm_portugal_metadata(station_name)
            if md:
                self.cache[cache_key] = (md, now)
                return md
            
            # Sinon, essayer avec le flux ICY standard
            md = self._get_icy_metadata(url, station_name)
            self.cache[cache_key] = (md, now)
            return md

        # Spécial: RTL - essayer d'abord l'API
        if "rtl" in station_name.lower():
            md = self._get_rtl_api_metadata(station_name)
            if md:
                self.cache[cache_key] = (md, now)
                return md
            
            # Sinon, essayer avec le flux ICY standard
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

        # Spécial: RadioKing - essayer de récupérer le vrai flux et les métadonnées
        if "radioking.com" in url:
            md = self._get_radioking_metadata(station_name, url)
            if md:
                self.cache[cache_key] = (md, now)
                return md

        md = self._get_icy_metadata(url, station_name)
        
        # Pour les chansons, essayer de trouver une pochette d'album si pas déjà fait
        if md.title and md.artist and md.title.lower() != "en direct":
            # Si pas de pochette ou si c'est juste le logo par défaut
            if not md.cover_url or md.cover_url == RADIO_LOGOS.get(station_name, ""):
                album_cover = self._get_album_cover(md.artist, md.title)
                if album_cover:
                    md = RadioMetadata(
                        station=md.station,
                        title=md.title,
                        artist=md.artist,
                        cover_url=album_cover
                    )
        
        # Pour toutes les radios, s'assurer qu'on a au moins le logo par défaut
        if not md.cover_url and station_name in RADIO_LOGOS:
            md = RadioMetadata(
                station=md.station,
                title=md.title,
                artist=md.artist,
                cover_url=RADIO_LOGOS[station_name]
            )
        
        self.cache[cache_key] = (md, now)
        return md


def _cli_monitor_once(station_name: str, url: str, interval: int = 30) -> int:
    """Lance le monitoring d'une seule radio"""
    try:
        fetcher = RadioFetcher()
        fetcher.monitor_radio(station_name, url, interval)
        return 0
    except Exception as e:
        print(f"Erreur: {e}", file=sys.stderr)
        return 1

def _cli_monitor_all(interval: int = 30) -> int:
    """Lance le monitoring de toutes les radios"""
    try:
        fetcher = RadioFetcher()
        fetcher.monitor_multiple_radios(RADIOS, interval)
        return 0
    except Exception as e:
        print(f"Erreur: {e}", file=sys.stderr)
        return 1

def _signal_handler(signum, frame):
    """Gestionnaire de signal pour arrêt propre"""
    global stop_monitoring
    stop_monitoring = True
    print("\n🛑 Signal d'arrêt reçu, arrêt en cours...")


def _cli_history_once(station_name: str, url: str, count: int = 10) -> int:
    try:
        fetcher = RadioFetcher()
        history = fetcher.get_history(station_name, url, count)
        
        if history:
            print(f"Historique des {len(history)} dernières musiques sur {station_name}:")
            print("=" * 60)
            for i, track in enumerate(history, 1):
                print(f"{i:2d}. {track['artist']} - {track['title']}")
                if track['timestamp']:
                    print(f"    Heure: {track['timestamp']}")
                if track['cover_url']:
                    print(f"    Pochette: {track['cover_url']}")
                print()
        else:
            # Vérifier si c'est une radio connue mais sans historique
            station_lower = station_name.lower()
            if any(keyword in station_lower for keyword in ["rtl", "bide", "100%", "mega", "flash", "superloustic", "radio gérard", "supernana", "génération", "made in", "top 80", "générikds", "chansons oubliées"]):
                print(f"L'historique n'est pas encore disponible pour {station_name}")
                print("Fonctionnalité actuellement disponible pour:")
                print("  ✅ Chante France")
                print("  ✅ Nostalgie (Les 80 Plus Grand Tubes, Les Tubes 80 N1)")
                print("\nLes autres radios seront ajoutées progressivement...")
            else:
                print(f"Aucun historique disponible pour {station_name}")
                print("Essayez avec --list pour voir les radios supportées")
        
        return 0
    except Exception as e:
        print(f"Erreur: {e}", file=sys.stderr)
        return 1


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
    # Configurer le gestionnaire de signal
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
    
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--list-all", action="store_true")
    parser.add_argument("--run-all", action="store_true")
    parser.add_argument("--history", action="store_true", help="Affiche l'historique des musiques passées")
    parser.add_argument("--monitor", action="store_true", help="Surveille une radio en continu")
    parser.add_argument("--monitor-all", action="store_true", help="Surveille toutes les radios en continu")
    parser.add_argument("--count", type=int, default=10, help="Nombre de musiques à afficher dans l'historique (défaut: 10)")
    parser.add_argument("--interval", type=int, default=30, help="Intervalle de monitoring en secondes (défaut: 30)")
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

    if args.monitor_all:
        return _cli_monitor_all(args.interval)

    if args.monitor:
        if not args.station or not args.url:
            sys.stderr.write("Missing --station or --url for --monitor\n")
            return 2
        return _cli_monitor_once(args.station, args.url, args.interval)

    if args.history:
        if not args.station or not args.url:
            sys.stderr.write("Missing --station or --url for --history\n")
            return 2
        return _cli_history_once(args.station, args.url, args.count)

    if args.json:
        if not args.station or not args.url:
            sys.stderr.write("Missing --station or --url\n")
            return 2
        return _cli_json_once(args.station, args.url)

    sys.stderr.write("Usage:\n")
    sys.stderr.write("  --json --station <name> --url <stream_url>\n")
    sys.stderr.write("  --history --station <name> --url <stream_url> [--count N]\n")
    sys.stderr.write("  --monitor --station <name> --url <stream_url> [--interval N]\n")
    sys.stderr.write("  --monitor-all [--interval N]\n")
    sys.stderr.write("  --list | --list-all | --run-all\n")
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(_entrypoint())
    except SystemExit as e:
        sys.exit(e.code)
