#!/usr/bin/env python3
"""
Script de test pour extraire les métadonnées de RTL depuis leur site web
"""

import requests
from bs4 import BeautifulSoup
import re
import json

def get_rtl_metadata():
    """Extrait les métadonnées depuis le site de RTL"""
    try:
        url = "https://www.rtl.fr"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        
        # Parser le HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extraire les métadonnées depuis les éléments data-player-*
        title = ""
        artist = ""
        host = ""
        
        # Titre depuis data-player-title
        title_elements = soup.find_all(attrs={"data-player-title": True})
        for elem in title_elements:
            text = elem.get_text(strip=True)
            if text and len(text) > 2:
                print(f"Titre trouvé (data-player-title): {text}")
                if not title:
                    title = text
        
        # Artiste depuis data-player-artist
        artist_elements = soup.find_all(attrs={"data-player-artist": True})
        for elem in artist_elements:
            text = elem.get_text(strip=True)
            if text and len(text) > 2:
                print(f"Artiste trouvé (data-player-artist): {text}")
                if not artist:
                    artist = text
        
        # Animateur depuis data-player-hosts
        host_elements = soup.find_all(attrs={"data-player-hosts": True})
        for elem in host_elements:
            text = elem.get_text(strip=True)
            if text and len(text) > 2:
                print(f"Animateur trouvé (data-player-hosts): {text}")
                if not host:
                    host = text
        
        # Si pas de titre trouvé, essayer de trouver une émission en transplant
        if not title:
            emission_elements = soup.find_all(['h1', 'h2', 'h3'], string=re.compile(r'.*émission.*|.*direct.*', re.I))
            for elem in emission_elements:
                text = elem.get_text(strip=True)
                if text and len(text) > 3:
                    print(f"Émission trouvée: {text}")
                    if not title:
                        title = text
        
        print(f"Titre: {title}")
        print(f"Artiste: {artist}")
        print(f"Animateur: {host}")
        
        return {
            'title': title,
            'artist': artist,
            'host': host
        }
        
    except Exception as e:
        print(f"Erreur: {e}")
        return None

if __name__ == "__main__":
    print("=== Test des métadonnées de RTL ===")
    metadata = get_rtl_metadata()
