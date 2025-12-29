import requests
from bs4 import BeautifulSoup
import re

def get_megahits_web_metadata():
    url = "https://megahits.sapo.pt/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-PT,pt;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Chercher des patterns communs pour les métadonnées
        metadata_patterns = [
            # Classes CSS communes pour les lecteurs
            {'class': 'now-playing'},
            {'class': 'current-track'},
            {'class': 'song-title'},
            {'class': 'artist-name'},
            {'class': 'track-info'},
            {'class': 'player-info'},
            {'class': 'radio-info'},
            # ID communs
            {'id': 'now-playing'},
            {'id': 'current-track'},
            {'id': 'song-title'},
            {'id': 'artist-name'},
            # Attributs data
            {'data-artist': True},
            {'data-title': True},
            {'data-track': True},
            {'data-song': True}
        ]
        
        results = {}
        
        # Chercher dans les scripts pour des données JSON
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Chercher des patterns JSON dans les scripts
                json_patterns = [
                    r'nowPlaying\s*:\s*({.*?})',
                    r'currentTrack\s*:\s*({.*?})',
                    r'playerData\s*:\s*({.*?})',
                    r'songInfo\s*:\s*({.*?})',
                    r'{"artist":.*?"title":.*?}',
                    r'{"title":.*?"artist":.*?}'
                ]
                
                for pattern in json_patterns:
                    matches = re.findall(pattern, script.string, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        try:
                            import json
                            data = json.loads(match)
                            results['json_data'] = data
                            print(f"Données JSON trouvées: {data}")
                        except:
                            pass
        
        # Chercher dans les éléments HTML
        for pattern in metadata_patterns:
            elements = soup.find_all(pattern)
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) > 3:  # Ignorer les textes trop courts
                    key = f"{'class' if 'class' in pattern else 'id' if 'id' in pattern else 'data'}"
                    value = list(pattern.values())[0] if isinstance(list(pattern.values())[0], str) else 'found'
                    results[f"{key}_{value}"] = text
                    print(f"Élément trouvé ({key}={value}): {text}")
        
        # Chercher dans les meta tags
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            if meta.get('property') and 'song' in meta.get('property', '').lower():
                results[f"meta_{meta.get('property')}"] = meta.get('content')
                print(f"Meta tag trouvé: {meta.get('property')} = {meta.get('content')}")
        
        return results
        
    except Exception as e:
        print(f"Erreur lors de l'analyse du site: {e}")
        return None

# Exécuter l'analyse
print("Analyse du site web de Mega Hits...")
metadata = get_megahits_web_metadata()

if metadata:
    print("\nRésultats trouvés:")
    for key, value in metadata.items():
        print(f"{key}: {value}")
else:
    print("\nAucune métadonnée trouvée sur le site web")
