import requests
import sys

def get_icy_metadata(url):
    headers = {
        'Icy-MetaData': '1',
        'User-Agent': 'VLC/3.0.18',
    }
    
    try:
        with requests.get(url, headers=headers, stream=True, timeout=5) as response:
            print("En-têtes de réponse:")
            for key, value in response.headers.items():
                print(f"{key}: {value}")
                
            if 'icy-metaint' in response.headers:
                print("\nMétadonnées ICY détectées!")
                meta_interval = int(response.headers['icy-metaint'])
                print(f"Intervalle des métadonnées: {meta_interval} octets")
                
                # Lire les données pour extraire les métadonnées
                for chunk in response.iter_content(chunk_size=meta_interval):
                    if len(chunk) >= meta_interval:
                        # Lire la longueur des métadonnées
                        meta_length = chunk[0] * 16
                        if meta_length > 0:
                            meta_data = chunk[1:1+meta_length].rstrip(b'\x00').decode('utf-8', errors='ignore')
                            print(f"\nMétadonnées brutes: {meta_data}")
                            
                            # Essayer d'extraire StreamTitle
                            if 'StreamTitle' in meta_data:
                                stream_title = meta_data.split('StreamTitle=')[1].split(';')[0].strip("'\"")
                                print(f"\nTitre du flux: {stream_title}")
                    break
            else:
                print("\nAucune métadonnée ICY trouvée dans les en-têtes.")
                
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://radio6.pro-fhi.net/radio/9004/stream"
    
    print(f"Vérification des métadonnées ICY pour: {url}\n")
    get_icy_metadata(url)
