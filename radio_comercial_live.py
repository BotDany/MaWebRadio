import requests
import re
import xml.etree.ElementTree as ET
from datetime import datetime
import time

class RadioComercialHLS:
    def __init__(self):
        # URL du flux HLS de Radio Comercial
        self.url = "https://stream-hls.bauermedia.pt/comercial.aac/playlist.m3u8"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'VLC/3.0.18',
            'Accept': '*/*',
            'Connection': 'keep-alive'
        })
        self.last_metadata = {}
        
    def fetch_hls_playlist(self):
        """Récupère la playlist HLS"""
        try:
            response = self.session.get(self.url, timeout=10)
            if response.status_code == 200:
                return response.text
        except Exception as e:
            print(f"Erreur lors de la récupération de la playlist: {e}")
        return None
    
    def parse_metadata(self, content):
        """Extrait les métadonnées du contenu HLS"""
        try:
            # Chercher les balises XML dans les segments EXTINF
            xml_pattern = r'#EXTINF:.*?(<\?xml.*?</RadioInfo>)'
            xml_matches = re.findall(xml_pattern, content, re.DOTALL)
            
            if not xml_matches:
                return None
                
            # Prendre le dernier XML trouvé (le plus récent)
            xml_content = xml_matches[-1]
            
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
                
                # Vérifier si les métadonnées ont changé
                if metadata != self.last_metadata and (metadata.get('song') or metadata.get('host')):
                    self.last_metadata = metadata
                    return metadata
                    
            except ET.ParseError as e:
                print(f"Erreur de parsing XML: {e}")
                
        except Exception as e:
            print(f"Erreur lors de l'extraction des métadonnées: {e}")
            
        return None
    
    def display_metadata(self, metadata):
        """Affiche les métadonnées de manière lisible"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n=== {timestamp} ===")
        
        if metadata.get('song') and metadata.get('artist'):
            print(f"🎵 {metadata['artist']} - {metadata['song']}")
            if metadata.get('album'):
                print(f"💿 Album: {metadata['album']}")
        
        if metadata.get('host'):
            print(f"🎤 Animateur: {metadata['host']}")
            if metadata.get('show'):
                print(f"📻 Émission: {metadata['show']}")
    
    def monitor(self, interval=10):
        """Surveille les métadonnées en continu"""
        print(f"Démarrage de la surveillance du flux HLS de Radio Comercial...")
        print("Appuyez sur Ctrl+C pour arrêter\n")
        
        try:
            while True:
                content = self.fetch_hls_playlist()
                if content:
                    metadata = self.parse_metadata(content)
                    if metadata:
                        self.display_metadata(metadata)
                
                # Attendre avant la prochaine vérification
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nArrêt de la surveillance.")
        except Exception as e:
            print(f"\nErreur: {e}")

if __name__ == "__main__":
    radio = RadioComercialHLS()
    radio.monitor()
