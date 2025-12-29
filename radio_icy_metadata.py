import socket
import re
import time
from datetime import datetime

class IcyMetadataFetcher:
    def __init__(self):
        # URL du flux audio de Radio Comercial
        self.stream_url = "stream-icy.bauermedia.pt"
        self.stream_path = "/comercial.aac"
        self.port = 80
        self.buffer_size = 4096
        self.metadata_interval = 16000  # Intervalle typique pour les métadonnées ICY
        
    def fetch_metadata(self):
        print(f"Connexion à {self.stream_url}...")
        
        try:
            # Créer une connexion socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
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
                return None
            
            # Extraire l'intervalle des métadonnées de l'en-tête ICY
            meta_interval = None
            for line in header_data.split(b'\r\n'):
                if line.lower().startswith(b'icy-metaint:'):
                    try:
                        meta_interval = int(line.split(b':')[1].strip())
                        print(f"Intervalle des métadonnées: {meta_interval} octets")
                        break
                    except (ValueError, IndexError):
                        continue
            
            if not meta_interval:
                print("Avertissement: L'en-tête ICY-MetaInt est manquant, utilisation de la valeur par défaut")
                meta_interval = self.metadata_interval
            
            # Lire les données audio et extraire les métadonnées
            print("\nÉcoute des données audio pour détecter les métadonnées...")
            print("Appuyez sur Ctrl+C pour arrêter\n")
            
            bytes_read = 0
            metadata_remaining = 0
            metadata_length = 0
            metadata = b''
            
            while True:
                # Lire les données par petits morceaux
                chunk = sock.recv(min(1024, meta_interval - bytes_read))
                if not chunk:
                    break
                
                bytes_read += len(chunk)
                
                # Vérifier si nous avons atteint la fin d'un bloc de données audio
                if bytes_read >= meta_interval:
                    # Lire la longueur des métadonnées (1 octet = longueur * 16)
                    meta_byte = sock.recv(1)
                    if not meta_byte:
                        break
                        
                    metadata_length = meta_byte[0] * 16
                    
                    if metadata_length > 0:
                        # Lire les métadonnées
                        metadata = b''
                        while len(metadata) < metadata_length:
                            chunk = sock.recv(metadata_length - len(metadata))
                            if not chunk:
                                break
                            metadata += chunk
                        
                        # Afficher les métadonnées si elles ne sont pas vides
                        if metadata and any(b > 32 for b in metadata):
                            self.display_metadata(metadata)
                    
                    bytes_read = 0
                    
        except socket.error as e:
            print(f"Erreur de connexion: {e}")
        except KeyboardInterrupt:
            print("\nArrêt de la réception des données.")
        except Exception as e:
            print(f"Erreur inattendue: {e}")
        finally:
            sock.close()
    
    def display_metadata(self, metadata_bytes):
        """Affiche les métadonnées ICY de manière lisible"""
        try:
            # Essayer de décoder en UTF-8 d'abord
            try:
                metadata_str = metadata_bytes.decode('utf-8')
            except UnicodeDecodeError:
                # Essayer avec d'autres encodages courants
                for encoding in ['latin-1', 'iso-8859-1', 'windows-1252']:
                    try:
                        metadata_str = metadata_bytes.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    print("Impossible de décoder les métadonnées avec les encodages courants")
                    return
            
            # Nettoyer et afficher les métadonnées
            metadata_str = metadata_str.strip('\x00').strip()
            if not metadata_str:
                return
                
            print(f"\n=== {datetime.now().strftime('%H:%M:%S')} ===")
            print("Métadonnées brutes:", metadata_str)
            
            # Essayer d'extraire le titre et l'artiste
            if 'StreamTitle=' in metadata_str:
                try:
                    title_part = metadata_str.split('StreamTitle=')[1].split(';')[0].strip("'\"")
                    if ' - ' in title_part:
                        artist, title = [s.strip() for s in title_part.split(' - ', 1)]
                        print(f"🎵 {artist} - {title}")
                    else:
                        print(f"📻 {title_part}")
                except Exception as e:
                    print(f"Format de métadonnées inattendu: {e}")
            else:
                print("Format de métadonnées non reconnu")
                
        except Exception as e:
            print(f"Erreur lors du traitement des métadonnées: {e}")

def main():
    print("=== Extracteur de métadonnées ICY pour Radio Comercial ===")
    print("Ce script tente de récupérer les métadonnées du flux audio en direct.\n")
    
    fetcher = IcyMetadataFetcher()
    fetcher.fetch_metadata()

if __name__ == "__main__":
    main()
