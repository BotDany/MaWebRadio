import requests
import re

def test_megahits_api():
    url = "https://playerservices.streamtheworld.com/api/livestream-redirect/MEGA_HITSAAC_SC"
    
    params = {
        "csegid": "2",
        "dist": "rmultimedia_apps",
        "lsid": "idfa:A4EC653A-076B-4270-98C9-71FFFB878883",
        "gdpr": "1",
        "gdpr_consent": "https:__megahits.sapo.pt_politica-de-privacidade",
        "bundle-id": "pt.megahits.ios",
        "store-id": "id1414420258",
        "store-url": "https://apps.apple.com/pt/app/mega-hits-mais-m%C3%BAsica-nova/id1414420258"
    }
    
    headers = {
        "X-Playback-Session-Id": "2129DA7C-E1B9-43E0-8B20-0C733A266859",
        "icy-metadata": "1",
        "Accept": "*/*",
        "User-Agent": "AppleCoreMedia/1.0.0.22F76 (iPhone; U; CPU OS 18_5 like Mac OS X; fr_fr)",
        "Accept-Language": "fr-FR,fr;q=0.9",
        "Accept-Encoding": "identity",
        "Connection": "keep-alive"
    }
    
    try:
        print("Test de l'API Mega Hits...")
        print(f"URL: {url}")
        print(f"Paramètres: {params}")
        print(f"En-têtes: {headers}")
        
        response = requests.get(url, params=params, headers=headers, stream=True, timeout=10, verify=False)
        
        print(f"\nStatut: {response.status_code}")
        print(f"En-têtes de réponse:")
        for key, value in response.headers.items():
            if 'icy-' in key.lower() or 'content-type' in key.lower() or 'location' in key.lower():
                print(f"  {key}: {value}")
        
        # Vérifier si c'est une redirection
        if response.status_code == 302:
            redirect_url = response.headers.get('location')
            print(f"\nRedirection vers: {redirect_url}")
            
            # Suivre la redirection
            if redirect_url:
                try:
                    redirect_response = requests.get(redirect_url, headers=headers, stream=True, timeout=10, verify=False)
                    print(f"Statut de la redirection: {redirect_response.status_code}")
                    
                    # Vérifier les métadonnées ICY
                    if 'icy-metaint' in redirect_response.headers:
                        meta_interval = int(redirect_response.headers['icy-metaint'])
                        print(f"Métadonnées ICY détectées (intervalle: {meta_interval} octets)")
                        
                        # Lire les données pour extraire les métadonnées
                        data = redirect_response.raw.read(meta_interval)
                        meta_length = int.from_bytes(redirect_response.raw.read(1), byteorder='big') * 16
                        if meta_length > 0:
                            metadata = redirect_response.raw.read(meta_length).rstrip(b'\x00').decode('utf-8', errors='ignore')
                            print(f"\nMétadonnées brutes: {metadata}")
                            
                            # Extraire titre et artiste
                            if 'StreamTitle' in metadata:
                                stream_title = re.search(r"StreamTitle='(.*?)';", metadata)
                                if stream_title:
                                    title = stream_title.group(1)
                                    print(f"Titre trouvé: {title}")
                                    return title
                        else:
                            print("Aucune métadonnée trouvée dans ce bloc")
                    else:
                        print("Aucune métadonnée ICY détectée dans la redirection")
                        
                except Exception as e:
                    print(f"Erreur lors de la redirection: {e}")
        else:
            print("Pas de redirection détectée")
            
            # Vérifier les métadonnées ICY directement
            if 'icy-metaint' in response.headers:
                meta_interval = int(response.headers['icy-metaint'])
                print(f"Métadonnées ICY détectées (intervalle: {meta_interval} octets)")
                
                # Essayer plusieurs blocs de métadonnées avec des pauses plus longues
                for attempt in range(10):  # Augmenter à 10 tentatives
                    print(f"\nTentative {attempt + 1}:")
                    
                    # Lire les données audio
                    data = response.raw.read(meta_interval)
                    
                    # Lire la longueur des métadonnées
                    meta_length = int.from_bytes(response.raw.read(1), byteorder='big') * 16
                    print(f"Longueur des métadonnées: {meta_length} octets")
                    
                    if meta_length > 0:
                        # Lire les métadonnées
                        metadata = response.raw.read(meta_length).rstrip(b'\x00').decode('utf-8', errors='ignore')
                        print(f"Métadonnées brutes: {metadata}")
                        
                        # Extraire titre et artiste
                        if 'StreamTitle' in metadata:
                            stream_title = re.search(r"StreamTitle='(.*?)';", metadata)
                            if stream_title:
                                title = stream_title.group(1)
                                print(f"Titre trouvé: {title}")
                                return title
                        else:
                            print("Aucun StreamTitle trouvé dans les métadonnées")
                    else:
                        print("Aucune métadonnée trouvée dans ce bloc")
                        
                    # Pause plus longue pour laisser le temps aux métadonnées d'arriver
                    import time
                    time.sleep(2.0)  # 2 secondes au lieu de 0.1
                    
            else:
                print("Aucune métadonnée ICY détectée")
            
        return None
        
    except Exception as e:
        print(f"Erreur: {e}")
        return None

# Exécuter le test
result = test_megahits_api()
if result:
    print(f"\nRésultat: {result}")
else:
    print("\nAucun résultat")
