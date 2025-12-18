import re
import json
import time
import requests
from dataclasses import dataclass
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Désactiver les avertissements SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def clean_text(text: str) -> str:
    """Nettoie le texte des caractères mal encodés et espaces superflus"""
    if not text:
        return ""
    
    # Décodage des entités HTML
    text = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), text)
    
    # Remplacement des caractères mal encodés
    replacements = {
        'Ã': 'à', 'Ã¢': 'â', 'Ã ': 'à', 'Ã§': 'ç', 'Ã¨': 'è', 'Ãª': 'ê', 'Ã«': 'ë',
        'Ã¬': 'ì', 'Ã­': 'í', 'Ã®': 'î', 'Ã¯': 'ï', 'Ã°': 'ð', 'Ã±': 'ñ', 'Ã²': 'ò',
        'Ã³': 'ó', 'Ã´': 'ô', 'Ã¶': 'ö', 'Ã¹': 'ù', 'Ãº': 'ú', 'Ã»': 'û', 'Ã¼': 'ü',
        'â€': '', 'â€': '"', 'â€¦': '...', 'â€"': '-', 'â€': '€', 'â€¹': '<', 'â€º': '>',
        '&quot;': '"', '&amp;': '&', '&lt;': '<', '&gt;': '>', '&apos;': "'", '&nbsp;': ' ',
        '\\u2013': '-', '\\u2014': '-', '\\u2018': "'", '\\u2019': "'", '\\u201c': '"', '\\u201d': '"'
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Supprimer les balises HTML/XML
    text = re.sub(r'<[^>]*>', '', text)
    
    # Supprimer les espaces multiples et les sauts de ligne
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Supprimer les caractères de contrôle
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    return text

@dataclass
class RadioMetadata:
    """Classe pour stocker les métadonnées d'une radio"""
    station: str
    title: str = "En direct"
    artist: str = ""
    cover_url: str = ""
    error: str = ""

class RadioFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Connection': 'keep-alive',
            'Accept-Encoding': 'gzip, deflate',
            'Cache-Control': 'no-cache'
        })
        self.cache = {}
        self.cache_timeout = 30  # secondes
        self.default_timeout = 5  # secondes par défaut
        
        # Configuration des retries - plus agressive pour les connexions instables
        retry_strategy = Retry(
            total=1,  # Réduit à 1 pour éviter les longs temps d'attente
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_maxsize=20,
            pool_connections=10
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    def get_metadata(self, station_name: str, stream_url: str) -> RadioMetadata:
        """Récupère les métadonnées pour une station de radio avec gestion des erreurs améliorée"""
        current_time = time.time()
        cache_key = f"{station_name}:{stream_url}"
        
        # Vérifier le cache
        if cache_key in self.cache:
            cached_metadata, timestamp = self.cache[cache_key]
            if current_time - timestamp < self.cache_timeout:
                return cached_metadata

        metadata = None
        try:
            # Sélectionner la méthode appropriée en fonction de l'URL
            if "nrjaudio.fm" in stream_url or "nostalgie" in station_name.lower():
                metadata = self._get_nrj_metadata(stream_url, station_name)
            elif "radioking.com" in stream_url:
                metadata = self._get_radioking_metadata(stream_url, station_name)
            elif "infomaniak.ch" in stream_url:
                metadata = self._get_infomaniak_metadata(stream_url, station_name)
            elif "streamtheworld.com" in stream_url:
                metadata = self._get_streamtheworld_metadata(stream_url, station_name)
            elif "radiosurle.net" in stream_url or "votreradiosurlenet" in stream_url:
                metadata = self._get_radiosurlenet_metadata(stream_url, station_name)
            elif "bauermedia.pt" in stream_url or "Radio Comercial" in station_name:
                metadata = self._get_rtp_metadata(stream_url, station_name)
            else:
                metadata = self._get_icy_metadata(stream_url, station_name)

            # Si on a des métadonnées valides, les mettre en cache
            if metadata and (metadata.title != "En direct" or metadata.artist):
                self.cache[cache_key] = (metadata, current_time)
                return metadata

        except requests.exceptions.RequestException as e:
            print(f"Erreur réseau pour {station_name}: {str(e)[:100]}...")
        except Exception as e:
            print(f"Erreur inattendue pour {station_name}: {str(e)[:100]}...")

        # En cas d'échec, essayer de récupérer les métadonnées ICY
        if not metadata or metadata.title == "En direct":
            try:
                metadata = self._get_icy_metadata(stream_url, station_name)
                if metadata and metadata.title != "En direct":
                    self.cache[cache_key] = (metadata, current_time)
                    return metadata
            except Exception:
                pass

        # Dernier recours : retourner des métadonnées par défaut
        return RadioMetadata(
            station=station_name,
            title="En direct",
            artist=station_name,
            error="Impossible de récupérer les métadonnées"
        )

    def _get_icy_metadata(self, url: str, station_name: str) -> Optional[RadioMetadata]:
        """Récupère les métadonnées ICY avec une meilleure détection et gestion des erreurs"""
        try:
            response = self.session.get(
                url,
                headers={
                    'Icy-MetaData': '1',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': '*/*',
                    'Connection': 'keep-alive',
                    'Icy-MetaData': '1'
                },
                stream=True,
                timeout=self.default_timeout,
            )
            
            # Vérifier si le flux supporte les métadonnées ICY
            if 'icy-metaint' not in response.headers:
                return None
                
            metadata = {
                'name': clean_text(response.headers.get('icy-name', '')),
                'description': clean_text(response.headers.get('icy-description', '')),
                'genre': response.headers.get('icy-genre', ''),
                'url': response.headers.get('icy-url', ''),
                'logo': response.headers.get('icy-logo', ''),
                'bitrate': response.headers.get('icy-br', '')
            }
            
            # Lire les métadonnées ICY
            meta_interval = int(response.headers['icy-metaint'])
            if meta_interval > 0:
                try:
                    # Lire les données jusqu'à atteindre les métadonnées
                    for _ in range(0, meta_interval, 4096):
                        chunk = next(response.iter_content(min(4096, meta_interval - _)))
                        if not chunk:
                            break
                    
                    # Lire la longueur des métadonnées
                    meta_length_byte = next(response.iter_content(1))
                    if not meta_length_byte:
                        return None
                        
                    meta_length = ord(meta_length_byte) * 16
                    if meta_length > 0:
                        meta_data = next(response.iter_content(meta_length)).decode('utf-8', errors='ignore')
                        if 'StreamTitle' in meta_data:
                            stream_title = meta_data.split('StreamTitle=')[1].split(';')[0].strip("'\"")
                            if stream_title and stream_title.strip():
                                metadata['stream_title'] = clean_text(stream_title)
                except Exception as e:
                    print(f"Erreur lecture métadonnées ICY: {str(e)[:100]}...")
                    return None
            
            # Nettoyer et formater les métadonnées
            title = metadata.get('stream_title', '')
            artist = None
            
            # Essayer de séparer l'artiste et le titre
            if ' - ' in title:
                artist, title = [s.strip() for s in title.split(' - ', 1)]
            
            # Nettoyer le titre et l'artiste
            title = clean_text(title) if title else "En direct"
            artist = clean_text(artist) if artist else metadata.get('description', 'Inconnu')
            
            # Éviter les boucles de métadonnées
            if title == artist:
                artist = metadata.get('name', 'Inconnu')
            
            return RadioMetadata(
                station=metadata.get('name', station_name),
                title=title,
                artist=artist,
                cover_url=metadata.get('logo')
            )
            
        except Exception as e:
            print(f"Erreur ICY pour {station_name}: {str(e)[:100]}...")
            return None

    def _get_nrj_metadata(self, url: str, station_name: str) -> RadioMetadata:
        """Métadonnées pour les radios NRJ avec gestion améliorée des erreurs"""
        metadata = None
        
        # 1. Essayer d'abord les métadonnées ICY
        try:
            metadata = self._get_icy_metadata(url, station_name)
            if metadata and metadata.title != "En direct" and "unspecified" not in metadata.title.lower():
                return metadata
        except Exception as e:
            print(f"Erreur ICY pour {station_name}: {str(e)[:100]}...")

        # 2. Essayer l'API NRJ avec un timeout court (désactivé pour éviter les erreurs)
        # L'API NRJ semble actuellement inaccessible, on se base uniquement sur ICY

        # 3. Si on a des métadonnées ICY mais que l'API a échoué, les utiliser
        if metadata:
            return metadata

        # Dernier recours : informations par défaut
        # 4. Dernier recours : informations par défaut
        return RadioMetadata(
            station=station_name,
            title="En direct",
            artist="Nostalgie"
        )

    def _get_rtp_metadata(self, url: str, station_name: str) -> RadioMetadata:
        """Métadonnées pour les radios RTP (Radio Comercial)"""
        try:
            # Essayer d'abord l'API officielle
            try:
                response = self.session.get(
                    "https://www.radiocomercial.pt/api/nowplaying/1",
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'application/json',
                        'Referer': 'https://www.radiocomercial.pt/'
                    },
                    timeout=self.default_timeout,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'now_playing' in data and 'song' in data['now_playing']:
                        song = data['now_playing']['song']
                        title = clean_text(song.get('title', ''))
                        artist = clean_text(song.get('artist', {}).get('name', ''))
                        cover_url = song.get('artwork_url', '')
                        
                        # Nettoyer l'URL de la pochette si elle contient des métadonnées
                        if cover_url and 'jpg' in cover_url:
                            cover_url = cover_url.split('jpg')[0] + 'jpg'
                        
                        return RadioMetadata(
                            station=station_name,
                            title=title,
                            artist=artist,
                            cover_url=cover_url
                        )
            except Exception as e:
                print(f"Erreur API Radio Comercial: {str(e)[:100]}...")
            
            # Si l'API échoue, essayer de récupérer les métadonnées ICY
            metadata = self._get_icy_metadata(url, station_name)
            if metadata and metadata.title != "En direct":
                # Nettoyer le titre et l'artiste
                title = clean_text(metadata.title)
                artist = clean_text(metadata.artist)
                
                # Supprimer les numéros et caractères spéciaux
                title = re.sub(r'\d+', '', title).strip()
                artist = re.sub(r'\d+', '', artist).strip()
                
                # Supprimer les parties non désirées
                for unwanted in ['.jpg', '.png', 'Rádio Comercial', 'Album']:
                    title = title.replace(unwanted, '')
                    artist = artist.replace(unwanted, '')
                
                return RadioMetadata(
                    station=station_name,
                    title=title or "En direct",
                    artist=artist or "Radio Comercial",
                    cover_url=metadata.cover_url
                )
                
            # Dernier recours : informations par défaut
            return RadioMetadata(
                station=station_name,
                title="En direct",
                artist="Radio Comercial"
            )
                
        except Exception as e:
            print(f"Erreur RTP pour {station_name}: {str(e)[:100]}...")
            return RadioMetadata(
                station=station_name,
                title="En direct",
                artist="Radio Comercial"
            )

    def _get_radioking_metadata(self, url: str, station_name: str) -> RadioMetadata:
        """Métadonnées pour les flux RadioKing (Générikds, Made In 80)"""
        try:
            # Essayer d'abord les métadonnées ICY
            metadata = self._get_icy_metadata(url, station_name)
            if metadata and metadata.title != "En direct":
                return metadata

            # Essayer l'API RadioKing
            try:
                # Extraire l'ID de la radio depuis l'URL
                radio_id = url.split('/')[-1] if '/' in url else url
                api_url = f"https://api.radioking.io/widget/radio/{radio_id}/track/current"
                
                response = self.session.get(
                    api_url,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'application/json'
                    },
                    timeout=self.default_timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'title' in data:
                        artist_name = ""
                        # Gérer le cas où artist peut être un string ou un dict
                        artist_data = data.get('artist', '')
                        if isinstance(artist_data, dict):
                            artist_name = artist_data.get('name', '')
                        elif isinstance(artist_data, str):
                            artist_name = artist_data
                        
                        return RadioMetadata(
                            station=station_name,
                            title=clean_text(data.get('title', '')),
                            artist=clean_text(artist_name),
                            cover_url=data.get('cover', {}).get('url', '') if isinstance(data.get('cover'), dict) else ''
                        )
            except Exception as e:
                print(f"Erreur API RadioKing pour {station_name}: {str(e)[:100]}...")
                
        except Exception as e:
            print(f"Erreur RadioKing pour {station_name}: {str(e)[:100]}...")
        
        return self._get_icy_metadata(url, station_name) or RadioMetadata(
            station=station_name,
            title="En direct",
            artist=station_name
        )

    def _get_infomaniak_metadata(self, url: str, station_name: str) -> RadioMetadata:
        """Métadonnées pour les flux Infomaniak (100% Radio, Chante France-80s)"""
        try:
            # Essayer d'abord les métadonnées ICY
            metadata = self._get_icy_metadata(url, station_name)
            if metadata and metadata.title != "En direct":
                return metadata
            )
            
            # Vérifier si le flux supporte les métadonnées ICY
            if 'icy-metaint' in response.headers:
                metadata = {
                    'name': clean_text(response.headers.get('icy-name', station_name)),
                    'description': clean_text(response.headers.get('icy-description', '')),
                }
                response = self.session.get(
                    url,
                    headers={
                        'Icy-MetaData': '1',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': '*/*',
                        'Connection': 'close'
                    },
                    stream=True,
                    timeout=short_timeout
                )
                
                # Vérifier si le flux supporte les métadonnées ICY
                if 'icy-metaint' in response.headers:
                    metadata = {
                        'name': clean_text(response.headers.get('icy-name', station_name)),
                        'description': clean_text(response.headers.get('icy-description', '')),
                    }
                    
                    # Lire les métadonnées ICY rapidement
                    meta_interval = int(response.headers['icy-metaint'])
                    if meta_interval > 0 and meta_interval < 32768:  # Protection contre les valeurs invalides
                        try:
                            # Lire seulement une petite partie pour éviter les blocages
                            response.iter_content(min(8192, meta_interval))
                            
                            meta_length_byte = next(response.iter_content(1))
                            if meta_length_byte:
                                meta_length = ord(meta_length_byte) * 16
                                if 0 < meta_length < 1024:  # Protection contre les métadonnées trop grandes
                                    meta_data = next(response.iter_content(meta_length)).decode('utf-8', errors='ignore')
                                    if 'StreamTitle' in meta_data:
                                        stream_title = meta_data.split('StreamTitle=')[1].split(';')[0].strip("'\"")
                                        if stream_title and len(stream_title) > 3:
                                            metadata['stream_title'] = clean_text(stream_title)
                                            
                                            # Nettoyer et formater
                                            title = metadata.get('stream_title', '')
                                            artist = None
                                            if ' - ' in title:
                                                artist, title = [s.strip() for s in title.split(' - ', 1)]
                                            
                                            title = clean_text(title) if title else "En direct"
                                            artist = clean_text(artist) if artist else metadata.get('name', station_name)
                                            
                                            if title == artist:
                                                artist = metadata.get('name', station_name)
                                            
                                            return RadioMetadata(
                                                station=metadata.get('name', station_name),
                                                title=title,
                                                artist=artist
                                            )
                        except Exception:
                            pass
                            
            except Exception:
                # Si ICY échoue, retourner immédiatement sans retry
                pass
                
            # Pour StreamTheWorld, se baser sur le nom de la station si ICY échoue
            return RadioMetadata(
                station=station_name,
                title="En direct",
                artist=station_name
            )
                
        except Exception as e:
            # Ne pas afficher les erreurs de connexion pour StreamTheWorld
            # car elles sont trop fréquentes
            return RadioMetadata(
                station=station_name,
                title="En direct",
                artist=station_name
            )

    def _get_radiosurlenet_metadata(self, url: str, station_name: str) -> RadioMetadata:
        """Métadonnées pour les flux RadioSurLeNet (Radio Gérard, Supernana)"""
        try:
            # Essayer d'abord les métadonnées ICY
            metadata = self._get_icy_metadata(url, station_name)
            if metadata and metadata.title != "En direct":
                return metadata
                
            # Pour RadioSurLeNet, on se base principalement sur ICY
            return metadata or RadioMetadata(
                station=station_name,
                title="En direct",
                artist=station_name
            )
        except Exception as e:
            print(f"Erreur RadioSurLeNet pour {station_name}: {str(e)[:100]}...")
            return self._get_icy_metadata(url, station_name) or RadioMetadata(
                station=station_name,
                title="En direct",
                artist=station_name
            )

def display_metadata(metadata: RadioMetadata) -> str:
    """Affiche les métadonnées de manière lisible"""
    if metadata.error:
        return f"❌ {metadata.station} - Erreur: {metadata.error}"
    
    output = f"🎵 {metadata.station}\n"
    
    # Nettoyer le titre pour supprimer les balises XML/HTML
    title = clean_text(metadata.title) if metadata.title else ""
    artist = clean_text(metadata.artist) if metadata.artist else ""
    
    # Supprimer les mentions de la station dans l'artiste ou le titre
    if metadata.station.lower() in artist.lower():
        artist = ""
    if metadata.station.lower() in title.lower() and not artist:
        title = title.replace(metadata.station, "").strip(" -")
    
    # Formater la sortie
    if artist and artist != "Inconnu":
        output += f"   {artist}"
        if title and title != "En direct":
            output += f" - {title}"
    elif title:
        output += f"   {title}"
    else:
        output += "   En direct"
    
    # Ajouter l'URL de la pochette si disponible
    if metadata.cover_url and not metadata.cover_url.startswith(('<?xml', '<!DOCTYPE')):
        output += f"\n   📻 {metadata.cover_url}"
    
    return output

def main():
    """Fonction principale"""
    print("\n🔍 Récupération des métadonnées en cours...\n")
    
    # Liste des radios avec leurs noms et URLs
    radios = [
        ("100% Radio", "https://100radio-80.ice.infomaniak.ch/100radio-80-128.mp3"),
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
        ("Top 80 Radio", "https://securestreams6.autopo.st:2321/")
    ]
    
    fetcher = RadioFetcher()
    
    with ThreadPoolExecutor(max_workers=10) as executor:  # Augmenté à 10 workers
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

if __name__ == "__main__":
    main()