#!/usr/bin/env python3
"""
Script de test pour extraire les métadonnées de Bide Et Musique depuis leur site web
"""

import requests
from bs4 import BeautifulSoup
import re

def get_bide_metadata():
    """Extrait les métadonnées depuis le site de Bide Et Musique"""
    try:
        url = "https://www.bide-et-musique.com/player2/radio-info.php"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.bide-et-musique.com/player2/bideplayertest.html'
        }
        
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        
        # Parser le HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extraire le titre de la chanson
        title_element = soup.find('p', class_='titre-song')
        title = ""
        if title_element:
            title_link = title_element.find('a')
            if title_link:
                title = title_link.get_text(strip=True)
        
        # Extraire l'artiste
        artist_element = soup.find('p', class_='titre-song2')
        artist = ""
        if artist_element:
            artist_link = artist_element.find('a')
            if artist_link:
                artist = artist_link.get_text(strip=True)
        
        # Extraire l'émission/programme
        program_element = soup.find('td', id='requete')
        program = ""
        if program_element:
            program_link = program_element.find('a')
            if program_link:
                program = program_link.get_text(strip=True)
        
        # Extraire la pochette
        pochette_element = soup.find('td', id='pochette')
        pochette_url = ""
        if pochette_element:
            img_element = pochette_element.find('img')
            if img_element:
                pochette_src = img_element.get('src', '')
                if pochette_src:
                    # Convertir l'URL relative en URL absolue
                    if pochette_src.startswith('/'):
                        pochette_url = f"https://www.bide-et-musique.com{pochette_src}"
                    else:
                        pochette_url = pochette_src
        
        print(f"Titre: {title}")
        print(f"Artiste: {artist}")
        print(f"Programme: {program}")
        print(f"Pochette: {pochette_url}")
        
        return {
            'title': title,
            'artist': artist,
            'program': program,
            'cover_url': pochette_url
        }
        
    except Exception as e:
        print(f"Erreur: {e}")
        return None

if __name__ == "__main__":
    print("=== Test des métadonnées de Bide Et Musique ===")
    metadata = get_bide_metadata()
