import requests
from bs4 import BeautifulSoup
import re

def get_superloustic_cover():
    url = "https://www.superloustic.com/cover.html"
    
    try:
        print(f"Récupération des métadonnées depuis {url}...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        print("\nContenu de la page :")
        print("-" * 50)
        print(response.text)
        print("-" * 50)
        
        # Essayer d'extraire les informations en utilisant BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Afficher tout le contenu de la balise body
        if soup.body:
            print("\nContenu de la balise body :")
            print(soup.body.get_text(separator='\n', strip=True))
        
        # Essayer de trouver des balises img pour les pochettes
        print("\nImages trouvées sur la page :")
        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', 'pas de texte alternatif')
            print(f"- {src} (alt: {alt})")
        
        # Essayer de trouver des balises meta
        print("\nBalises meta trouvées :")
        for meta in soup.find_all('meta'):
            name = meta.get('name', meta.get('property', 'sans-nom'))
            content = meta.get('content', 'pas de contenu')
            if any(keyword in name.lower() for keyword in ['title', 'artist', 'album', 'image']):
                print(f"{name}: {content}")
        
    except Exception as e:
        print(f"Erreur : {e}")

if __name__ == "__main__":
    get_superloustic_cover()
