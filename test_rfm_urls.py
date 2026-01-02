#!/usr/bin/env python3
import requests

def test_rfm_urls():
    """Teste les deux URLs RFM pour voir laquelle fonctionne"""
    
    urls_to_test = [
        ("RFM Portugal 29043", "https://29043.live.streamtheworld.com/RFMAAC.aac"),
        ("RFM Portugal 25543", "https://25543.live.streamtheworld.com/RFMAAC.aac"),
    ]
    
    print("Test des URLs RFM")
    print("================")
    
    for name, url in urls_to_test:
        print(f"\n📻 {name}")
        print(f"🔗 URL: {url}")
        
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                print(f"✅ Fonctionne (Status: {response.status_code})")
                print(f"📍 Final URL: {response.url}")
            else:
                print(f"❌ Erreur (Status: {response.status_code})")
        except Exception as e:
            print(f"❌ ERREUR: {e}")

if __name__ == "__main__":
    test_rfm_urls()
