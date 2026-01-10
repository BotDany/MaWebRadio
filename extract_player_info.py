from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

def get_player_info():
    # Configuration de Chrome en mode headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--log-level=3")  # Réduire les logs
    
    # Utilisation de webdriver-manager pour gérer automatiquement le pilote Chrome
    service = Service(ChromeDriverManager().install())
    
    try:
        # Démarrer le navigateur
        print("Démarrage du navigateur...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Accéder à la page
        url = "https://www.superloustic.com"
        print(f"Chargement de la page {url}...")
        driver.get(url)
        
        # Attendre que la page soit chargée
        time.sleep(5)  # Attendre que le lecteur se charge
        
        print("\nRecherche des informations du lecteur...")
        
        # Essayer de trouver des éléments de lecteur audio
        print("\nÉléments audio trouvés :")
        audio_elements = driver.find_elements(By.TAG_NAME, 'audio')
        print(f"Nombre d'éléments audio trouvés : {len(audio_elements)}")
        
        # Afficher les sources audio
        for i, audio in enumerate(audio_elements, 1):
            print(f"\nLecteur audio {i}:")
            print(f"Source: {audio.get_attribute('src')}")
            print(f"Titre: {audio.get_attribute('title')}")
            print(f"Artiste: {audio.get_attribute('artist')}")
        
        # Chercher des éléments qui pourraient contenir les métadonnées
        print("\nRecherche d'éléments de métadonnées...")
        
        # Essayer de trouver des éléments avec des classes courantes pour les métadonnées
        metadata_selectors = [
            '.now-playing', '.current-track', '.track-info',
            '.player-title', '.player-artist', '.player-now-playing'
        ]
        
        for selector in metadata_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"\nÉléments trouvés avec le sélecteur '{selector}':")
                for el in elements:
                    print(f"- {el.text}")
        
        # Prendre une capture d'écran pour débogage
        print("\nCapture d'écran de la page...")
        driver.save_screenshot('superloustic_screenshot.png')
        print("Capture d'écran enregistrée sous 'superloustic_screenshot.png'")
        
    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        # Fermer le navigateur
        if 'driver' in locals():
            driver.quit()
            print("\nNavigateur fermé.")

if __name__ == "__main__":
    get_player_info()
