import requests
import re

try:
    response = requests.get('https://www.nostalgie.fr/', headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
    content = response.text
    
    # Chercher des URLs qui pourraient contenir des métadonnées
    patterns = [
        r'https://[^\s\"\'<>]*api[^\s\"\'<>]*',
        r'https://[^\s\"\'<>]*live[^\s\"\'<>]*',
        r'https://[^\s\"\'<>]*meta[^\s\"\'<>]*',
        r'https://[^\s\"\'<>]*now[^\s\"\'<>]*',
        r'https://[^\s\"\'<>]*player[^\s\"\'<>]*'
    ]
    
    found_urls = set()
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        found_urls.update(matches)
    
    print('Potential metadata URLs:')
    for url in found_urls:
        if any(keyword in url.lower() for keyword in ['nostalgie', 'nrj', 'api', 'live', 'meta', 'now']):
            print('  ' + url)
            
except Exception as e:
    print('Error: ' + str(e))
