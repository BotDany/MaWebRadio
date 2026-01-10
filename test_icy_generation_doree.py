import requests
import sys

def get_icy_metadata():
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    url = "https://stream.votreradiosurlenet.eu/generationdorothee.mp3"
    headers = {'Icy-MetaData': '1', 'User-Agent': 'WinampMPEG/5.09'}
    
    try:
        with requests.get(url, headers=headers, stream=True, verify=False) as response:
            # Afficher les en-têtes de réponse
            print("En-têtes de réponse:")
            for key, value in response.headers.items():
                print(f"  {key}: {value}")
            
            # Vérifier si les métadonnées ICY sont disponibles
            meta_int = int(response.headers.get('icy-metaint', 0))
            if not meta_int:
                print("\nAucune métadonnée ICY trouvée dans les en-têtes.")
                return
            
            # Lire les données jusqu'au prochain bloc de métadonnées
            audio_data = b''
            while len(audio_data) < meta_int:
                chunk = response.raw.read(meta_int - len(audio_data))
                if not chunk:
                    print("\nFin du flux atteinte avant de trouver des métadonnées.")
                    return
                audio_data += chunk
            
            # Lire la longueur des métadonnées
            meta_length_byte = response.raw.read(1)
            if not meta_length_byte:
                print("\nImpossible de lire la longueur des métadonnées.")
                return
                
            meta_length = ord(meta_length_byte) * 16
            print(f"\nLongueur des métadonnées: {meta_length} octets")
            
            if meta_length > 0:
                # Lire les métadonnées
                metadata = response.raw.read(meta_length).decode('utf-8', errors='replace').rstrip('\x00')
                print("\nMétadonnées ICY:")
                print(metadata)
                
                # Essayer d'extraire le titre et l'artiste
                if ';' in metadata:
                    for part in metadata.split(';'):
                        part = part.strip("'")
                        if '=' in part:
                            key, value = part.split('=', 1)
                            print(f"{key}: {value}")
            else:
                print("Aucune métadonnée trouvée dans le flux.")
                
    except Exception as e:
        print(f"\nErreur lors de la récupération des métadonnées: {e}")

if __name__ == "__main__":
    print("Test de récupération des métadonnées ICY pour Génération Dorothée\n")
    get_icy_metadata()
