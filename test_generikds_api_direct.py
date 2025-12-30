#!/usr/bin/env python3
"""
Test direct de l'API RadioKing pour Générikds
"""

import requests
import json

def test_generikds_api():
    """Test direct de l'API RadioKing pour Générikds"""
    api_url = "https://api.radioking.io/widget/radio/generikids/track/current"
    
    print("🎵 Test direct de l'API RadioKing Générikds")
    print(f"🔗 API: {api_url}")
    print("=" * 60)
    
    # Test 1: Appel direct de l'API
    try:
        print("1️⃣ Test API direct...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Referer": "https://www.radioking.com/"
        }
        
        response = requests.get(api_url, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        if response.status_code == 200:
            print("   ✅ API accessible")
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # Vérifier les champs importants
            if isinstance(data, dict):
                is_live = data.get("is_live", "N/A")
                title = data.get("title", "N/A")
                artist = data.get("artist", "N/A")
                cover = data.get("cover", "N/A")
                
                print(f"   🎤 Artiste: {artist}")
                print(f"   🎶 Titre  : {title}")
                print(f"   🖼️ Cover  : {cover}")
                print(f"   🎙️ Live   : {is_live}")
                
                if is_live and title and artist:
                    print("   ✅ Métadonnées valides trouvées !")
                else:
                    print("   ⚠️ Métadonnées invalides ou manquantes")
            else:
                print("   ❌ Format de réponse invalide")
        else:
            print("   ❌ API inaccessible")
    except Exception as e:
        print(f"   ❌ Erreur API: {e}")
    
    print("=" * 60)
    print("🎯 Test API terminé !")

if __name__ == "__main__":
    test_generikds_api()
