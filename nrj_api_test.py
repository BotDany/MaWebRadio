#!/usr/bin/env python3
import requests
import re
import json

def test_nrj_api_variations():
    """Tester différentes variations de l'API NRJ"""
    base_urls = [
        'https://players.nrjaudio.fm/wr_api/live/fr/',
        'https://players.nrjaudio.fm/wr_api/live/de/',
        'https://players.nrjaudio.fr/wr_api/live/fr/',
        'https://api.nrjaudio.fm/wr_api/live/fr/',
        'https://nrjaudio.fm/api/live/',
        'https://www.nostalgie.fr/api/live/',
        'https://www.nostalgie.fr/player/api/'
    ]
    
    params_variations = [
        {'q': 'getMetaData', 'id': '1640'},
        {'q': 'getMetaData', 'id': '1640', 'format': 'json'},
        {'q': 'getMetaData', 'id': '1640', 'callback': 'jsonp'},
        {'method': 'getMetaData', 'id': '1640'},
        {'action': 'metadata', 'id': '1640'},
        {'q': 'getMetaData', 'radio_id': '1640'},
        {'q': 'getMetaData', 'station_id': '1640'},
        {'id': '1640', 'type': 'metadata'},
        {'station': '1640', 'action': 'now'}
    ]
    
    headers_variations = [
        {'User-Agent': 'Mozilla/5.0'},
        {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
        {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.nostalgie.fr/'},
        {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.nostalgie.fr/', 'Origin': 'https://www.nostalgie.fr'},
        {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/xml, text/xml, */*'},
        {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json, text/plain, */*'}
    ]
    
    for base_url in base_urls:
        for params in params_variations:
            for headers in headers_variations:
                try:
                    response = requests.get(base_url, params=params, headers=headers, timeout=5)
                    if response.content and len(response.content) > 0:
                        print(f"SUCCESS!")
                        print(f"URL: {base_url}")
                        print(f"Params: {params}")
                        print(f"Headers: {headers}")
                        print(f"Content: {response.content[:200]}")
                        return True
                except Exception as e:
                    continue
    
    return False

def analyze_nostalgie_website():
    """Analyser le site Nostalgie pour trouver des sources de métadonnées"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get('https://www.nostalgie.fr/', headers=headers, timeout=10)
        content = response.text
        
        # Chercher des URLs d'API
        api_patterns = [
            r'https://[^\s\"\'<>]*api[^\s\"\'<>]*',
            r'https://[^\s\"\'<>]*live[^\s\"\'<>]*',
            r'https://[^\s\"\'<>]*meta[^\s\"\'<>]*',
            r'https://[^\s\"\'<>]*now[^\s\"\'<>]*',
            r'https://[^\s\"\'<>]*player[^\s\"\'<>]*'
        ]
        
        found_urls = set()
        for pattern in api_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            found_urls.update(matches)
        
        print("Found URLs:")
        for url in found_urls:
            if 'nostalgie' in url.lower() or 'nrj' in url.lower():
                print(f"  {url}")
        
        # Chercher des données JavaScript
        js_patterns = [
            r'nowPlaying[^}]*}',
            r'currentSong[^}]*}',
            r'liveData[^}]*}',
            r'metadata[^}]*}'
        ]
        
        for pattern in js_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                print(f"Found JS data: {matches[0]}")
        
        return found_urls
    except Exception as e:
        print(f"Error analyzing website: {e}")
        return set()

def test_websocket_connections():
    """Tester des connexions WebSocket possibles"""
    import websocket
    import json
    
    possible_ws_urls = [
        'wss://players.nrjaudio.fm/ws',
        'wss://www.nostalgie.fr/ws',
        'wss://api.nostalgie.fr/ws'
    ]
    
    for ws_url in possible_ws_urls:
        try:
            ws = websocket.create_connection(ws_url, timeout=5)
            print(f"WebSocket connected: {ws_url}")
            ws.close()
            return True
        except Exception as e:
            continue
    
    return False

if __name__ == "__main__":
    print("=== Testing NRJ API variations ===")
    if test_nrj_api_variations():
        print("Found working NRJ API!")
    else:
        print("No working NRJ API found")
    
    print("\n=== Analyzing Nostalgie website ===")
    analyze_nostalgie_website()
    
    print("\n=== Testing WebSocket connections ===")
    test_websocket_connections()
