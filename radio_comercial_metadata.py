import socket
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import urlparse

class RadioComercialMetadata:
    def __init__(self):
        self.stream_url = "stream-icy.bauermedia.pt"
        self.stream_path = "/comercial.aac"
        self.port = 80
        self.buffer_size = 4096
        self.running = True
        
    def clean_xml(self, xml_str):
        """Nettoie la chaîne XML pour la rendre analysable"""
        # Supprimer les caractères nuls et autres caractères non imprimables
        clean = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', xml_str)
        # S'assurer qu'il n'y a qu'une seule déclaration XML
        clean = re.sub(r'<\?xml[^>]*>', '', clean, flags=re.IGNORECASE)
        clean = '<?xml version="1.0" encoding="UTF-8"?>\n' + clean.strip()
        return clean
    
    def parse_metadata(self, metadata):
        """Analyse les métadonnées XML de Radio Comercial"""
        try:
            # Nettoyer les métadonnées
            clean_metadata = self.clean_xml(metadata)
            
            # Essayer de parser le XML
            root = ET.fromstring(clean_metadata)
            result = {}
            
            # Extraire les informations de la chanson
            table = root.find('.//Table')
            if table is not None:
                result['song'] = table.findtext('.//DB_SONG_NAME', '').strip()
                result['artist'] = table.findtext('.//DB_DALET_ARTIST_NAME', '').strip()
                result['album'] = table.findtext('.//DB_ALBUM_NAME', '').strip()
                result['album_image'] = table.findtext('.//DB_ALBUM_IMAGE', '').strip()
            
            # Extraire les informations de l'émission
            animador = root.find('.//AnimadorInfo')
            if animador is not None:
                result['host'] = animador.findtext('.//TITLE', '').strip()
                result['show_name'] = animador.findtext('.//SHOW_NAME', '').strip()
                result['show_hours'] = animador.findtext('.//SHOW_HOURS', '').strip()
                result['image'] = animador.findtext('.//IMAGE', '').strip()
            
            return result if any(result.values()) else None
            
        except ET.ParseError as e:
            print(f"Erreur d'analyse XML: {e}")
            print("Données XML brutes:", metadata[:200] + "..." if len(metadata) > 200 else metadata)
            return None
        except Exception as e:
            print(f"Erreur lors de l'analyse des métadonnées: {e}")
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
            if metadata.get('show_name'):
                show_info = metadata['show_name']
                if metadata.get('show_hours'):
                    show_info += f" ({metadata['show_hours']})"
                print(f"📻 Émission: {show_info}")
        
        # Afficher les URLs des images si disponibles
        if metadata.get('image'):
            image_url = metadata['image']
            if not image_url.startswith('http'):
                image_url = f"https://radiocomercial.pt{image_url}"
            print(f"🖼️ Image: {image_url}")
            
        if metadata.get('album_image'):
            print(f"💿 Pochette: https://cdn.radios.com/pics/{metadata['album_image']}")
    
    def fetch_metadata(self):
        """Récupère les métadonnées en continu depuis le flux"""
        print(f"Connexion à {self.stream_url}...")
        
        try:
            # Créer une connexion socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30)
            sock.connect((self.stream_url, self.port))
            
            # Envoyer la requête HTTP
            request = (
                f"GET {self.stream_path} HTTP/1.0\r\n"
                f"Host: {self.stream_url}\r\n"
                "Icy-MetaData: 1\r\n"
                "User-Agent: VLC/3.0.18\r\n"
                "Accept: */*\r\n"
                "Connection: close\r\n\r\n"
            )
            sock.sendall(request.encode())
            
            # Lire l'en-tête HTTP
            header_data = b''
            while True:
                chunk = sock.recv(1)
                if not chunk:
                    break
                    
                header_data += chunk
                if header_data.endswith(b'\r\n\r\n'):
                    break
            
            # Afficher l'en-tête pour le débogage
            print("\n=== En-tête HTTP reçu ===")
            print(header_data.decode('utf-8', errors='ignore'))
            
            # Vérifier la réponse
            if b'200 OK' not in header_data:
                print("Erreur: Le serveur n'a pas répondu avec un code 200 OK")
                return
            
            # Lire les données jusqu'à trouver les métadonnées
            print("\nRecherche de métadonnées dans le flux...")
            print("Appuyez sur Ctrl+C pour arrêter\n")
            
            buffer = b''
            last_metadata = None
            
            while self.running:
                try:
                    # Lire des données du socket
                    chunk = sock.recv(self.buffer_size)
                    if not chunk:
                        print("Fin du flux")
                        break
                    
                    buffer += chunk
                    
                    # Chercher des balises XML dans le buffer
                    xml_start = buffer.find(b'<RadioInfo>')
                    if xml_start != -1:
                        xml_end = buffer.find(b'</RadioInfo>', xml_start)
                        if xml_end != -1:
                            # Extraire le XML complet
                            xml_data = buffer[xml_start:xml_end + len('</RadioInfo>')]
                            buffer = buffer[xml_end + len('</RadioInfo>'):]
                            
                            # Essayer de parser les métadonnées
                            try:
                                metadata = self.parse_metadata(xml_data.decode('utf-8', errors='ignore'))
                                if metadata and metadata != last_metadata:
                                    self.display_metadata(metadata)
                                    last_metadata = metadata
                            except Exception as e:
                                print(f"Erreur lors du traitement des métadonnées: {e}")
                    
                    # Vider le buffer s'il devient trop grand
                    if len(buffer) > 100000:  # 100KB max
                        buffer = buffer[-10000:]
                    
                except socket.timeout:
                    print("Délai d'attente dépassé, nouvelle tentative...")
                    continue
                except KeyboardInterrupt:
                    print("\nArrêt demandé par l'utilisateur.")
                    self.running = False
                    break
                except Exception as e:
                    print(f"Erreur lors de la lecture des données: {e}")
                    break
            
        except socket.error as e:
            print(f"Erreur de connexion: {e}")
        except Exception as e:
            print(f"Erreur inattendue: {e}")
        finally:
            sock.close()
            print("Connexion fermée.")

def main():
    print("=== Extracteur de métadonnées Radio Comercial ===")
    print("Ce script affiche les métadonnées en temps réel du flux audio.\n")
    
    radio = RadioComercialMetadata()
    
    try:
        radio.fetch_metadata()
    except KeyboardInterrupt:
        print("\nArrêt du programme.")
    except Exception as e:
        print(f"\nErreur: {e}")

if __name__ == "__main__":
    main()
