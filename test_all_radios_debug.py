#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from radio_metadata_fetcher_fixed_clean import RadioFetcher, RADIOS

def test_all_radios():
    """Teste toutes les radios et affiche les métadonnées"""
    fetcher = RadioFetcher()
    
    print("🎵 Test de toutes les radios")
    print("=" * 80)
    
    for name, url in RADIOS:
        print(f"\n📻 {name}")
        print(f"🔗 URL: {url}")
        
        try:
            metadata = fetcher.get_metadata(name, url)
            
            print(f"🎵 Titre: {metadata.title}")
            print(f"🎤 Artiste: {metadata.artist}")
            print(f"🖼️  Cover: {metadata.cover_url}")
            print(f"🎙️  Host: {metadata.host}")
            
            # Vérifier si c'est RFM Portugal
            if "rfm" in name.lower() and "portugal" in name.lower():
                print("🔍 DÉTECTION RFM PORTUGAL ✅")
                if metadata.artist == "En direct" and metadata.title == "En direct":
                    print("❌ PROBLÈME: Affiche générique au lieu de l'API")
                elif "RADIOSHOW" in metadata.artist or "TOP" in metadata.artist:
                    print("✅ OK: Utilise bien l'API animateurs")
            
        except Exception as e:
            print(f"❌ ERREUR: {e}")
        
        print("-" * 60)

if __name__ == "__main__":
    test_all_radios()
