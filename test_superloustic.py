#!/usr/bin/env python3

# Test simple de Superloustic
import requests
import re

# Test direct de Superloustic
url = 'https://radio6.pro-fhi.net/radio/9004/stream'
headers = {'Icy-MetaData': '1', 'Accept': '*/*'}

try:
    response = requests.get(url, headers=headers, timeout=5)
    if response.status_code == 200:
        meta_int = response.headers.get('icy-metaint', '')
        if meta_int:
            meta_data = meta_int.split(';')
            for meta in meta_data:
                if 'StreamTitle=' in meta:
                    stream_title = meta.split('StreamTitle=')[1].split(';')[0].strip('\"')
                    stream_title = stream_title.strip()
                    
                    if ' - ' in stream_title:
                        artist, title = stream_title.split(' - ', 1)
                    else:
                        title = stream_title
                        artist = 'Superloustic'
                    
                    print(f'Titre: {title}')
                    print(f'artiste: {artist}')
                    
                    # Test extraction pochette
                    site_response = requests.get('https://www.superloustic.com/', timeout=5)
                    if site_response.status_code == 200:
                        content = site_response.text
                        # Chercher la pochette dans le div qtmplayer__cover
                        cover_match = re.search(r'<div id=\"qtmplayer__cover\"[^>]*>.*?<img[^>]+src=\"([^\"]+)\"', content)
                        if cover_match:
                            cover_url = cover_match.group(1)
                            print(f'pochette: {cover_url}')
                        else:
                            print('pas de pochette')
                    else:
                        print('erreur site')
except Exception as e:
    print(f'erreur: {e}')