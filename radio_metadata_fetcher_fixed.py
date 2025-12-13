import ssl
import time
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

# Désactiver les avertissements SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

def _parse_bide_radio_info(text: str) -> Optional[Tuple[str, str]]:
    if not isinstance(text, str):
        return None
    
    # Extract from openImage onclick: openImage('/path', 'Artist - Title', width, height)
    onclick_match = re.search(r"openImage\([^,]+,\s*['\"]([^'\"]+)['\"]", text)
    if onclick_match:
        title_artist = onclick_match.group(1)
        # Replace + with space and normalize
        title_artist = title_artist.replace('+', ' ')
        title_artist = _normalize_text(title_artist)
        
        # Split by " - " to separate artist and title
        if ' - ' in title_artist:
            artist, title = title_artist.split(' - ', 1)
            artist = _normalize_text(artist.strip())
            title = _normalize_text(title.strip())
            if title and artist:
                return title, artist
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
                        return title, artist
    
    # Try to extract from HTML format with specific classes
    title_match = re.search(r'<td[^>]*class="titre"[^>]*>(.*?)</td>', text, re.IGNORECASE | re.DOTALL)
    if title_match:
        title = _normalize_text(title_match.group(1))
        # Look for artist
        artist_match = re.search(r'<td[^>]*class="artiste"[^>]*>(.*?)</td>', text, re.IGNORECASE | re.DOTALL)
        if artist_match:
            artist = _normalize_text(artist_match.group(1))
            if title and artist:
                return title, artist
    
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
            return title, artist
    
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

    def _station_matches(station: dict) -> bool:
        for k in ("url_64k_aac", "url_128k_mp3", "url_hd_aac"):
            v = station.get(k)
            if isinstance(v, str) and v and v == stream_url:
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
        r = session.get("https://www.nostalgie.fr/onair.json", timeout=10)
        if r.status_code != 200:
            return None
        parsed = _extract_nostalgie_onair_for_stream(r.json(), stream_url)
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
            # Récupération des métadonnées
            response = self.session.get(url, stream=True, timeout=self.default_timeout)
            
            # Vérification des en-têtes ICY
            if 'icy-name' in response.headers:
                station = station_name
                title = _normalize_text(response.headers.get('icy-name', 'En direct'))
                artist = _normalize_text(response.headers.get('icy-description', station_name))
                cover_url = _normalize_text(response.headers.get('icy-url', ''))

                # Si possible, lire le StreamTitle ICY (souvent plus précis)
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

                            if title and title != "En direct":
                                break
                    except Exception:
                        pass

                response.close()
                return RadioMetadata(
                    station=_normalize_text(station),
                    title=_normalize_text(title),
                    artist=_normalize_text(artist),
                    cover_url=cover_url
                )
                
            response.close()
            return RadioMetadata(
                title="En direct",
                artist=station_name
            )
            
        except Exception as e:
            print(f"Erreur StreamRadio pour {station_name}: {str(e)[:100]}...")
            return RadioMetadata(
                station=station_name,
                title="En direct",
                artist=station_name
            )

    def get_metadata(self, station_name: str, url: str) -> RadioMetadata:
        # Vérification du cache
        cache_key = f"{station_name}:{url}"
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_timeout:
                if station_name.lower() == "mega hits":
                    if not cached_data.cover_url or "sapo.pt" in cached_data.cover_url:
                        cached_data.cover_url = "https://megahits.fm/"
                return cached_data

        # Détection du type de flux
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

        if station_name.lower() == "mega hits":
            if not metadata.cover_url or "sapo.pt" in metadata.cover_url:
                metadata.cover_url = "https://megahits.fm/"

        # Mise en cache
        self.cache[cache_key] = (metadata, time.time())
        return metadata

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
                        else:
                            title = stream_title

                        if title and title != "En direct":
                            break
                except Exception:
                    pass

            response.close()

            # Fallback spécifique: Bide&Musique expose un endpoint now-playing
            if (title == "En direct" or not title) and ("bide-et-musique.com" in url or "relay1.bide-et-musique.com" in url):
                try:
                    r = self.session.get("https://www.bide-et-musique.com/radio-info.php", timeout=self.api_timeout)
                    if r.status_code == 200 and r.text:
                        parsed = _parse_bide_radio_info(r.text)
                        if parsed:
                            title, artist = parsed
                except Exception:
                    pass

            # Fallback spécifique: Bide&Musique (si ICY ne donne rien)
            if (title == "En direct" or not title or title.startswith("<table")) and ("bide" in station_name.lower()):
                try:
                    r = self.session.get("https://www.bide-et-musique.com/radio-info.php", timeout=self.api_timeout)
                    if r.status_code == 200 and r.text:
                        parsed = _parse_bide_radio_info(r.text)
                        if parsed:
                            title, artist = parsed
                except Exception:
                    pass

            # Fallback spécifique: 100% Radio (SSE)
            if title == "En direct" and ("100radio-80.ice.infomaniak.ch" in url or station_name.lower() == "100% radio"):
                try:
                    headers = {
                        "Accept": "application/json",
                        "Referer": "https://www.centpourcent.com/",
                        "User-Agent": "Mozilla/5.0",
                    }
                    r = self.session.get(
                        "https://www.centpourcent.com/ws/metas?id=3301185310276687502",
                        headers=headers,
                        stream=True,
                        timeout=(5, 5),
                    )
                    if r.status_code == 200:
                        for raw_line in r.iter_lines(decode_unicode=True):
                            if not raw_line:
                                continue
                            parsed = _parse_centpourcent_metas_sse(raw_line)
                            if parsed:
                                title, artist = parsed
                            break
                except Exception:
                    pass

            # Fallback spécifique: Mega Hits (XML UTF-16)
            if title == "En direct" and station_name.lower() == "mega hits":
                try:
                    r = self.session.get(
                        "https://configsa01.blob.core.windows.net/megahits/megaOnAir.xml",
                        timeout=self.api_timeout,
                    )
                    if r.status_code == 200 and r.content:
                        parsed = _parse_megahits_onair_xml(r.content)
                        if parsed:
                            title, artist = parsed
                except Exception:
                    pass

            # Fallback spécifique: RadioSurle (Supernana, Radio Gérard, etc.)
            if (title == "SongTitle" or title == "En direct" or not title) and "radiosurle.net" in url:
                try:
                    # Extract station key from URL (e.g., "showsupernana" from https://radiosurle.net:8765/showsupernana)
                    station_key = url.split("/")[-1].split("?")[0]
                    r = self.session.get(
                        f"https://radiosurle.net/current_station_metadata_ice.php?station={station_key}",
                        timeout=self.api_timeout,
                    )
                    if r.status_code == 200 and r.text:
                        parsed = _parse_radiosurle_metadata(r.text, station_key)
                        if parsed:
                            title, artist = parsed
                except Exception:
                    pass

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
        """Récupère les métadonnées pour les flux NRJ avec extraction directe"""
        try:
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
                    fallback = _fetch_nostalgie_onair_metadata(self.session, url, station_name)
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
                    fallback = _fetch_nostalgie_onair_metadata(self.session, url, station_name)
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
                            fallback = _fetch_nostalgie_onair_metadata(self.session, url, station_name)
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
                        if st_l.startswith("nostalgie") or st_l == station_name.lower() or st_norm == station_name:
                            fallback = _fetch_nostalgie_onair_metadata(self.session, url, station_name)
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
                    try:
                        r = self.session.get("https://www.nostalgie.fr/onair.json", timeout=10)
                        if r.status_code == 200:
                            parsed = _extract_nostalgie_onair_for_stream(r.json(), url)
                            if parsed:
                                title, artist, cover_url = parsed
                    except Exception:
                        pass

                    return RadioMetadata(
                        station=station_name,
                        title=title,
                        artist=artist,
                        cover_url=cover_url
                    )
            else:
                response.close()
                if "nostalgie" in station_name.lower():
                    fallback = _fetch_nostalgie_onair_metadata(self.session, url, station_name)
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
        md = fetcher.get_metadata(station_name, url)
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