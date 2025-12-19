import argparse
import contextlib
import io
import html
import json
import os
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


_STREAMRADIO_SERVER_ID: Optional[str] = None
_STREAMRADIO_SERVER_ID_TS: float = 0.0


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
    s = html.unescape(value).strip()
    if not s:
        return ""
    s = re.sub(r"\s+", " ", s).strip()
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
    source: str = ""


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
                if cover_id:
                    cover_id = "".join(cover_id.split())
                    cover = f"https://www.centpourcent.com/ws/cover/{quote(cover_id, safe='/')}"
            if title and artist:
                return title, artist, cover

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
    
    # Handle XML wrapped in StreamTitle
    if s.startswith("'") and s.endswith("'"):
        s = s.strip("'")
    
    # Look for XML content in the text
    if "<?xml" in s:
        start = s.find("<?xml")
    elif "<RadioInfo" in s:
        start = s.find("<RadioInfo")
    else:
        return None
    
    if start > 0:
        s = s[start:]
    
    try:
        root = ET.fromstring(s)
    except Exception as e:
        return None

    artist_el = root.find(".//DB_DALET_ARTIST_NAME")
    title_el = root.find(".//DB_DALET_TITLE_NAME")
    img_el = root.find(".//DB_ALBUM_IMAGE")

    artist = _normalize_text(artist_el.text) if (artist_el is not None and artist_el.text) else ""
    title = _normalize_text(title_el.text) if (title_el is not None and title_el.text) else ""

    cover_url = ""
    if img_el is not None and img_el.text:
        img = _normalize_text(img_el.text)
        if img:
            cover_url = f"https://static.radiocomercial.pt/imagens/reprodutor/{img}"

    if not artist or not title:
        return None
    return title, artist, cover_url


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
                parsed2 = _parse_icecast_title(str(title_field))
                if parsed2:
                    title2, artist2 = parsed2
                    return RadioMetadata(station=station_name, title=title2, artist=artist2, cover_url="")

            if url.endswith("/7.html") and isinstance(r.text, str):
                raw = r.text
                raw = raw.replace("\r", " ").replace("\n", " ")
                raw = raw.split("<body>")[-1].split("</body>")[0]
                raw = raw.split(",")[0]
                parsed2 = _parse_icecast_title(raw)
                if parsed2:
                    title2, artist2 = parsed2
                    return RadioMetadata(station=station_name, title=title2, artist=artist2, cover_url="")

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


def _fetch_bideetmusique_programme_page(session: requests.Session, station_name: str) -> Optional[RadioMetadata]:
    try:
        url = "http://www.bide-et-musique.com/programme-webradio.html"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Connection": "close",
        }
        r = session.get(url, timeout=(3, 6), headers=headers)
        if r.status_code != 200:
            return None
        html = r.text or ""
        if not html:
            return None

        m = re.search(r"En\s*ce\s*moment\s*vous\s*(?:écoutez|ecoutez)\s*: ?", html, flags=re.IGNORECASE)
        if not m:
            return None
        tail = html[m.end() :]

        links = re.findall(r"<a\s+[^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>", tail, flags=re.IGNORECASE | re.DOTALL)
        if not links:
            return None

        song_txt = ""
        artist_txt = ""
        for href, inner in links:
            href2 = _normalize_text(href)
            txt = _normalize_text(re.sub(r"<[^>]+>", "", inner))
            if not txt:
                continue
            if not song_txt and re.search(r"/song/\d+\.html", href2, flags=re.IGNORECASE):
                song_txt = txt
                continue
            if song_txt and not artist_txt and re.search(r"/artist/\d+\.html", href2, flags=re.IGNORECASE):
                artist_txt = txt
                break

        title = song_txt
        artist = artist_txt

        if not title or not artist:
            return None
        return RadioMetadata(station=station_name, title=title, artist=artist, cover_url="")
    except Exception:
        return None


def _resolve_streamtheworld_redirect(session: requests.Session, url: str) -> str:
    try:
        if not isinstance(url, str) or not url:
            return url
        if "playerservices.streamtheworld.com" not in url:
            return url

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "*/*",
            "Connection": "close",
        }
        r = session.get(url, timeout=(3, 6), headers=headers, allow_redirects=False)
        try:
            if r.status_code in (301, 302, 303, 307, 308):
                loc = str(r.headers.get("location") or "").strip()
                if loc:
                    return loc
            return url
        finally:
            try:
                r.close()
            except Exception:
                pass
    except Exception:
        return url


def _get_icy_metadata_with_max_blocks(session: requests.Session, url: str, station_name: str, max_blocks: int) -> RadioMetadata:
    try:
        headers = {
            "Icy-MetaData": "1",
            "Accept": "*/*",
        }

        if "ice.infomaniak.ch" in (url or ""):
            headers.update({
                "User-Agent": "AIM",
                "Referer": "apli",
                "Accept-Encoding": "identity",
                "Accept-Language": "fr-FR,fr;q=0.9",
                "Connection": "keep-alive",
                "icy-metadata": "1",
            })
        elif "streamradio.fr" in (url or ""):
            headers.update({
                "User-Agent": "AppleCoreMedia/1.0.0.22F76 (iPhone; U; CPU OS 18_5 like Mac OS X; fr_fr)",
                "Accept-Language": "fr-FR,fr;q=0.9",
                "Accept-Encoding": "identity",
                "Connection": "keep-alive",
                "icy-metadata": "1",
            })
        else:
            headers.update({
                "User-Agent": "VLC/3.0.18",
                "Connection": "close",
            })

        r = session.get(url, stream=True, timeout=8, headers=headers)
        title = "En direct"
        artist = station_name
        cover_url = ""

        if "icy-metaint" in r.headers:
            meta_int = int(r.headers["icy-metaint"])
            for _ in range(max(1, int(max_blocks))):
                r.raw.read(meta_int)
                meta_len_b = r.raw.read(1)
                if not meta_len_b:
                    break
                meta_len = (meta_len_b[0] if isinstance(meta_len_b, (bytes, bytearray)) else ord(meta_len_b)) * 16
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


def _fetch_streamapps_manager_nowplaying(session: requests.Session, station_name: str, server: str, radio: str) -> Optional[RadioMetadata]:
    try:
        if not server or not radio:
            return None
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "fr-FR,fr;q=0.9",
            "Connection": "close",
        }
        r = session.get(
            "https://api.streamapps.fr/manager.php",
            params={"server": server, "radio": radio, "nowrap": "true"},
            timeout=0.5,
            headers=headers,
        )
        if r.status_code != 200:
            return None
        try:
            data = r.json()
        except Exception:
            return None
        if not isinstance(data, dict):
            return None
        md = data.get("metadata")
        if not isinstance(md, dict):
            return None
        title = _normalize_text(str(md.get("title") or ""))
        artist = _normalize_text(str(md.get("artist") or ""))
        cover_url = _normalize_text(str(md.get("cover") or ""))
        if not title or title.lower() == "en direct":
            return None
        if not artist:
            artist = station_name
        return RadioMetadata(station=station_name, title=title, artist=artist, cover_url=cover_url)
    except Exception:
        return None


def _fetch_rtl_metadata(session: requests.Session, station_name: str) -> Optional[RadioMetadata]:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "fr-FR,fr;q=0.9",
            "Connection": "close",
        }
        
        # Try RTL live API
        try:
            r = session.get("https://www.rtl.fr/ws/live/live", timeout=2, headers=headers)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict):
                    title = _normalize_text(str(data.get("title") or ""))
                    hosts = _normalize_text(str(data.get("hosts") or ""))
                    program_slug = _normalize_text(str(data.get("programSlug") or ""))
                    
                    if title and title.lower() != "en direct":
                        # Use hosts as artist if available, otherwise station name
                        artist = hosts if hosts else station_name
                        return RadioMetadata(station=station_name, title=title, artist=artist, cover_url="")
        except Exception:
            pass
                
    except Exception:
        pass
    
    return None


def _decode_id3_text(payload: bytes) -> str:
    if not payload:
        return ""
    enc = payload[0]
    data = payload[1:]
    try:
        if enc == 0:
            return _normalize_text(data.decode("latin-1", errors="ignore"))
        if enc == 1:
            return _normalize_text(data.decode("utf-16", errors="ignore"))
        if enc == 2:
            return _normalize_text(data.decode("utf-16-be", errors="ignore"))
        if enc == 3:
            return _normalize_text(data.decode("utf-8", errors="ignore"))
    except Exception:
        return ""
    return ""


def _synchsafe_to_int(b4: bytes) -> int:
    if not isinstance(b4, (bytes, bytearray)) or len(b4) != 4:
        return 0
    return ((b4[0] & 0x7F) << 21) | ((b4[1] & 0x7F) << 14) | ((b4[2] & 0x7F) << 7) | (b4[3] & 0x7F)


def _parse_id3_tags(buf: bytes) -> dict:
    out = {}
    if not isinstance(buf, (bytes, bytearray)) or len(buf) < 10:
        return out

    # ID3 tags in AAC/HLS segments are not always at offset 0.
    # Search a few occurrences to increase the chance of finding timed ID3 metadata.
    start = 0
    for _ in range(4):
        idx = buf.find(b"ID3", start)
        if idx < 0 or idx + 10 > len(buf):
            break
        b2 = buf[idx:]

        version_major = b2[3]
        if version_major not in (2, 3, 4):
            start = idx + 3
            continue

        size = _synchsafe_to_int(b2[6:10])
        if size <= 0:
            start = idx + 3
            continue

        end = min(len(b2), 10 + size)
        i = 10
        while i + 10 <= end:
            frame_id = b2[i : i + 4]
            if frame_id == b"\x00\x00\x00\x00":
                break

            if version_major == 2:
                # ID3v2.2 uses 3-char IDs (not handled here)
                break

            if version_major == 3:
                frame_size = int.from_bytes(b2[i + 4 : i + 8], "big", signed=False)
            else:
                frame_size = _synchsafe_to_int(b2[i + 4 : i + 8])

            if frame_size <= 0:
                break

            frame_start = i + 10
            frame_end = frame_start + frame_size
            if frame_end > end:
                break

            fid = frame_id.decode("ascii", errors="ignore")
            payload = b2[frame_start:frame_end]
            if fid in ("TIT2", "TPE1"):
                val = _decode_id3_text(payload)
                if val:
                    out[fid] = val

            i = frame_end

        # If we got at least one useful tag, stop early.
        if out.get("TIT2") or out.get("TPE1"):
            break

        start = idx + 3

    return out


def _parse_m3u8_first_url(text: str) -> Optional[str]:
    if not isinstance(text, str) or not text:
        return None
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("http://") or s.startswith("https://"):
            return s
    return None


def _parse_m3u8_last_segment_url(text: str) -> Optional[str]:
    if not isinstance(text, str) or not text:
        return None
    last = None
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("http://") or s.startswith("https://"):
            last = s
    return last


def _fetch_bauer_hls_id3_metadata(session: requests.Session, url: str, station_name: str) -> Optional[RadioMetadata]:
    try:
        if not isinstance(url, str) or ".m3u8" not in url:
            return None

        headers = {
            "Accept": "*/*",
            "Accept-Language": "fr-FR,fr;q=0.9",
            "User-Agent": "AppleCoreMedia/1.0.0.22F76 (iPhone; U; CPU OS 18_5 like Mac OS X; fr_fr)",
            "Accept-Encoding": "identity",
            "Connection": "close",
        }

        r1 = session.get(url, timeout=(3, 6), headers=headers)
        if r1.status_code != 200:
            return None
        text1 = r1.text or ""
        next_url = _parse_m3u8_first_url(text1)
        r1.close()

        playlist_url = next_url or url

        r2 = session.get(playlist_url, timeout=(3, 6), headers=headers)
        if r2.status_code != 200:
            return None
        text2 = r2.text or ""
        seg_url = _parse_m3u8_last_segment_url(text2)

        if seg_url and seg_url.endswith(".m3u8"):
            playlist_url2 = seg_url
            r2.close()
            r2 = session.get(playlist_url2, timeout=(3, 6), headers=headers)
            if r2.status_code != 200:
                return None
            text2 = r2.text or ""
            seg_url = _parse_m3u8_last_segment_url(text2)

        r2.close()

        if not seg_url:
            return None

        if "/ads/" in seg_url:
            last_non_ad = None
            for line in text2.splitlines():
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                if (s.startswith("http://") or s.startswith("https://")) and "/ads/" not in s:
                    last_non_ad = s
            if last_non_ad:
                seg_url = last_non_ad

        r3 = session.get(seg_url, timeout=(3, 10), headers=headers, stream=True)
        if r3.status_code != 200:
            r3.close()
            return None

        buf = b""
        try:
            for chunk in r3.iter_content(chunk_size=8192):
                if not chunk:
                    continue
                buf += chunk
                if len(buf) >= 512 * 1024:
                    break
        finally:
            r3.close()

        tags = _parse_id3_tags(buf)
        title = _normalize_text(str(tags.get("TIT2") or ""))
        artist = _normalize_text(str(tags.get("TPE1") or ""))

        if not title and not artist:
            return None
        if not artist:
            artist = station_name
        if not title:
            title = "En direct"

        return RadioMetadata(station=station_name, title=title, artist=artist, cover_url="")
    except Exception:
        return None


def _fetch_radiocomercial_nowplaying_xml(session: requests.Session, station_name: str) -> Optional[RadioMetadata]:
    try:
        url = "https://radiocomercial.pt/nowplaying.xml"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/xml,text/xml,*/*",
            "Accept-Language": "fr-FR,fr;q=0.9",
            "Connection": "close",
        }
        r = session.get(url, timeout=(3, 6), headers=headers)
        if r.status_code != 200:
            return None
        text = r.text or ""
        r.close()

        # Try song info first (when available)
        try:
            root = ET.fromstring(text[text.find("<RadioInfo") :] if "<RadioInfo" in text else text)
        except Exception:
            root = None

        if root is not None:
            title_el = root.find(".//DB_DALET_TITLE_NAME")
            artist_el = root.find(".//DB_DALET_ARTIST_NAME")
            img_el = root.find(".//DB_ALBUM_IMAGE")

            title = _normalize_text(title_el.text) if (title_el is not None and title_el.text) else ""
            artist = _normalize_text(artist_el.text) if (artist_el is not None and artist_el.text) else ""
            cover_url = ""
            if img_el is not None and img_el.text:
                img = _normalize_text(img_el.text)
                if img:
                    cover_url = f"https://static.radiocomercial.pt/imagens/reprodutor/{img}"

            if title and artist:
                return RadioMetadata(station=station_name, title=title, artist=artist, cover_url=cover_url)

            # Fallback: show/host metadata
            show_title_el = root.find(".//AnimadorInfo/TITLE")
            show_desc_el = root.find(".//AnimadorInfo/DESCRIPTION")
            show_name_el = root.find(".//AnimadorInfo/SHOW_NAME")
            show_hours_el = root.find(".//AnimadorInfo/SHOW_HOURS")

            show_title = _normalize_text(show_title_el.text) if (show_title_el is not None and show_title_el.text) else ""
            show_desc = _normalize_text(show_desc_el.text) if (show_desc_el is not None and show_desc_el.text) else ""
            show_name = _normalize_text(show_name_el.text) if (show_name_el is not None and show_name_el.text) else ""
            show_hours = _normalize_text(show_hours_el.text) if (show_hours_el is not None and show_hours_el.text) else ""

            title2 = show_name or show_title
            artist2 = show_desc
            if show_hours and title2:
                title2 = f"{title2} ({show_hours})"

            if title2:
                return RadioMetadata(station=station_name, title=title2, artist=artist2 or station_name, cover_url="")

        # As a last resort, try the existing parser (handles XML embedded in StreamTitle)
        parsed = _parse_radiocomercial_radioinfo_xml(text)
        if parsed:
            title, artist, cover_url = parsed
            if title and artist:
                return RadioMetadata(station=station_name, title=title, artist=artist, cover_url=cover_url)
        return None
    except Exception:
        return None


def _fetch_streamradio_nowplaying(session: requests.Session, station_name: str) -> Optional[RadioMetadata]:
    try:
        base = "https://manager7.streamradio.fr:1970"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "fr-FR,fr;q=0.9",
            "Connection": "close",
        }

        global _STREAMRADIO_SERVER_ID, _STREAMRADIO_SERVER_ID_TS
        now = time.time()
        if not _STREAMRADIO_SERVER_ID or (now - _STREAMRADIO_SERVER_ID_TS) > 300:
            try:
                r0 = session.get(f"{base}/api/startpage/", timeout=1.5, headers=headers)
                if r0.status_code == 200:
                    data0 = None
                    try:
                        data0 = r0.json()
                    except Exception:
                        data0 = None
                    if isinstance(data0, dict):
                        cur = data0.get("currentServer")
                        if isinstance(cur, dict) and cur.get("id") is not None:
                            _STREAMRADIO_SERVER_ID = str(cur.get("id"))
                            _STREAMRADIO_SERVER_ID_TS = now
            except Exception:
                pass

        server_id = _STREAMRADIO_SERVER_ID or "1970"

        params = {
            "server": server_id,
            "limit": "1",
            "format": "jsonp",
        }

        r = session.get(f"{base}/api/v2/history/", params=params, timeout=2, headers=headers)
        if r.status_code != 200:
            return None

        payload = _extract_jsonp_payload(r.text or "")
        if not payload:
            return None

        try:
            data = json.loads(payload)
        except Exception:
            return None

        if not isinstance(data, dict):
            return None
        results = data.get("results")
        if not isinstance(results, list) or not results:
            return None
        item = results[0]
        if not isinstance(item, dict):
            return None

        meta = _normalize_text(str(item.get("metadata") or ""))
        cover_url = _normalize_text(str(item.get("img_medium_url") or item.get("img_url") or ""))

        if not meta:
            return None

        artist = station_name
        title = meta
        if " - " in meta:
            a, t = meta.split(" - ", 1)
            artist = _normalize_text(a) or station_name
            title = _normalize_text(t)
        if not title:
            return None

        return RadioMetadata(station=station_name, title=title, artist=artist, cover_url=cover_url)
    except Exception:
        return None


def _fetch_bauermedia_radiocomercial_lastsongs_json(session: requests.Session, station_name: str) -> Optional[RadioMetadata]:
    try:
        url = "https://bauermedia.pt/static/radiocomercial/radiocomercial.json"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json,*/*",
            "Accept-Language": "fr-FR,fr;q=0.9",
            "Connection": "close",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
        params = {"_": str(int(time.time()))}
        r = session.get(url, params=params, timeout=(3, 6), headers=headers)
        if r.status_code != 200:
            return None
        try:
            data = r.json()
        finally:
            r.close()

        if not isinstance(data, dict):
            return None
        recs = data.get("now_playing_record")
        if not isinstance(recs, list) or not recs:
            return None

        def _rec_key(item: object) -> Tuple[str, str]:
            if not isinstance(item, dict):
                return ("", "")
            d = _normalize_text(str(item.get("date") or ""))
            t = _normalize_text(str(item.get("time_played") or ""))
            return (d, t)

        candidates = [x for x in recs if isinstance(x, dict)]
        if not candidates:
            return None

        candidates.sort(key=_rec_key, reverse=True)

        for rec in candidates:
            mcr = rec.get("mcr") if isinstance(rec.get("mcr"), dict) else {}
            zenon = rec.get("zenon") if isinstance(rec.get("zenon"), dict) else {}

            title = _normalize_text(str(mcr.get("song_name") or zenon.get("song_name") or ""))
            if not title:
                continue

            artist = _normalize_text(
                str((mcr.get("album") or {}).get("lead_artist", {}).get("name") if isinstance(mcr.get("album"), dict) else "")
            )
            if not artist:
                artist = _normalize_text(str(zenon.get("artist_name") or ""))

            cover_url = ""
            album = mcr.get("album") if isinstance(mcr.get("album"), dict) else None
            if album and album.get("image"):
                img = _normalize_text(str(album.get("image") or ""))
                if img:
                    img = "".join(img.split())
                    cover_url = f"https://static.radiocomercial.pt/imagens/reprodutor/{img}"

            if not artist:
                artist = station_name

            return RadioMetadata(station=station_name, title=title, artist=artist, cover_url=cover_url)

        return None
    except Exception:
        return None


def _load_mytuner_creds_from_file(path: str) -> dict:
    try:
        p = _normalize_text(path)
        if not p:
            return {}
        if not os.path.isfile(p):
            return {}
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {}
        out = {}
        for k in ("authorization", "time", "app_codename", "app", "radio_id", "origin", "referer"):
            if k in data:
                out[k] = _normalize_text(str(data.get(k) or ""))
        return out
    except Exception:
        return {}


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

    def _get_icy_metadata(self, url: str, station_name: str) -> RadioMetadata:
        return _get_icy_metadata_with_max_blocks(self.session, url, station_name, max_blocks=6)

    def get_metadata(self, station_name: str, url: str) -> RadioMetadata:
        cache_key = f"{station_name}:{url}"
        now = time.time()
        hit = self.cache.get(cache_key)

        if hit and now - hit[1] < self.cache_timeout_s:
            try:
                if _normalize_text(getattr(hit[0], "title", "")).lower() != "en direct":
                    return hit[0]
            except Exception:
                return hit[0]

        md: Optional[RadioMetadata] = None

        try:
            st_base = station_name.strip().lower()
            u_base = _normalize_text(url).lower()
            looks_like_comercial = ("comercial" in st_base) or ("/comercial" in u_base) or ("comercial." in u_base)

            creds_path = _normalize_text(os.environ.get("MYTUNER_CREDS_FILE", ""))
            creds = _load_mytuner_creds_from_file(creds_path) if creds_path else {}

            auth = _normalize_text(creds.get("authorization") or os.environ.get("MYTUNER_AUTH", ""))
            tms = _normalize_text(creds.get("time") or os.environ.get("MYTUNER_TIME", ""))

            app = _normalize_text(
                creds.get("app")
                or creds.get("app_codename")
                or os.environ.get("MYTUNER_APP", "radioportugal_web")
            )
            rid = _normalize_text(creds.get("radio_id") or os.environ.get("MYTUNER_RADIO_ID", "413031"))
            origin = _normalize_text(creds.get("origin") or os.environ.get("MYTUNER_ORIGIN", "https://www.radios-online.pt"))
            referer = _normalize_text(creds.get("referer") or os.environ.get("MYTUNER_REFERER", "https://www.radios-online.pt/"))

            if looks_like_comercial and auth and tms and app and rid and origin and referer:
                md_mt = _fetch_mytuner_song_history(
                    self.session,
                    station_name,
                    app_codename=app,
                    radio_id=rid,
                    time_ms=tms,
                    authorization=auth if auth.lower().startswith("hmac ") else f"HMAC {auth}",
                    origin=origin,
                    referer=referer,
                )
                if md_mt:
                    md_mt.source = "mytuner"
                    self.cache[cache_key] = (md_mt, now)
                    return md_mt

            if looks_like_comercial:
                md_icy = _get_icy_metadata_with_max_blocks(
                    self.session,
                    "https://stream-icy.bauermedia.pt/comercial.mp3",
                    station_name,
                    max_blocks=10,
                )
                if md_icy and md_icy.title:
                    t = _normalize_text(md_icy.title)
                    is_xmlish = ("<radioinfo" in t.lower()) or t.lstrip().startswith("<?xml")
                    if (not is_xmlish) and t.lower() != "en direct":
                        md_icy.source = "icy"
                        self.cache[cache_key] = (md_icy, now)
                        return md_icy

                md_api = _fetch_radiocomercial_nowplaying_xml(self.session, station_name)
                if md_api:
                    md_api.source = "radiocomercial_xml"
                    self.cache[cache_key] = (md_api, now)
                    return md_api

                md_last0 = _fetch_bauermedia_radiocomercial_lastsongs_json(self.session, station_name)
                if md_last0:
                    md_last0.source = "bauer_json"
                    self.cache[cache_key] = (md_last0, now)
                    return md_last0
        except Exception:
            pass

        st_norm = station_name.strip().lower()
        u_norm = _normalize_text(url).lower()

        is_100radio80 = (
            "100% radio 80" in st_norm
            or "100 radio 80" in st_norm
            or "100radio80" in st_norm
            or "100radio80" in u_norm
            or "100radio-80" in u_norm
        )

        if is_100radio80:
            md = _fetch_100radio_ws_metas(self.session, station_name)
            if md:
                md.source = "100radio_ws"
                self.cache[cache_key] = (md, now)
                return md

            md = _fetch_infomaniak_icecast_status(self.session, url, station_name)
            if md:
                md.source = "icecast_status"
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

        if station_name.strip().lower() == "bide et musique":
            md = _fetch_bideetmusique_programme_page(self.session, station_name)
            if md:
                self.cache[cache_key] = (md, now)
                return md

            alt_url = url
            try:
                if isinstance(url, str) and ":9300" in url:
                    alt_url = url.replace(":9300", ":9100")
            except Exception:
                alt_url = url

            md = _get_icy_metadata_with_max_blocks(self.session, alt_url, station_name, max_blocks=10)
            self.cache[cache_key] = (md, now)
            return md

        if station_name.strip().lower() == "mega hits":
            resolved = _resolve_streamtheworld_redirect(self.session, url)
            md = _get_icy_metadata_with_max_blocks(self.session, resolved, station_name, max_blocks=18)
            md.source = "icy"
            self.cache[cache_key] = (md, now)
            return md

        is_flash80 = (
            "flash 80" in st_norm
            or (
                "streamradio.fr" in u_norm
                and (
                    ":1985" in u_norm
                    or ":1970" in u_norm
                    or "/stream" in u_norm
                )
            )
        )

        if is_flash80:
            # Some Streamradio setups behave differently depending on scheme/port.
            # Be defensive and try a small set of candidate bases.
            candidates = []
            try:
                parsed = urllib.parse.urlparse(_normalize_text(url))
                if parsed.hostname and parsed.port:
                    scheme = parsed.scheme or "https"
                    candidates.append(f"{scheme}://{parsed.hostname}:{parsed.port}")
                    # If HTTPS on this port fails (common), try HTTP too.
                    if scheme.lower() == "https":
                        candidates.append(f"http://{parsed.hostname}:{parsed.port}")
                    elif scheme.lower() == "http":
                        candidates.append(f"https://{parsed.hostname}:{parsed.port}")
            except Exception:
                pass

            # Known manager base (works even when stream is on another port).
            candidates.append("https://manager7.streamradio.fr:1970")
            candidates.append("http://manager7.streamradio.fr:1970")
            candidates.append("http://manager7.streamradio.fr:1985")

            seen = set()
            for base in candidates:
                b = _normalize_text(base)
                if not b or b in seen:
                    continue
                seen.add(b)

                md_mgr = _fetch_streamapps_manager_nowplaying(self.session, station_name, b, "1")
                if md_mgr:
                    md_mgr.source = "streamradio_manager"
                    self.cache[cache_key] = (md_mgr, now)
                    return md_mgr

            md_fast = RadioMetadata(station=station_name, title="En direct", artist=station_name, cover_url="")
            md_fast.source = "fallback"
            self.cache[cache_key] = (md_fast, now)
            return md_fast

        if station_name.strip().lower() == "rtl":
            md_rtl = _fetch_rtl_metadata(self.session, station_name)
            if md_rtl:
                self.cache[cache_key] = (md_rtl, now)
                return md_rtl

            md = self._get_icy_metadata(url, station_name)
            self.cache[cache_key] = (md, now)
            return md

        try:
            u = _normalize_text(url)
            is_bauer_hls = (
                u
                and ".m3u8" in u
                and (
                    "bauermedia.pt" in u
                    or "stream-hls.bauermedia.pt" in u
                    or "stream-hls.bauermedia.pt:443" in u
                )
            )
            if is_bauer_hls:
                md_hls = _fetch_bauer_hls_id3_metadata(self.session, u, station_name)
                if md_hls:
                    md_hls.source = "hls_id3"
                    self.cache[cache_key] = (md_hls, now)
                    return md_hls

                md_last = _fetch_bauermedia_radiocomercial_lastsongs_json(self.session, station_name)
                if md_last:
                    md_last.source = "bauer_json"
                    self.cache[cache_key] = (md_last, now)
                    return md_last

                # Fallback: Bauer ICY streams often carry RadioInfo XML inside StreamTitle.
                st = station_name.strip().lower()
                if "comercial" in st or "/comercial" in u:
                    md_icy = _get_icy_metadata_with_max_blocks(
                        self.session,
                        "https://stream-icy.bauermedia.pt/comercial.mp3",
                        station_name,
                        max_blocks=10,
                    )
                    if md_icy and md_icy.title:
                        t = _normalize_text(md_icy.title)
                        # Sometimes StreamTitle contains embedded RadioInfo XML; don't return it as-is.
                        is_xmlish = ("<radioinfo" in t.lower()) or t.lstrip().startswith("<?xml")
                        if (not is_xmlish) and t.lower() != "en direct":
                            md_icy.source = "icy"
                            self.cache[cache_key] = (md_icy, now)
                            return md_icy

                    md_api = _fetch_radiocomercial_nowplaying_xml(self.session, station_name)
                    if md_api:
                        md_api.source = "radiocomercial_xml"
                        self.cache[cache_key] = (md_api, now)
                        return md_api
        except Exception:
            pass

        md = self._get_icy_metadata(url, station_name)
        md.source = "icy"
        self.cache[cache_key] = (md, now)
        return md


def _fetch_streamradio_nowplaying(session: requests.Session, station_name: str) -> Optional[RadioMetadata]:
    try:
        base = "https://manager7.streamradio.fr:1970"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "fr-FR,fr;q=0.9",
            "Connection": "close",
        }

        global _STREAMRADIO_SERVER_ID, _STREAMRADIO_SERVER_ID_TS
        now = time.time()
        if not _STREAMRADIO_SERVER_ID or (now - _STREAMRADIO_SERVER_ID_TS) > 300:
            try:
                r0 = session.get(f"{base}/api/startpage/", timeout=1.5, headers=headers)
                if r0.status_code == 200:
                    data0 = None
                    try:
                        data0 = r0.json()
                    except Exception:
                        data0 = None
                    if isinstance(data0, dict):
                        cur = data0.get("currentServer")
                        if isinstance(cur, dict) and cur.get("id") is not None:
                            _STREAMRADIO_SERVER_ID = str(cur.get("id"))
                            _STREAMRADIO_SERVER_ID_TS = now
            except Exception:
                pass

        server_id = _STREAMRADIO_SERVER_ID or "1970"

        params = {
            "server": server_id,
            "limit": "1",
            "format": "jsonp",
        }

        r = session.get(f"{base}/api/v2/history/", params=params, timeout=2, headers=headers)
        if r.status_code != 200:
            return None

        payload = _extract_jsonp_payload(r.text or "")
        if not payload:
            return None

        try:
            data = json.loads(payload)
        except Exception:
            return None

        if not isinstance(data, dict):
            return None
        results = data.get("results")
        if not isinstance(results, list) or not results:
            return None
        item = results[0]
        if not isinstance(item, dict):
            return None

        meta = _normalize_text(str(item.get("metadata") or ""))
        cover_url = _normalize_text(str(item.get("img_medium_url") or item.get("img_url") or ""))

        if not meta:
            return None

        artist = station_name
        title = meta
        if " - " in meta:
            a, t = meta.split(" - ", 1)
            artist = _normalize_text(a) or station_name
            title = _normalize_text(t)
        if not title:
            return None

        return RadioMetadata(station=station_name, title=title, artist=artist, cover_url=cover_url)
    except Exception:
        return None


def _cli_json_once(station_name: str, url: str, no_cache: bool) -> int:
    try:
        fetcher = RadioFetcher()
        if no_cache:
            fetcher.cache_timeout_s = 0

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            md = fetcher.get_metadata(station_name, url)

        noisy = buf.getvalue()
        if noisy:
            sys.stderr.write(noisy)

        station = _normalize_text(md.station)
        title = _normalize_text(md.title)
        artist = _normalize_text(md.artist)
        source = _normalize_text(getattr(md, "source", ""))
        cover_url = "".join(_normalize_text(md.cover_url).split())

        cover_url = "".join(cover_url.split())

        # Defensive: some sources can surface raw XML or very long blobs.
        if title.lstrip().startswith("<?xml") or "<radioinfo" in title.lower():
            title = "En direct"
        if artist.lstrip().startswith("<?xml") or "<radioinfo" in artist.lower():
            artist = station

        # Keep output reasonable
        if len(title) > 300:
            title = title[:300]
        if len(artist) > 200:
            artist = artist[:200]
        if len(cover_url) > 500:
            cover_url = cover_url[:500]

        payload = {
            "station": station,
            "title": title,
            "artist": artist,
            "cover_url": cover_url,
            "source": source,
        }
        print(json.dumps(payload, ensure_ascii=False))
        return 0
    except Exception as e:
        sys.stderr.write(str(e))
        sys.stderr.write("\n")
        return 1


def _cli_poll(station_name: str, url: str, interval_s: float, duration_s: float, json_mode: bool, no_cache: bool) -> int:
    try:
        fetcher = RadioFetcher()
        if no_cache:
            fetcher.cache_timeout_s = 0

        t0 = time.time()
        last_key = None

        while True:
            if duration_s > 0 and (time.time() - t0) >= duration_s:
                return 0

            md = fetcher.get_metadata(station_name, url)

            station = _normalize_text(md.station)
            title = _normalize_text(md.title)
            artist = _normalize_text(md.artist)
            source = _normalize_text(getattr(md, "source", ""))
            cover_url = "".join(_normalize_text(md.cover_url).split())

            key = f"{artist} — {title}" if (artist or title) else title
            if key and key != last_key:
                last_key = key
                payload = {
                    "station": station,
                    "title": title,
                    "artist": artist,
                    "cover_url": cover_url,
                    "source": source,
                }
                if json_mode:
                    print(json.dumps(payload, ensure_ascii=False))
                else:
                    if artist and title and artist.lower() != station.lower() and title.lower() != "en direct":
                        print(f"{artist} - {title}")
                    else:
                        print(title or "En direct")

            time.sleep(max(0.2, float(interval_s)))
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        sys.stderr.write(str(e))
        sys.stderr.write("\n")
        return 1


def _print_supported_stations() -> None:
    print("100% Radio 80")
    print("Nostalgie-Les 80 Plus Grand Tubes")
    print("Nostalgie-Les Tubes 80 N1")


def _print_all_radios() -> None:
    for name, url in RADIOS:
        print(f"{name} | {url}")


def _run_all_radios() -> int:
    fetcher = RadioFetcher()

    def _truncate(s: str, max_len: int) -> str:
        s2 = _normalize_text(s)
        if not s2:
            return ""
        if len(s2) <= max_len:
            return s2
        return s2[: max(0, max_len - 1)] + "…"


    def _short_url(u: str, max_len: int) -> str:
        u2 = _normalize_text(u)
        if not u2:
            return ""
        try:
            p = urlparse(u2)
            host = p.netloc
            path = p.path or ""
            base = path.rstrip("/").split("/")[-1] if path else ""
            if base:
                return _truncate(base, max_len)
            if host:
                return _truncate(host, max_len)
        except Exception:
            pass
        return _truncate(u2, max_len)


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
                print(_truncate(name, 42))

                title = _truncate(md.title, 26)
                artist = _truncate(md.artist, 16)
                cover = _short_url(md.cover_url, 14)

                if not title or title.lower() == "en direct":
                    line2 = "  En direct"
                elif artist and artist.lower() != _normalize_text(name).lower():
                    line2 = f"  {artist} - {title}"
                else:
                    line2 = f"  {title}"

                if cover:
                    line2 = f"{line2} | {cover}"

                print(_truncate(line2, 60))
                print("")
            except Exception as e:
                print(f"ERROR | {str(e)[:200]}")

    return 0


def _entrypoint() -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--poll", action="store_true")
    parser.add_argument("--interval", type=float, default=5.0)
    parser.add_argument("--duration", type=float, default=0.0)
    parser.add_argument("--no-cache", action="store_true")
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

    if args.poll:
        if not args.url:
            sys.stderr.write("Missing --url\n")
            return 2
        if not args.station:
            args.station = "Custom"
        return _cli_poll(
            args.station,
            args.url,
            interval_s=args.interval,
            duration_s=args.duration,
            json_mode=bool(args.json),
            no_cache=bool(args.no_cache),
        )

    if args.json:
        if not args.url:
            sys.stderr.write("Missing --url\n")
            return 2
        if not args.station:
            args.station = "Custom"
        return _cli_json_once(args.station, args.url, no_cache=bool(args.no_cache))

    sys.stderr.write("Use --json --station <name> --url <stream_url>\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(_entrypoint())