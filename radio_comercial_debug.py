import requests
import re
import xml.etree.ElementTree as ET
from datetime import datetime
import time
import json

class RadioComercialHLS:
    def __init__(self):
        # Différentes URLs possibles pour Radio Comercial
        self.urls = [
            "https://stream-hls.bauermedia.pt/comercial.aac/playlist.m3u8",
            "https://stream-icy.bauermedia.pt/comercial.aac",
            "https://stream-icy.bauermedia.pt/comercial.mp3",
            "http://mcrwowza6.mcr.iol.pt/comercial/comercial.sdp/playlist.m3u8"
        ]
        self.current_url_index = 0
        self.session = self._create_session()
        self.last_metadata = {}
    
    def _create_session(self):
        """Crée une session avec des en-têtes réalistes"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Origin': 'https://radiocomercial.pt',
            'Referer': 'https://radiocomercial.pt/',
            'Connection': 'keep-alive'
        })
        return session
    
    def get_current_url(self):
        """Retourne l'URL actuelle et passe à la suivante pour le prochain essai"""
        url = self.urls[self.current_url_index]
        self.current_url_index = (self.current_url_index + 1) % len(self.urls)
        return url
    
    def fetch_hls_playlist(self):
        """Tente de récupérer la playlist HLS avec différentes URLs"""
        for _ in range(len(self.urls)):
            url = self.get_current_url()
            print(f"\nEssai avec l'URL: {url}")
            
            try:
                response = self.session.get(url, timeout=10, stream=True)
                print(f"  Status: {response.status_code}")
                print(f"  Headers: {json.dumps(dict(response.headers), indent=2)}")
                
                if response.status_code == 200:
                    content = response.text
                    print(f"  Taille de la réponse: {len(content)} octets")
                    print(f"  Début de la réponse: {content[:200]}...")
                    
                    # Vérifier si c'est bien une playlist HLS
                    if '#EXTM3U' in content:
                        print("  Playlist HLS détectée!")
                        return content
                    else:
                        print("  La réponse ne semble pas être une playlist HLS valide")
                
            except Exception as e:
                print(f"  Erreur: {e}")
            
            time.sleep(1)  # Petit délai entre les essais
        
        return None
    
    def parse_metadata(self, content):
        """Extrait les métadonnées du contenu HLS"""
        try:
            # Chercher les balises XML dans les segments EXTINF
            xml_patterns = [
                r'#EXTINF:.*?(<\?xml.*?</RadioInfo>)',  # Format XML complet
                r'<DB_SONG_NAME>(.*?)</DB_SONG_NAME>.*?<DB_DALET_ARTIST_NAME>(.*?)</DB_DALET_ARTIST_NAME>',  # Format brut
                r'StreamTitle=["\'](.*?)["\']'  # Format ICY
            ]
            
            for pattern in xml_patterns:
                matches = re.findall(pattern, content, re.DOTALL)
                if matches:
                    print(f"Métadonnées trouvées avec le motif: {pattern[:50]}...")
                    print(f"Nombre de correspondances: {len(matches)}")
                    
                    # Afficher les premières correspondances pour le débogage
                    for i, match in enumerate(matches[:3]):
                        print(f"  Match {i+1}: {str(match)[:200]}...")
                    
                    # Essayer de parser le XML si c'est le bon format
                    if pattern.startswith('#EXTINF'):
                        return self._parse_xml_metadata(matches[-1])
                    elif pattern.startswith('<DB_SONG_NAME>'):
                        return self._parse_raw_metadata(matches[-1])
                    elif 'StreamTitle' in pattern:
                        return self._parse_icy_metadata(matches[-1])
            
            print("Aucun motif de métadonnées reconnu dans le contenu")
            return None
            
        except Exception as e:
            print(f"Erreur lors de l'extraction des métadonnées: {e}")
            return None
    
    def _parse_xml_metadata(self, xml_content):
        """Parse les métadonnées au format XML"""
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
            
            return metadata if any(metadata.values()) else None
            
        except ET.ParseError as e:
            print(f"Erreur de parsing XML: {e}")
            return None
    
    def _parse_raw_metadata(self, match):
        """Parse les métadonnées au format brut"""
        try:
            if len(match) >= 2:
                return {
                    'song': match[0].strip(),
                    'artist': match[1].strip(),
                    'source': 'raw_metadata'
                }
        except Exception as e:
            print(f"Erreur lors du parsing des métadonnées brutes: {e}")
        return None
    
    def _parse_icy_metadata(self, match):
        """Parse les métadonnées au format ICY"""
        try:
            if match and ' - ' in match:
                artist, song = match.split(' - ', 1)
                return {
                    'artist': artist.strip(),
                    'song': song.strip(),
                    'source': 'icy_metadata'
                }
        except Exception as e:
            print(f"Erreur lors du parsing des métadonnées ICY: {e}")
        return None
    
    def display_metadata(self, metadata):
        """Affiche les métadonnées de manière lisible"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n=== {timestamp} ===")
        
        if not metadata:
            print("Aucune métadonnée valide trouvée")
            return
        
        if metadata.get('song') and metadata.get('artist'):
            print(f"🎵 {metadata['artist']} - {metadata['song']}")
            if metadata.get('album'):
                print(f"💿 Album: {metadata['album']}")
        
        if metadata.get('host'):
            print(f"🎤 Animateur: {metadata['host']}")
            if metadata.get('show'):
                print(f"📻 Émission: {metadata['show']}")
        
        if metadata.get('source'):
            print(f"🔧 Source: {metadata['source']}")
    
    def monitor(self, interval=10):
        """Surveille les métadonnées en continu"""
        print("=== Démarrage de la surveillance de Radio Comercial ===")
        print("Tentative de connexion aux différents flux...\n")
        
        try:
            while True:
                print(f"\n{'='*50}")
                print(f"Nouvelle tentative à {datetime.now().strftime('%H:%M:%S')}")
                
                content = self.fetch_hls_playlist()
                if content:
                    print("\nAnalyse du contenu...")
                    metadata = self.parse_metadata(content)
                    if metadata:
                        self.display_metadata(metadata)
                    else:
                        print("Aucune métadonnée trouvée dans le contenu")
                else:
                    print("Impossible de récupérer le contenu du flux")
                
                # Attendre avant la prochaine vérification
                print(f"\nAttente de {interval} secondes avant la prochaine tentative...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nArrêt de la surveillance.")
        except Exception as e:
            print(f"\nErreur: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    radio = RadioComercialHLS()
    radio.monitor()
