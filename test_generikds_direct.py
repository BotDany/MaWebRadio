#!/usr/bin/env python3
"""
Test direct de l'URL Générikds pour vérifier les métadonnées
"""

import requests
from radio_metadata_fetcher_fixed_clean import RadioFetcher

def test_generikds_url():
    """Test direct de l'URL Générikds"""
    url = "https://listen.radioking.com/radio/497599/stream/554719"
    
    print("🎵 Test direct de Générikds")
    print(f"🔗 URL: {url}")
    print("=" * 60)
    
    # Test 1: Requête HTTP simple
    try:
        print("1️⃣ Test HTTP simple...")
        response = requests.get(url, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"   Content-Length: {response.headers.get('Content-Length', 'N/A')}")
        
        if response.status_code == 200:
            print("   ✅ URL accessible")
        else:
            print("   ❌ URL inaccessible")
    except Exception as e:
        print(f"   ❌ Erreur HTTP: {e}")
    
    print()
    
    # Test 2: Test avec le fetcher
    try:
        print("2️⃣ Test avec RadioFetcher...")
        fetcher = RadioFetcher()
        metadata = fetcher.get_metadata("Générikds", url)
        
        if metadata:
            print(f"   🎤 Artiste: {metadata.artist}")
            print(f"   🎶 Titre  : {metadata.title}")
            print(f"   🖼️ Cover  : {metadata.cover_url}")
            print(f"   🎙️ Host   : {metadata.host}")
        else:
            print("   🎙️ Pas de métadonnées trouvées")
    except Exception as e:
        print(f"   ❌ Erreur fetcher: {e}")
    
    print("=" * 60)
    print("🎯 Test terminé !")

if __name__ == "__main__":
    test_generikds_url()
