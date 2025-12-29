import requests
import re

def get_icy_metadata(url):
    headers = {
        'Icy-MetaData': '1',
        'User-Agent': 'VLC/3.0.18'
    }
    
    try:
        with requests.get(url, headers=headers, stream=True, timeout=10) as response:
            # Vérifier si le serveur supporte les métadonnées ICY
            if 'icy-metaint' not in response.headers:
                print("Le serveur ne supporte pas les métadonnées ICY")
                print("En-têtes reçus:", dict(response.headers))
                return None
            
            # Récupérer l'intervalle des métadonnées
            meta_interval = int(response.headers['icy-metaint'])
            print(f"Intervalle des métadonnées: {meta_interval} octets")
            
            # Lire les données jusqu'à ce qu'on trouve des métadonnées
            for _ in range(5):  # Essayer 5 fois
                # Lire les données audio
                response.raw.read(meta_interval)
                
                # Lire la longueur des métadonnées
                meta_length = int.from_bytes(response.raw.read(1), byteorder='big') * 16
                if meta_length > 0:
                    # Lire les métadonnées
                    metadata = response.raw.read(meta_length).rstrip(b'\x00').decode('utf-8', errors='ignore')
                    print(f"Métadonnées brutes: {metadata}")
                    
                    # Essayer d'extraire le titre et l'artiste
                    if 'StreamTitle' in metadata:
                        stream_title = re.search(r"StreamTitle='(.*?)';", metadata)
                        if stream_title:
                            title = stream_title.group(1)
                            print(f"Trouvé: {title}")
                            return title
                else:
                    print("Aucune métadonnée trouvée dans ce bloc")
            
            print("Aucune métadonnée ICY trouvée après plusieurs tentatives")
            return None
            
    except Exception as e:
        print(f"Erreur lors de la récupération des métadonnées: {e}")
        return None

# URL du flux Mega Hits
url = "https://playerservices.streamtheworld.com/api/livestream-redirect/MEGA_HITSAAC.aac"

print(f"Tentative de récupération des métadonnées pour {url}...")
metadata = get_icy_metadata(url)

if metadata:
    print(f"Métadonnées trouvées: {metadata}")
else:
    print("Impossible de récupérer les métadonnées")
