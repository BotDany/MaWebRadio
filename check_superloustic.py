import requests
from bs4 import BeautifulSoup
import re

def get_superloustic_metadata():
    url = "https://www.superloustic.com"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"Récupération des données de {url}...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        print("Analyse du contenu...")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Essayer de trouver des éléments de lecteur audio
        print("\nRecherche d'éléments de lecteur audio...")
        players = soup.find_all(['audio', 'video', 'div', 'span'], class_=re.compile(r'(player|track|now-playing|current-track)', re.I))
        print(f"{len(players)} éléments de lecteur trouvés")
        
        # Afficher tout le contenu des balises meta
        print("\nMétadonnées de la page :")
        for meta in soup.find_all('meta'):
            if meta.get('name') or meta.get('property'):
                print(f"{meta.get('name', meta.get('property'))}: {meta.get('content')}")
        
        # Afficher le contenu des balises script qui pourraient contenir des données JSON
        print("\nRecherche de données JSON dans les scripts...")
        for script in soup.find_all('script'):
            if script.string and 'track' in script.string and 'artist' in script.string:
                print("Script potentiellement intéressant trouvé :")
                print(script.string[:500] + "...")  # Afficher les 500 premiers caractères
        
        # Afficher les iframes qui pourraient contenir un lecteur
        print("\nIframes trouvées :")
        for iframe in soup.find_all('iframe'):
            print(f"Iframe src: {iframe.get('src')}")
        
        # Afficher tout le contenu de la page pour inspection
        print("\nContenu de la page (début) :")
        print(response.text[:1000] + "...")
        
    except Exception as e:
        print(f"Erreur : {e}")

if __name__ == "__main__":
    get_superloustic_metadata()
