#!/usr/bin/env python3
"""
Script de test pour extraire les métadonnées de RTL depuis leur API
"""

import requests
import json

def get_rtl_api_metadata():
    """Extrait les métadonnées depuis l'API RTL"""
    try:
        url = "https://www.rtl.fr/ws/live/live"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Referer': 'https://www.rtl.fr/'
        }
        
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        
        # Parser le JSON
        data = response.json()
        
        # Extraire les métadonnées
        title = data.get('title', '')
        hosts = data.get('hosts', '')
        cover_url = data.get('cover', '')
        
        print(f"Titre: {title}")
        print(f"Animateur: {hosts}")
        print(f"Pochette: {cover_url}")
        
        return {
            'title': title,
            'artist': hosts,  # L'animateur est traité comme artiste
            'host': hosts,
            'cover_url': cover_url
        }
        
    except Exception as e:
        print(f"Erreur: {e}")
        return None

if __name__ == "__main__":
    print("=== Test des métadonnées API RTL ===")
    metadata = get_rtl_api_metadata()
