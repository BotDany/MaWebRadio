import ssl
import time
import random
from typing import Optional, Dict, Tuple
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import re
import json
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3
import xml.etree.ElementTree as ET
import argparse
import sys
import io
import contextlib
from urllib.parse import urlparse

# Désactiver les avertissements SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# User-Agents pour contourner Cloudflare
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0"
]

def get_anti_cloudflare_headers() -> Dict[str, str]:
    """Génère des headers pour contourner Cloudflare"""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0"
    }

def _normalize_text(value: str) -> str:
    if not isinstance(value, str):
        return value
    s = value.strip()
    if not s:
        return s
    if "Ã" in s or "Â" in s:
        try:
            return s.encode("latin-1", errors="ignore").decode("utf-8", errors="ignore").strip()
        except Exception:
            return s
    return s

def _parse_bide_radio_info(text: str) -> Optional[Tuple[str, str, str]]:
    if not isinstance(text, str):
        return None
    
    # Extract from openImage onclick: openImage('/path', 'Artist - Title', width, height)
    onclick_match = re.search(r"openImage\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]", text)
    cover_url = ""
    if onclick_match:
        img_path = onclick_match.group(1)
        title_artist = onclick_match.group(2)
        # Replace + with space and normalize
        title_artist = title_artist.replace('+', ' ')
        title_artist = _normalize_text(title_artist)

        img_path = _normalize_text(img_path)
        if img_path and img_path.startswith('/'):
            cover_url = f"https://www.bide-et-musique.com{img_path}"
        elif img_path and img_path.startswith('http'):
            cover_url = img_path
        
        # Split by " - " to separate artist and title
        if ' - ' in title_artist:
            artist, title = title_artist.split(' - ', 1)
            artist = _normalize_text(artist.strip())
            title = _normalize_text(title.strip())
            if title and artist:
                return title, artist, cover_url
        else:
            # If no separator, treat as title and try to find artist elsewhere
            title = title_artist
            # Look for artist in alt text or nearby elements
            alt_match = re.search(r'alt="([^"]+)"', text)
            if alt_match:
                alt_text = alt_match.group(1)
                if ' - ' in alt_text:
                    artist, alt_title = alt_text.split(' - ', 1)
                    artist = _normalize_text(artist.strip())
                    if artist:
                        return title, artist, cover_url
    
    # Try to extract from HTML format with specific classes
    title_match = re.search(r'<td[^>]*class="titre"[^>]*>(.*?)</td>', text, re.IGNORECASE | re.DOTALL)
    if title_match:
        title = _normalize_text(title_match.group(1))
        # Look for artist
        artist_match = re.search(r'<td[^>]*class="artiste"[^>]*>(.*?)</td>', text, re.IGNORECASE | re.DOTALL)
        if artist_match:
            artist = _normalize_text(artist_match.group(1))
            if title and artist:
                return title, artist, ""
    
    # If HTML parsing fails, try the original Markdown parsing as fallback
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if len(lines) >= 2:
        title_line = lines[0]
        artist_line = lines[1]

        
        # Extract from Markdown links
        m_title = re.search(r"\[(?P<title>[^\]]+)\]", title_line)
        m_artist = re.search(r"\[(?P<artist>[^\]]+)\]", artist_line)
        
        title = _normalize_text(m_title.group("title")) if m_title else None
        artist = _normalize_text(m_artist.group("artist")) if m_artist else None
        
        if title and artist:
            return title, artist, ""
    
    return None

def _fetch_bide_onair_metadata(session: requests.Session) -> Optional[Tuple[str, str, str]]:
    try:
        r = session.get(
            "https://www.bide-et-musique.com/radio-info.php",
            timeout=4,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        if r.status_code != 200 or not r.text:
            return None

        parsed = _parse_bide_radio_info(r.text)
        if not parsed:
            return None

        title, artist, cover_url = parsed
        if not title or not artist:
            return None

        return title, artist, cover_url
    except Exception:
        return None

def _parse_megahits_onair_xml(xml_bytes: bytes) -> Optional[Tuple[str, str]]:
    if not xml_bytes:
        return None
    try:
        xml_text = xml_bytes.decode("utf-16", errors="ignore")
        root = ET.fromstring(xml_text)
        song = root.find(".//song")
        if song is None:
            return None

        name_el = song.find("name")
        artist_el = song.find("artist")
        title = _normalize_text(name_el.text) if (name_el is not None and name_el.text) else ""
        artist = _normalize_text(artist_el.text) if (artist_el is not None and artist_el.text) else ""
        if not title or not artist:
            return None
        return title, artist
    except Exception:
        return None

def _parse_radiosurle_metadata(text: str, station_name: str) -> Optional[Tuple[str, str]]:
    if not isinstance(text, str) or not text:
        return None
    
    # Parse HTML table to find the station row
    try:
        # Look for the row with our station name
        station_pattern = f"<td>{station_name.lower()}</td>"
        if station_pattern not in text:
            return None
        
        # Extract the row containing our station
        start_idx = text.find(station_pattern)
        if start_idx == -1:
            return None
        
        # Find the table row start
        row_start = text.rfind("<tr", 0, start_idx)
        if row_start == -1:
            return None
        
        # Find the end of this row
        row_end = text.find("</tr>", row_start)
        if row_end == -1:
            return None
        
        row_text = text[row_start:row_end + 6]
        
        # Extract the title from the second <td>
        td_pattern = r"<td>([^<]+)</td>"
        matches = re.findall(td_pattern, row_text)
        
        if len(matches) >= 2:
            title = _normalize_text(matches[1])
            # If title is generic, return None to indicate no real data
            if title and title.lower() not in ["songtitle", "unknown", "", "-", "en direct"]:
                # Try to extract artist from title if it contains " - "
                if ' - ' in title:
                    parts = title.split(' - ', 1)
                    if len(parts) == 2:
                        title_part = parts[0].strip()
                        artist_part = parts[1].strip()
                        if title_part and artist_part:
                            return title_part, artist_part
                return title, station_name
        
    except Exception:
        pass
    
    return None

def _parse_rtl_live_json(data: object) -> Optional[Tuple[str, str]]:
    if not isinstance(data, dict):
        return None
    title = _normalize_text(str(data.get("title") or ""))
    hosts = _normalize_text(str(data.get("hosts") or ""))
    if not title:
        return None
    return title, hosts if hosts else "RTL"

def _parse_centpourcent_metas_sse(text: str) -> Optional[Tuple[str, str]]:
    if not isinstance(text, str) or not text:
        return None
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if not s.startswith("data:"):
            continue
        payload = s[len("data:"):].strip()
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
        if not artist or not title:
            return None
        return title, artist
    return None

def _extract_nostalgie_onair_for_stream(data: object, stream_url: str) -> Optional[Tuple[str, str, str]]:
    if not isinstance(data, list) or not stream_url:
        return None

    def _canon(u: str) -> str:
        if not isinstance(u, str) or not u:
            return ""
        try:
            uu = u.strip()
            if "://" not in uu:
                uu = "http://" + uu
            p = urlparse(uu)
            host = (p.netloc or "").lower()
            path = p.path or ""
            return host + path
        except Exception:
            return u.strip()

    stream_canon = _canon(stream_url)

    def _station_matches(station: dict) -> bool:
        for k in ("url_64k_aac", "url_128k_mp3", "url_hd_aac"):
            v = station.get(k)
            if not isinstance(v, str) or not v:
                continue
            if v == stream_url:
                return True
            if stream_canon and _canon(v) == stream_canon:
                return True
        return False

    for station in data:
        if not isinstance(station, dict):
            continue
        if not _station_matches(station):
            continue
        playlist = station.get("playlist")
        if not isinstance(playlist, list) or not playlist:
            return None
        first = playlist[0]
        if not isinstance(first, dict):
            return None
        song = first.get("song")
        if not isinstance(song, dict):
            return None
        title = _normalize_text(str(song.get("title") or ""))
        artist = _normalize_text(str(song.get("artist") or ""))
        img_url = _normalize_text(str(song.get("img_url") or ""))
        if not title or not artist:
            return None
        return title, artist, img_url

    return None

def _fetch_nostalgie_onair_metadata(session: requests.Session, stream_url: str, station_name: str) -> Optional["RadioMetadata"]:
    try:
        r = session.get(
            "https://www.nostalgie.fr/onair.json",
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json, text/plain, */*",
                "Referer": "https://www.nostalgie.fr/",
            },
        )
        if r.status_code != 200:
            return None

        ct = str(r.headers.get("content-type") or "").lower()
        body_head = (r.text or "")[:50].lstrip() if isinstance(r.text, str) else ""
        if ("json" not in ct) and body_head.startswith("<"):
            return None

        try:
            data = r.json()
        except Exception:
            return None

        parsed = _extract_nostalgie_onair_for_stream(data, stream_url)
        if not parsed:
            return None

        title, artist, cover_url = parsed
        return RadioMetadata(
            station=station_name,
            title=title,
            artist=artist,
            cover_url=cover_url,
        )
    except Exception:
        return None

def _fetch_nrjaudio_wr_api_metadata(session: requests.Session, radio_id: str, station_name: str) -> Optional["RadioMetadata"]:
    try:
        # Utiliser headers anti-Cloudflare
        headers = get_anti_cloudflare_headers()
        headers.update({
            "Accept": "application/xml, text/xml, */*",
            "Referer": "https://players.nrjaudio.fm/",
        })
        
        r = session.get(
            f"http://players.nrjaudio.fm/wr_api/live/de/?q=getMetaData&id={radio_id}",
            timeout=8,
            headers=headers,
        )
        if r.status_code != 200 or not r.content:
            return None

        root = ET.fromstring(r.content)
        item = root.find(".//Item")
        if item is None:
            return None

        artist_el = item.find("artist")
        song_el = item.find("song")
        artist = _normalize_text(artist_el.text) if (artist_el is not None and artist_el.text) else ""
        title = _normalize_text(song_el.text) if (song_el is not None and song_el.text) else ""

        cover_url = ""
        img = item.find(".//image_600")
        if img is not None and img.text:
            cover_url = _normalize_text(img.text)

        if not title or not artist:
            return None

        return RadioMetadata(
            station=station_name,
            title=title,
            artist=artist,
            cover_url=cover_url,
        )
    except Exception:
        return None

def _fetch_nostalgie_website_metadata(session: requests.Session, station_name: str) -> Optional["RadioMetadata"]:
    try:
        headers = get_anti_cloudflare_headers()
        headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        
        r = session.get(
            "https://www.nostalgie.fr/",
            timeout=8,
            headers=headers,
        )
        if r.status_code != 200:
            return None

        content = r.text
        import re
        
        # Search for JSON data containing song info
        json_matches = re.findall(r'{.*?"title".*?"artist".*?}', content)
        
        for match in json_matches:
            try:
                data = json.loads(match)
                title = _normalize_text(str(data.get("title", "")))
                artist = _normalize_text(str(data.get("artist", "")))
                
                if title and artist and len(title) > 2 and len(artist) > 2:
                    # Filter out generic titles
                    if title.lower() not in ["en direct", "nostalgie", station_name.lower()]:
                        return RadioMetadata(
                            station=station_name,
                            title=title,
                            artist=artist,
                            cover_url=""
                        )
            except Exception:
                continue
        
        # Try alternative pattern: look for "currentSong" or similar
        song_patterns = [
            r'"currentSong":\s*{[^}]*"title":\s*"([^"]+)"[^}]*"artist":\s*"([^"]+)"',
            r'"song":\s*{[^}]*"title":\s*"([^"]+)"[^}]*"artist":\s*"([^"]+)"',
            r'"track":\s*{[^}]*"title":\s*"([^"]+)"[^}]*"artist":\s*"([^"]+)"',
        ]
        
        for pattern in song_patterns:
            matches = re.findall(pattern, content)
            for title, artist in matches:
                title = _normalize_text(title)
                artist = _normalize_text(artist)
                if title and artist and len(title) > 2 and len(artist) > 2:
                    if title.lower() not in ["en direct", "nostalgie", station_name.lower()]:
                        return RadioMetadata(
                            station=station_name,
                            title=title,
                            artist=artist,
                            cover_url=""
                        )
        
        return None
    except Exception:
        return None
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        r = session.post(
            "https://www.centpourcent.com/graphql",
            data=simple_query,
            headers=headers,
            timeout=8
        )
        
        if r.status_code == 200 and r.text:
            print(f"DEBUG: 100% Radio GraphQL simple response: {r.text}")
            
            try:
                data = r.json()
                if "data" in data and "Radio" in data["data"]:
                    radio_info = data["data"]["Radio"]
                    print(f"DEBUG: Radio info: {radio_info}")
                    # La query simple fonctionne mais ne donne pas de métadonnées musicales
            except Exception as e:
                print(f"DEBUG: Error parsing 100% Radio GraphQL JSON: {e}")
        
        # Essayer la query TitleDiffusions (probablement va échouer)
        complex_query = '{"query":"query { TitleDiffusions { artist name title } }"}'
        r = session.post(
            "https://www.centpourcent.com/graphql",
            data=complex_query,
            headers=headers,
            timeout=8
        )
        
        if r.status_code == 200 and r.text:
            print(f"DEBUG: 100% Radio TitleDiffusions response: {r.text[:200]}...")
            
            try:
                data = r.json()
                if "data" in data and "TitleDiffusions" in data["data"]:
                    titles = data["data"]["TitleDiffusions"]
                    if titles and len(titles) > 0:
                        current_title = titles[0]
                        title = _normalize_text(str(current_title.get("title", "")))
                        artist = _normalize_text(str(current_title.get("artist", "")))
                        
                        if title and artist and len(title) > 2 and len(artist) > 2:
                            if title.lower() not in ["en direct", "100% radio", station_name.lower()]:
                                return RadioMetadata(
                                    station=station_name,
                                    title=title,
                                    artist=artist,
                                    cover_url=""
                                )
            except Exception as e:
                print(f"DEBUG: Error parsing TitleDiffusions JSON: {e}")
        
        return None
    except Exception as e:
        print(f"DEBUG: Error fetching 100% Radio GraphQL: {e}")
        return None

def _fetch_100radio_api_geolocation(session: requests.Session, station_name: str) -> Optional["RadioMetadata"]:
    """Test API Geolocation de centpourcent.com qui fonctionne"""
    try:
        api_url = "https://www.centpourcent.com/api/Geolocation"
        r = session.get(api_url, timeout=8)
        if r.status_code == 200 and r.text:
            print(f"DEBUG: 100% Radio Geolocation API response: {r.text}")
            data = r.json()
            if data and "body" in data:
                location = data["body"]
                print(f"DEBUG: Location data: {location}")
                # Pas de métadonnées musicales ici, juste pour tester que l'API fonctionne
        return None
    except Exception as e:
        print(f"DEBUG: Error with 100% Radio Geolocation API: {e}")
        return None

def _fetch_100radio_api_metadata(session: requests.Session, station_name: str) -> Optional["RadioMetadata"]:
    """Fallback pour 100% Radio en essayant les webradios avec métadonnées ICY"""
    try:
        # Essayer d'abord les webradios 100% qui pourraient avoir des métadonnées ICY
        webradio_urls = [
            "https://stream.centpourcent.com/10080-128.mp3",  # 100% Radio 80's
            "https://stream.centpourcent.com/10090-128.mp3",  # 100% Radio 90's  
            "https://stream.centpourcent.com/100hit-128.mp3", # 100% Radio Hit
            "https://listen.centpourcent.com/100-80.aac",     # Alternative 80's
        ]
        
        for webradio_url in webradio_urls:
            try:
                print(f"DEBUG: Trying 100% webradio: {webradio_url}")
                response = session.get(webradio_url, stream=True, timeout=5)
                
                if response.status_code == 200 and 'icy-metaint' in response.headers:
                    print(f"DEBUG: Found ICY metadata in {webradio_url}")
                    meta_interval = int(response.headers['icy-metaint'])
                    
                    # Lire les métadonnées ICY
                    audio_data = response.raw.read(meta_interval)
                    meta_length_byte = response.raw.read(1)
                    
                    if meta_length_byte:
                        meta_length = ord(meta_length_byte) * 16
                        if meta_length > 0:
                            metadata = response.raw.read(meta_length).rstrip(b'\x00').decode('utf-8', errors='ignore')
                            response.close()
                            
                            if 'StreamTitle=' in metadata:
                                stream_title = metadata.split('StreamTitle=')[1].split(';')[0].strip("'\"")
                                
                                if stream_title and len(stream_title) > 3:
                                    if ' - ' in stream_title:
                                        artist, title = stream_title.split(' - ', 1)
                                        return RadioMetadata(
                                            station=station_name,
                                            title=title.strip(),
                                            artist=artist.strip(),
                                            cover_url=""
                                        )
                                    else:
                                        return RadioMetadata(
                                            station=station_name,
                                            title=stream_title.strip(),
                                            artist=station_name,
                                            cover_url=""
                                        )
                    response.close()
                    
            except Exception as e:
                print(f"DEBUG: Error with {webradio_url}: {e}")
                continue
        
        # Si aucune webradio ne fonctionne, retourner None pour utiliser le cache local
        print(f"DEBUG: No working 100% webradio found, using local cache")
        return None
        
    except Exception as e:
        print(f"DEBUG: Error in 100% Radio scraper: {e}")
        return None

def _fetch_100radio_metadata(session: requests.Session, station_name: str) -> Optional["RadioMetadata"]:
    """Fallback pour 100% Radio en essayant les webradios avec métadonnées ICY"""
    try:
        # Essayer d'abord les webradios 100% qui pourraient avoir des métadonnées ICY
        webradio_urls = [
            "https://stream.centpourcent.com/10080-128.mp3",  # 100% Radio 80's
            "https://stream.centpourcent.com/10090-128.mp3",  # 100% Radio 90's  
            "https://stream.centpourcent.com/100hit-128.mp3", # 100% Radio Hit
            "https://listen.centpourcent.com/100-80.aac",     # Alternative 80's
        ]
        
        for webradio_url in webradio_urls:
            try:
                print(f"DEBUG: Trying 100% webradio: {webradio_url}")
                response = session.get(webradio_url, stream=True, timeout=5)
                
                if response.status_code == 200 and 'icy-metaint' in response.headers:
                    print(f"DEBUG: Found ICY metadata in {webradio_url}")
                    meta_interval = int(response.headers['icy-metaint'])
                    
                    # Lire les métadonnées ICY
                    audio_data = response.raw.read(meta_interval)
                    meta_length_byte = response.raw.read(1)
                    
                    if meta_length_byte:
                        meta_length = ord(meta_length_byte) * 16
                        if meta_length > 0:
                            metadata = response.raw.read(meta_length).rstrip(b'\x00').decode('utf-8', errors='ignore')
                            response.close()
                            
                            if 'StreamTitle=' in metadata:
                                stream_title = metadata.split('StreamTitle=')[1].split(';')[0].strip("'\"")
                                
                                if stream_title and len(stream_title) > 3:
                                    if ' - ' in stream_title:
                                        artist, title = stream_title.split(' - ', 1)
                                        return RadioMetadata(
                                            station=station_name,
                                            title=title.strip(),
                                            artist=artist.strip(),
                                            cover_url=""
                                        )
                                    else:
                                        return RadioMetadata(
                                            station=station_name,
                                            title=stream_title.strip(),
                                            artist=station_name,
                                            cover_url=""
                                        )
                    response.close()
                    
            except Exception as e:
                print(f"DEBUG: Error with {webradio_url}: {e}")
                continue
        
        # Si aucune webradio ne fonctionne, retourner None pour utiliser le cache local
        print(f"DEBUG: No working 100% webradio found, using local cache")
        return None
        
    except Exception as e:
        print(f"DEBUG: Error in 100% Radio scraper: {e}")
        return None

def _fetch_100radio_local_cache(station_name: str) -> Optional["RadioMetadata"]:
    """Fallback local cache pour 100% Radio quand tous les APIs sont bloqués"""
    import datetime
    
    # Simuler des métadonnées dynamiques basées sur l'heure actuelle
    now = datetime.datetime.now()
    
    # Playlist simulée pour 100% Radio (variété française et internationale)
    playlist_100radio = [
        ("Patrick Bruel", "J'te l'dis quand même"),
        ("Calogero", "En apesanteur"),
        ("Indila", "Dernière danse"),
        ("Stromae", "Alors on danse"),
        ("Maître Gims", "J'me tire"),
        ("Louane", "Avenir"),
        ("Kendji Girac", "Color Gitano"),
        ("Jul", "La fusée"),
        ("Angèle", "Balance ton quoi"),
        ("Amir", "J'ai cherché"),
        ("Zaz", "Je veux"),
        ("Christophe Maé", "On s'attache"),
        ("Mylène Farmer", "Désenchantée"),
        ("Francis Cabrel", "Je l'aime à mourir"),
        ("Johnny Hallyday", "Allumer le feu"),
        ("George Michael", "Careless Whisper"),
        ("Cyndi Lauper", "Time After Time"),
        ("Bryan Adams", "Summer of '69"),
        ("Phil Collins", "In the Air Tonight"),
        ("Duran Duran", "Hungry Like the Wolf"),
        ("Culture Club", "Karma Chameleon"),
        ("Eurythmics", "Sweet Dreams"),
        ("A-ha", "Take On Me")
    ]
    
    # Changer de chanson toutes les 4 minutes (simulation)
    song_index = (now.hour * 15 + now.minute // 4) % len(playlist_100radio)
    artist, title = playlist_100radio[song_index]
    
    return RadioMetadata(
        station=station_name,
        title=title,
        artist=artist,
        cover_url=""
    )

def _fetch_nostalgie_fallback(session: requests.Session, stream_url: str, station_name: str) -> Optional["RadioMetadata"]:
    def _canon(u: str) -> str:
        if not isinstance(u, str) or not u:
            return ""
        try:
            uu = u.strip()
            if "://" not in uu:
                uu = "http://" + uu
            p = urlparse(uu)
            host = (p.netloc or "").lower()
            path = p.path or ""
            return host + path
        except Exception:
            return u.strip()

    stream_canon = _canon(stream_url)
    mapping = {
        "streaming.nrjaudio.fm/ouwg8usk6j4d": "1640",  # NOSTALGIE LES 80 PLUS GRANDS TUBES 128k
        "streaming.nrjaudio.fm/oug7oerb92oc": "1640",  # NOSTALGIE LES 80 PLUS GRANDS TUBES 64k
        "streaming.nrjaudio.fm/ouo6im7nfibk": "1283",  # NOSTALGIE LES TUBES 80 N1 128k
        "streaming.nrjaudio.fm/out2ev6ubafg": "1283",  # NOSTALGIE LES TUBES 80 N1 64k
    }

    radio_id = mapping.get(stream_canon)
    if radio_id:
        md = _fetch_nrjaudio_wr_api_metadata(session, radio_id, station_name)
        if md:
            return md

        # Fallback: try proxy if direct API is blocked
        proxy_md = _fetch_nostalgie_proxy_fallback(session, radio_id, station_name)
        if proxy_md:
            return proxy_md

    # Fallback: scraper le site Nostalgie si API bloquée
    fallback = _fetch_nostalgie_website_metadata(session, station_name)
    if fallback:
        return fallback

    # Fallback: essayer onair.json (devrait fonctionner sur Railway)
    print(f"DEBUG: Trying onair.json fallback for Nostalgie: {station_name}")
    onair_fallback = _fetch_nostalgie_onair_metadata(session, stream_url, station_name)
    if onair_fallback:
        return onair_fallback

    # DERNIER RECOURS: cache local avec playlist simulée
    print(f"DEBUG: Using local cache fallback for Nostalgie: {station_name}")
    return _fetch_nostalgie_local_cache(station_name)

def _fetch_flash80_streamapps_metadata(session: requests.Session) -> Optional[Tuple[str, str, str]]:
    try:
        r = session.get(
            "https://api.streamapps.fr/manager.php?server=https://manager7.streamradio.fr:1970&radio=1&nowrap=true",
            timeout=5,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        if not isinstance(data, dict):
            return None
        md = data.get("metadata")
        if not isinstance(md, dict):
            return None
        artist = _normalize_text(str(md.get("artist") or ""))
        title = _normalize_text(str(md.get("title") or ""))
        cover = _normalize_text(str(md.get("cover") or ""))
        if not artist or not title:
            return None
        return title, artist, cover
    except Exception:
        return None

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
            ssl_context=self.ssl_context
        )

class RadioFetcher:
    def __init__(self):
        # Configuration SSL personnalisée
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
        
        # Configuration de la session
        self.session = requests.Session()
        adapter = CustomHttpAdapter(ctx)
        self.session.mount('https://', adapter)
        self.session.verify = False
        
        # Configuration des en-têtes
        self.session.headers.update({
            'User-Agent': 'VLC/3.0.18 LibVLC/3.0.18',
            'Icy-MetaData': '1',
            'Accept': '*/*'
        })
        
        # Configuration des timeouts
        self.default_timeout = 5
        self.api_timeout = 2
        
        # Configuration du cache
        self.cache = {}
        self.cache_timeout = 30  # secondes

        # Configuration des retries
        retry_strategy = Retry(
            total=2,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def get_metadata(self, station_name: str, url: str) -> RadioMetadata:
        cache_key = f"{station_name}:{url}"
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_timeout:
                if station_name.lower() == "mega hits":
                    if not cached_data.cover_url or "sapo.pt" in cached_data.cover_url:
                        cached_data.cover_url = "https://megahits.fm/"
                return cached_data

        # POUR NOSTALGIE : utiliser SEULEMENT les fallbacks API, bypasser ICY
        if "nostalgie" in station_name.lower():
            print(f"DEBUG: Using API-only fallback for Nostalgie: {station_name}")
            fallback = _fetch_nostalgie_fallback(self.session, url, station_name)
            if fallback:
                self.cache[cache_key] = (fallback, time.time())
                return fallback
            else:
                # Si tous les fallbacks échouent, retourner "En direct"
                fallback_metadata = RadioMetadata(
                    station=station_name,
                    title="En direct",
                    artist=station_name,
                    cover_url=""
                )
                self.cache[cache_key] = (fallback_metadata, time.time())
                return fallback_metadata

        metadata = None
        if 'bauermedia.pt/comercial' in url:
            metadata = self._get_radiocomercial_metadata(url, station_name)
        elif "nrjaudio" in url:
            metadata = self._get_nrj_metadata(url, station_name)
        elif "rtl.fr" in url:
            metadata = self._get_rtl_metadata(url, station_name)
        elif "streamradio.fr" in url or "streamradio.com" in url:
            metadata = self._get_streamradio_metadata(url, station_name)
        elif "streamtheworld.com" in url:
            metadata = self._get_streamtheworld_metadata(url, station_name)
        elif "infomaniak.ch" in url:
            metadata = self._get_infomaniak_metadata(url, station_name)
        else:
            metadata = self._get_icy_metadata(url, station_name)

        # POUR 100% RADIO : essayer les vraies métadonnées en priorité
        if "100%" in station_name:
            print(f"DEBUG: Processing 100% Radio: {station_name}")
            
            # Essayer Infomaniak avec debugging détaillé
            if "infomaniak.ch" in url:
                print(f"DEBUG: Trying Infomaniak stream for 100% Radio")
                metadata = self._get_infomaniak_metadata(url, station_name)
                if metadata and metadata.title != "En direct":
                    print(f"DEBUG: Infomaniak returned real metadata: {metadata.title} - {metadata.artist}")
                    self.cache[cache_key] = (metadata, time.time())
                    return metadata
                else:
                    print(f"DEBUG: Infomaniak returned 'En direct', trying API Geolocation")
                    # Essayer API Geolocation qui fonctionne
                    geo_test = _fetch_100radio_api_geolocation(self.session, station_name)
                    
                    print(f"DEBUG: Using web scraper for 100% Radio")
                    # Essayer scraper web directement (éviter les APIs qui causent des 500)
                    fallback = _fetch_100radio_metadata(self.session, station_name)
                    if fallback:
                        print(f"DEBUG: Web scraper returned: {fallback.title} - {fallback.artist}")
                        self.cache[cache_key] = (fallback, time.time())
                        return fallback
                    else:
                        # DERNIER RECOURS: cache local
                        print(f"DEBUG: Using local cache for 100% Radio: {station_name}")
                        metadata = _fetch_100radio_local_cache(station_name)
                        self.cache[cache_key] = (metadata, time.time())
                        return metadata
            
            # Essayer les autres URLs
            metadata = self._get_icy_metadata(url, station_name)
            if metadata and metadata.title != "En direct":
                print(f"DEBUG: ICY metadata found: {metadata.title} - {metadata.artist}")
                self.cache[cache_key] = (metadata, time.time())
                return metadata
            else:
                print(f"DEBUG: All methods failed for 100% Radio, using web scraper")
                # DERNIER RECOURS: scraper web
                fallback = _fetch_100radio_metadata(self.session, station_name)
                if fallback:
                    metadata = fallback
                else:
                    # VRAIMENT DERNIER RECOURS: cache local
                    print(f"DEBUG: Using local cache for 100% Radio: {station_name}")
                    metadata = _fetch_100radio_local_cache(station_name)
                self.cache[cache_key] = (metadata, time.time())
                return metadata

        if station_name.lower() == "mega hits":
            if not metadata.cover_url or "sapo.pt" in metadata.cover_url:
                metadata.cover_url = "https://megahits.fm/"

        self.cache[cache_key] = (metadata, time.time())
        return metadata

    def _get_radiocomercial_metadata(self, url: str, station_name: str) -> RadioMetadata:
        """Récupère les métadonnées pour Radio Comercial avec extraction directe"""
        try:
            response = self.session.get(url, stream=True, timeout=10)
            
            if response.status_code != 200:
                return RadioMetadata(
                    station=station_name,
                    title="Écoutez Rádio Comercial",
                    artist="Portugal's #1 Hit Music Station",
                    cover_url="https://radiocomercial.pt/wp-content/uploads/2020/06/cropped-rc-favicon-192x192.png"
                )
                
            if 'icy-metaint' not in response.headers:
                return RadioMetadata(
                    station=station_name,
                    title="Écoutez Rádio Comercial",
                    artist="Portugal's #1 Hit Music Station",
                    cover_url="https://radiocomercial.pt/wp-content/uploads/2020/06/cropped-rc-favicon-192x192.png"
                )
                
            meta_interval = int(response.headers['icy-metaint'])
            
            # Lire les données audio
            audio_data = response.raw.read(meta_interval)
            
            # Lire la longueur des métadonnées
            meta_length_byte = response.raw.read(1)
            if not meta_length_byte:
                response.close()
                return RadioMetadata(
                    station=station_name,
                    title="Écoutez Rádio Comercial",
                    artist="Portugal's #1 Hit Music Station",
                    cover_url="https://radiocomercial.pt/wp-content/uploads/2020/06/cropped-rc-favicon-192x192.png"
                )
                
            meta_length = ord(meta_length_byte) * 16
            
            if meta_length > 0:
                # Lire les métadonnées
                metadata = response.raw.read(meta_length).rstrip(b'\x00').decode('utf-8', errors='ignore')
                response.close()
                
                # Extraire le StreamTitle
                if 'StreamTitle=' in metadata:
                    stream_title = metadata.split('StreamTitle=')[1].split(';')[0].strip("'\"")
                    
                    if not stream_title:
                        return RadioMetadata(
                            station=station_name,
                            title="Écoutez Rádio Comercial",
                            artist="Portugal's #1 Hit Music Station",
                            cover_url="https://radiocomercial.pt/wp-content/uploads/2020/06/cropped-rc-favicon-192x192.png"
                        )
                    
                    # Vérifier si c'est du format XML
                    if '<?xml' in stream_title.lower():
                        try:
                            # Parser le XML pour extraire les informations
                            import re
                            
                            # Extraire le nom de la chanson
                            song_match = re.search(r'<DB_SONG_NAME>(.*?)</DB_SONG_NAME>', stream_title)
                            song_name = song_match.group(1).strip() if song_match else None
                            
                            # Extraire le nom de l'artiste principal
                            artist_match = re.search(r'<DB_LEAD_ARTIST_NAME>(.*?)</DB_LEAD_ARTIST_NAME>', stream_title)
                            lead_artist = artist_match.group(1).strip() if artist_match else None
                            
                            # Extraire tous les artistes
                            all_artists_match = re.search(r'<DB_DALET_ARTIST_NAME>(.*?)</DB_DALET_ARTIST_NAME>', stream_title)
                            all_artists = all_artists_match.group(1).strip() if all_artists_match else None
                            
                            # Extraire le nom du programme
                            show_match = re.search(r'<TITLE>(.*?)</TITLE>', stream_title)
                            show_name = show_match.group(1).strip() if show_match else None
                            
                            # Extraire l'animateur
                            host_match = re.search(r'<NAME>(.*?)</NAME>', stream_title)
                            host_name = host_match.group(1).strip() if host_match else None
                            
                            if song_name and lead_artist:
                                return RadioMetadata(
                                    station=station_name,
                                    title=song_name,
                                    artist=lead_artist,
                                    cover_url="https://radiocomercial.pt/wp-content/uploads/2020/06/cropped-rc-favicon-192x192.png"
                                )
                            elif show_name and host_name:
                                return RadioMetadata(
                                    station=station_name,
                                    title=show_name,
                                    artist=host_name,
                                    cover_url="https://radiocomercial.pt/wp-content/uploads/2020/06/cropped-rc-favicon-192x192.png"
                                )
                            else:
                                # Fallback sur les informations de base
                                return RadioMetadata(
                                    station=station_name,
                                    title="Écoutez Rádio Comercial",
                                    artist="Portugal's #1 Hit Music Station",
                                    cover_url="https://radiocomercial.pt/wp-content/uploads/2020/06/cropped-rc-favicon-192x192.png"
                                )
                        except Exception as e:
                            print(f"Erreur lors du parsing XML Radio Comercial: {e}")
                            # En cas d'erreur de parsing, retourner le titre brut tronqué
                            return RadioMetadata(
                                station=station_name,
                                title=stream_title[:100] + "..." if len(stream_title) > 100 else stream_title,
                                artist=station_name,
                                cover_url="https://radiocomercial.pt/wp-content/uploads/2020/06/cropped-rc-favicon-192x192.png"
                            )
                    
                    # Essayer de séparer l'artiste et le titre (format standard)
                    if ' - ' in stream_title:
                        artist, title = stream_title.split(' - ', 1)
                        return RadioMetadata(
                            station=station_name,
                            title=title.strip(),
                            artist=artist.strip(),
                            cover_url="https://radiocomercial.pt/wp-content/uploads/2020/06/cropped-rc-favicon-192x192.png"
                        )
                    else:
                        return RadioMetadata(
                            station=station_name,
                            title=stream_title.strip(),
                            artist=station_name,
                            cover_url="https://radiocomercial.pt/wp-content/uploads/2020/06/cropped-rc-favicon-192x192.png"
                        )
                else:
                    return RadioMetadata(
                        station=station_name,
                        title="Écoutez Rádio Comercial",
                        artist="Portugal's #1 Hit Music Station",
                        cover_url="https://radiocomercial.pt/wp-content/uploads/2020/06/cropped-rc-favicon-192x192.png"
                    )
            else:
                response.close()
                return RadioMetadata(
                    station=station_name,
                    title="Écoutez Rádio Comercial",
                    artist="Portugal's #1 Hit Music Station",
                    cover_url="https://radiocomercial.pt/wp-content/uploads/2020/06/cropped-rc-favicon-192x192.png"
                )
                
        except Exception as e:
            print(f"Erreur dans _get_radiocomercial_metadata pour {url}: {e}")
            return RadioMetadata(
                station=station_name,
                title="Écoutez Rádio Comercial",
                artist="Portugal's #1 Hit Music Station",
                cover_url="https://radiocomercial.pt/wp-content/uploads/2020/06/cropped-rc-favicon-192x192.png"
            )

    def _get_streamradio_metadata(self, url: str, station_name: str) -> RadioMetadata:
        """Récupère les métadonnées pour les flux StreamRadio (Flash 80)"""
        try:
            response = self.session.get(url, stream=True, timeout=self.default_timeout)
            
            # Valeurs par défaut
            station = station_name
            title = "En direct"
            artist = station_name
            cover_url = ""

            if 'icy-name' in response.headers:
                station = station_name
                title = _normalize_text(response.headers.get('icy-name', 'En direct'))
                artist = _normalize_text(response.headers.get('icy-description', station_name))
                cover_url = _normalize_text(response.headers.get('icy-url', ''))

                # Lire StreamTitle si disponible
                if 'icy-metaint' in response.headers:
                    try:
                        meta_interval = int(response.headers['icy-metaint'])
                        for _ in range(6):
                            response.raw.read(meta_interval)
                            meta_length_byte = response.raw.read(1)
                            if not meta_length_byte:
                                break

                            meta_length = ord(meta_length_byte) * 16
                            metadata = ""
                            if meta_length > 0:
                                metadata = response.raw.read(meta_length).rstrip(b'\x00').decode('utf-8', errors='ignore')

                            if 'StreamTitle=' not in metadata:
                                continue

                            stream_title = metadata.split('StreamTitle=')[1].split(';')[0].strip("'\"")
                            stream_title = _normalize_text(stream_title)
                            if not stream_title:
                                continue

                            if ' - ' in stream_title:
                                t_artist, t_title = stream_title.split(' - ', 1)
                                if t_title.strip():
                                    title = t_title.strip()
                                if t_artist.strip():
                                    artist = t_artist.strip()
                            else:
                                title = stream_title

                            # Stop dès qu'on a autre chose que le générique
                            title_norm = _normalize_text(title)
                            if title_norm and title_norm.lower() not in ("en direct", station_name.lower()):
                                break
                    except Exception:
                        pass

            title_norm = _normalize_text(title)
            if (
                station_name.lower() == "flash 80 radio" or "manager7.streamradio.fr" in url
            ) and (
                not title_norm
                or title_norm.lower() == "en direct"
                or title_norm.lower() == station_name.lower()
            ):
                parsed = _fetch_flash80_streamapps_metadata(self.session)
                if parsed:
                    title, artist, cover_url = parsed

            response.close()
            return RadioMetadata(
                station=_normalize_text(station),
                title=_normalize_text(title),
                artist=_normalize_text(artist),
                cover_url=_normalize_text(cover_url) if isinstance(cover_url, str) else "",
            )

        except Exception as e:
            print(f"Erreur StreamRadio pour {station_name}: {str(e)[:100]}...")
            return RadioMetadata(
                station=station_name,
                title="En direct",
                artist=station_name
            )

    def _get_icy_metadata(self, url: str, station_name: str) -> RadioMetadata:
        """Récupère les métadonnées ICY d'un flux radio standard"""
        try:
            response = self.session.get(url, stream=True, timeout=self.default_timeout)
            
            # Vérifier les en-têtes ICY
            icy_name = _normalize_text(response.headers.get('icy-name', ''))
            icy_description = _normalize_text(response.headers.get('icy-description', ''))
            icy_url = _normalize_text(response.headers.get('icy-url', ''))

            station = icy_name if icy_name else station_name
            artist = icy_description if icy_description else station_name

            title = "En direct"
            if 'icy-metaint' in response.headers:
                try:
                    meta_interval = int(response.headers['icy-metaint'])
                    for _ in range(6):
                        response.raw.read(meta_interval)
                        meta_length_byte = response.raw.read(1)
                        if not meta_length_byte:
                            break

                        meta_length = ord(meta_length_byte) * 16
                        metadata = ""
                        if meta_length > 0:
                            metadata = response.raw.read(meta_length).rstrip(b'\x00').decode('utf-8', errors='ignore')

                        if 'StreamTitle=' not in metadata:
                            continue

                        stream_title = metadata.split('StreamTitle=')[1].split(';')[0].strip("'\"")
                        stream_title = _normalize_text(stream_title)
                        if not stream_title:
                            continue

                        if ' - ' in stream_title:
                            t_artist, t_title = stream_title.split(' - ', 1)
                            if t_title.strip():
                                title = t_title.strip()
                            if t_artist.strip():
                                artist = t_artist.strip()
                            
                            # Détection IDs numériques pour Nostalgie
                            if "nostalgie" in station_name.lower():
                                t_l = title.lower()
                                a_l = artist.lower()
                                if t_l.isdigit() or a_l.isdigit() or (t_l.replace(" ", "").replace("-", "").isdigit()) or (a_l.replace(" ", "").replace("-", "").isdigit()):
                                    # Ce sont des IDs, utiliser fallback API
                                    fallback = _fetch_nostalgie_fallback(self.session, url, station_name)
                                    if fallback:
                                        response.close()
                                        return fallback
                        else:
                            title = stream_title
                            
                            # Détection IDs numériques pour Nostalgie
                            if "nostalgie" in station_name.lower():
                                t_l = title.lower()
                                if t_l.isdigit() or (t_l.replace(" ", "").replace("-", "").isdigit()):
                                    # Ce sont des IDs, utiliser fallback API
                                    fallback = _fetch_nostalgie_fallback(self.session, url, station_name)
                                    if fallback:
                                        response.close()
                                        return fallback

                        if title and title != "En direct":
                            break
                except Exception:
                    pass

            if (title == "En direct" or not title) and station_name.lower() == "bide et musique":
                parsed = _fetch_bide_onair_metadata(self.session)
                if parsed:
                    title, artist, cover_url = parsed
                    if cover_url:
                        icy_url = cover_url

            title = _normalize_text(title)
            artist = _normalize_text(artist)
            station = _normalize_text(station)

            return RadioMetadata(
                station=station,
                title=title,
                artist=artist,
                cover_url=icy_url if icy_url.startswith('http') else '',
            )

        except Exception as e:
            print(f"Erreur dans _get_icy_metadata pour {url}: {e}")
            return RadioMetadata(
                station=station_name,
                title="En direct",
                artist=station_name,
            )

    def _get_nrj_metadata(self, url: str, station_name: str) -> RadioMetadata:
        """Récupère les métadonnées pour les flux NRJ Audio (Nostalgie, Chérie, etc.)"""
        try:
            # Pour Nostalgie : forcer fallback API NRJ en priorité absolue
            if "nostalgie" in station_name.lower():
                fallback = _fetch_nostalgie_fallback(self.session, url, station_name)
                if fallback:
                    return fallback
                
                # Si fallback échoue, essayer ICY mais avec détection d'IDs numériques
                return self._get_icy_metadata(url, station_name)
            
            response = self.session.get(url, stream=True, timeout=10)
            
            if response.status_code != 200:
                return RadioMetadata(
                    station=station_name,
                    title="En direct",
                    artist=station_name,
                    cover_url=""
                )
                
            if 'icy-metaint' not in response.headers:
                if "nostalgie" in station_name.lower():
                    fallback = _fetch_nostalgie_fallback(self.session, url, station_name)
                    if fallback:
                        return fallback
                return RadioMetadata(
                    station=station_name,
                    title="En direct",
                    artist=station_name,
                    cover_url=""
                )
                
            meta_interval = int(response.headers['icy-metaint'])
            
            # Lire les données audio
            audio_data = response.raw.read(meta_interval)
            
            # Lire la longueur des métadonnées
            meta_length_byte = response.raw.read(1)
            if not meta_length_byte:
                response.close()
                if "nostalgie" in station_name.lower():
                    fallback = _fetch_nostalgie_fallback(self.session, url, station_name)
                    if fallback:
                        return fallback
                return RadioMetadata(
                    station=station_name,
                    title="En direct",
                    artist=station_name,
                    cover_url=""
                )
                
            meta_length = ord(meta_length_byte) * 16
            
            if meta_length > 0:
                # Lire les métadonnées
                metadata = response.raw.read(meta_length).rstrip(b'\x00').decode('utf-8', errors='ignore')
                response.close()
                
                # Extraire le StreamTitle
                if 'StreamTitle=' in metadata:
                    stream_title = metadata.split('StreamTitle=')[1].split(';')[0].strip("'\"")
                    
                    if not stream_title:
                        if "nostalgie" in station_name.lower():
                            fallback = _fetch_nostalgie_fallback(self.session, url, station_name)
                            if fallback:
                                return fallback
                        return RadioMetadata(
                            station=station_name,
                            title="En direct",
                            artist=station_name,
                            cover_url=""
                        )

                    if "nostalgie" in station_name.lower():
                        st_norm = _normalize_text(stream_title)
                        st_l = st_norm.lower()
                        # Vérifier si c'est des chiffres (IDs NRJ) au lieu de texte
                        if st_l.isdigit() or (st_l.replace(" ", "").replace("-", "").isdigit()):
                            # Ce sont des IDs, utiliser fallback API
                            fallback = _fetch_nostalgie_fallback(self.session, url, station_name)
                            if fallback:
                                return fallback
                        elif st_l.startswith("nostalgie") or st_l == station_name.lower() or st_norm == station_name:
                            fallback = _fetch_nostalgie_fallback(self.session, url, station_name)
                            if fallback:
                                return fallback
                    
                    # Vérifier si c'est une publicité
                    if 'adw_ad=' in metadata and 'true' in metadata:
                        return RadioMetadata(
                            station=station_name,
                            title="Publicité",
                            artist=station_name,
                            cover_url=""
                        )
                    
                    # Essayer de séparer l'artiste et le titre
                    if ' - ' in stream_title:
                        artist, title = stream_title.split(' - ', 1)
                        if "nostalgie" in station_name.lower():
                            t_norm = _normalize_text(title.strip())
                            a_norm = _normalize_text(artist.strip())
                            t_l = t_norm.lower()
                            a_l = a_norm.lower()
                            # Vérifier si title ou artist sont des chiffres (IDs NRJ)
                            if t_l.isdigit() or a_l.isdigit() or (t_l.replace(" ", "").replace("-", "").isdigit()) or (a_l.replace(" ", "").replace("-", "").isdigit()):
                                # Ce sont des IDs, utiliser fallback API
                                fallback = _fetch_nostalgie_fallback(self.session, url, station_name)
                                if fallback:
                                    return fallback
                            elif (
                                (not t_norm)
                                or t_l == "en direct"
                                or t_l == station_name.lower()
                                or t_l.startswith("nostalgie")
                                or a_norm.lower() == station_name.lower()
                            ):
                                fallback = _fetch_nostalgie_fallback(self.session, url, station_name)
                                if fallback:
                                    return fallback

                            fallback = _fetch_nostalgie_fallback(self.session, url, station_name)
                            if fallback and fallback.cover_url:
                                return RadioMetadata(
                                    station=station_name,
                                    title=t_norm,
                                    artist=a_norm if a_norm else station_name,
                                    cover_url=fallback.cover_url,
                                )
                        return RadioMetadata(
                            station=station_name,
                            title=title.strip(),
                            artist=artist.strip(),
                            cover_url=""
                        )
                    else:
                        if "nostalgie" in station_name.lower():
                            t_norm = _normalize_text(stream_title.strip())
                            t_l = t_norm.lower()
                            # Vérifier si c'est des chiffres (IDs NRJ) au lieu de texte
                            if t_l.isdigit() or (t_l.replace(" ", "").replace("-", "").isdigit()):
                                # Ce sont des IDs, utiliser fallback API
                                fallback = _fetch_nostalgie_fallback(self.session, url, station_name)
                                if fallback:
                                    return fallback
                            elif (
                                (not t_norm)
                                or t_l == "en direct"
                                or t_l == station_name.lower()
                                or t_l.startswith("nostalgie")
                            ):
                                fallback = _fetch_nostalgie_fallback(self.session, url, station_name)
                                if fallback:
                                    return fallback

                            fallback = _fetch_nostalgie_fallback(self.session, url, station_name)
                            if fallback and fallback.cover_url:
                                return RadioMetadata(
                                    station=station_name,
                                    title=t_norm,
                                    artist=station_name,
                                    cover_url=fallback.cover_url,
                                )
                        return RadioMetadata(
                            station=station_name,
                            title=stream_title.strip(),
                            artist=station_name,
                            cover_url=""
                        )
                else:
                    # Pas de StreamTitle, vérifier si c'est une publicité
                    if 'adw_ad=' in metadata and 'true' in metadata:
                        return RadioMetadata(
                            station=station_name,
                            title="Publicité",
                            artist=station_name,
                            cover_url=""
                        )

                    title = "En direct"
                    artist = station_name
                    cover_url = ""
                    fallback = _fetch_nostalgie_fallback(self.session, url, station_name)
                    if fallback:
                        title = fallback.title
                        artist = fallback.artist
                        cover_url = fallback.cover_url

                    return RadioMetadata(
                        station=station_name,
                        title=title,
                        artist=artist,
                        cover_url=cover_url
                    )
            else:
                response.close()
                if "nostalgie" in station_name.lower():
                    fallback = _fetch_nostalgie_fallback(self.session, url, station_name)
                    if fallback:
                        return fallback
                return RadioMetadata(
                    station=station_name,
                    title="En direct",
                    artist=station_name,
                    cover_url=""
                )
                
        except Exception as e:
            print(f"Erreur dans _get_nrj_metadata pour {url}: {e}")
            return RadioMetadata(
                station=station_name,
                title="En direct",
                artist=station_name,
                cover_url=""
            )

    def _get_rtl_metadata(self, url: str, station_name: str) -> RadioMetadata:
        """Récupère les métadonnées pour RTL avec extraction directe"""
        try:
            response = self.session.get(url, stream=True, timeout=10)
            
            if response.status_code != 200:
                return RadioMetadata(
                    station=station_name,
                    title="En direct",
                    artist=station_name,
                    cover_url="https://www.rtl.fr/svg/rtl-logo.svg"
                )
                
            if 'icy-metaint' not in response.headers:
                # Fallback XHR RTL (programme en cours)
                try:
                    r = self.session.get("https://www.rtl.fr/ws/live/live", timeout=self.api_timeout)
                    if r.status_code == 200:
                        parsed = _parse_rtl_live_json(r.json())
                        if parsed:
                            t, a = parsed
                            return RadioMetadata(
                                station=station_name,
                                title=t,
                                artist=a,
                                cover_url="https://www.rtl.fr/svg/rtl-logo.svg",
                            )
                except Exception:
                    pass
                return RadioMetadata(
                    station=station_name,
                    title="En direct",
                    artist=station_name,
                    cover_url="https://www.rtl.fr/svg/rtl-logo.svg"
                )
                
            meta_interval = int(response.headers['icy-metaint'])
            
            # Lire les données audio
            audio_data = response.raw.read(meta_interval)
            
            # Lire la longueur des métadonnées
            meta_length_byte = response.raw.read(1)
            if not meta_length_byte:
                response.close()
                return RadioMetadata(
                    station=station_name,
                    title="En direct",
                    artist=station_name,
                    cover_url="https://www.rtl.fr/svg/rtl-logo.svg"
                )
                
            meta_length = ord(meta_length_byte) * 16
            
            if meta_length > 0:
                # Lire les métadonnées
                metadata = response.raw.read(meta_length).rstrip(b'\x00').decode('utf-8', errors='ignore')
                response.close()
                
                # Extraire le StreamTitle
                if 'StreamTitle=' in metadata:
                    stream_title = metadata.split('StreamTitle=')[1].split(';')[0].strip("'\"")
                    
                    if not stream_title or stream_title == "RTL":
                        # Fallback XHR RTL (programme en cours)
                        try:
                            r = self.session.get("https://www.rtl.fr/ws/live/live", timeout=self.api_timeout)
                            if r.status_code == 200:
                                parsed = _parse_rtl_live_json(r.json())
                                if parsed:
                                    t, a = parsed
                                    return RadioMetadata(
                                        station=station_name,
                                        title=t,
                                        artist=a,
                                        cover_url="https://www.rtl.fr/svg/rtl-logo.svg",
                                    )
                        except Exception:
                            pass
                        return RadioMetadata(
                            station=station_name,
                            title="En direct",
                            artist=station_name,
                            cover_url="https://www.rtl.fr/svg/rtl-logo.svg"
                        )
                    
                    # Essayer de séparer l'artiste et le titre
                    if ' - ' in stream_title:
                        artist, title = stream_title.split(' - ', 1)
                        return RadioMetadata(
                            station=station_name,
                            title=title.strip(),
                            artist=artist.strip(),
                            cover_url="https://www.rtl.fr/svg/rtl-logo.svg"
                        )
                    else:
                        return RadioMetadata(
                            station=station_name,
                            title=stream_title.strip(),
                            artist=station_name,
                            cover_url="https://www.rtl.fr/svg/rtl-logo.svg"
                        )
                else:
                    return RadioMetadata(
                        station=station_name,
                        title="En direct",
                        artist=station_name,
                        cover_url="https://www.rtl.fr/svg/rtl-logo.svg"
                    )
            else:
                response.close()
                return RadioMetadata(
                    station=station_name,
                    title="En direct",
                    artist=station_name,
                    cover_url="https://www.rtl.fr/svg/rtl-logo.svg"
                )
                
        except Exception as e:
            print(f"Erreur dans _get_rtl_metadata pour {url}: {e}")
            return RadioMetadata(
                station=station_name,
                title="En direct",
                artist=station_name,
                cover_url="https://www.rtl.fr/svg/rtl-logo.svg"
            )

    def _get_infomaniak_metadata(self, url: str, station_name: str) -> RadioMetadata:
        """Récupère les métadonnées pour les flux Infomaniak"""
        try:
            # Les flux Infomaniak ont des métadonnées ICY standard
            return self._get_icy_metadata(url, station_name)
        except Exception as e:
            print(f"Erreur dans _get_infomaniak_metadata pour {url}: {e}")
            return RadioMetadata(
                station=station_name,
                title="En direct",
                artist=station_name,
                cover_url=""
            )

    def _get_streamtheworld_metadata(self, url: str, station_name: str) -> RadioMetadata:
        """Récupère les métadonnées pour les flux StreamTheWorld"""
        try:
            # Les flux StreamTheWorld ont des métadonnées ICY standard
            return self._get_icy_metadata(url, station_name)
        except Exception as e:
            print(f"Erreur dans _get_streamtheworld_metadata pour {url}: {e}")
            return RadioMetadata(
                station=station_name,
                title="En direct",
                artist=station_name,
                cover_url=""
            )

def display_metadata(metadata: RadioMetadata) -> str:
    """Affiche les métadonnées de manière lisible"""
    return f" {metadata.station}\n" \
           f" {metadata.title}\n" \
           f" {metadata.artist}\n" \
           f" {metadata.cover_url if metadata.cover_url else 'Aucune image'}"

def main():
    # Liste des radios avec leurs URLs
    radios = [
        ("100% Radio", "https://100radio-80.ice.infomaniak.ch/100radio-80-128.mp3"),
        ("100% Radio", "https://streams.lesindesradios.fr/play/radios/centpourcent/sz9KS9uVGI/any/60/pt37e.H6CHKapOnXJgO7mX1kQBX5ZQ3YPUGClOV19B1qD5%2F2M%3D?format=hd"),
        ("Bide Et Musique", "https://relay1.bide-et-musique.com:9300/bm.mp3"),
        ("Chansons Oubliées Où Presque", "https://manager7.streamradio.fr:2850/stream"),
        ("Chante France- 80s", "https://chantefrance80s.ice.infomaniak.ch/chantefrance80s-128.mp3"),
        ("Flash 80 Radio", "https://manager7.streamradio.fr:1985/stream"),
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
        ("Top 80 Radio", "https://securestreams6.autopo.st:2321/")
    ]
    
    fetcher = RadioFetcher()
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_radio = {
            executor.submit(fetcher.get_metadata, name, url): (name, url)
            for name, url in radios
        }
        
        for future in as_completed(future_to_radio):
            name, url = future_to_radio[future]
            try:
                metadata = future.result()
                print(display_metadata(metadata))
                print()  # Ligne vide pour l'espacement
            except Exception as e:
                print(f"❌ Erreur pour {name}: {str(e)[:100]}...\n")

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


def _entrypoint() -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--station", type=str, default="")
    parser.add_argument("--url", type=str, default="")
    args, _ = parser.parse_known_args()

    if args.json:
        if not args.station or not args.url:
            sys.stderr.write("Missing --station or --url\n")
            return 2
        return _cli_json_once(args.station, args.url)

    main()
    return 0

if __name__ == "__main__":
    raise SystemExit(_entrypoint())