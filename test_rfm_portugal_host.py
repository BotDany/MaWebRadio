#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from radio_metadata_fetcher_fixed_clean import RadioFetcher

def test_rfm_portugal_host_only():
    """Teste uniquement l'API animateurs de RFM Portugal"""
    fetcher = RadioFetcher()
    
    print("Test API animateurs RFM Portugal (mode sans musique)")
    print("=================================================")
    
    name = "RFM Portugal"
    
    try:
        # Tester uniquement l'API des animateurs
        host_metadata = fetcher._get_rfm_portugal_host_metadata(name)
        
        if host_metadata:
            print(f"✅ API animateurs fonctionne!")
            print(f"Titre: {host_metadata.title}")
            print(f"Artiste: {host_metadata.artist}")
            print(f"Cover: {host_metadata.cover_url}")
            print(f"Host: {host_metadata.host}")
            print()
            print("🎙️ Quand pas de musique, RFM Portugal affichera:")
            print(f"   {host_metadata.artist} - {host_metadata.title}")
        else:
            print("❌ API animateurs ne retourne rien")
            
    except Exception as e:
        print(f"ERREUR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rfm_portugal_host_only()
