#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from radio_metadata_fetcher_fixed_clean import RadioFetcher

def test_rfm_portugal():
    """Teste spécifiquement RFM Portugal"""
    fetcher = RadioFetcher()
    
    print("Test de RFM Portugal")
    print("===================")
    
    name = "RFM Portugal"
    url = "https://29043.live.streamtheworld.com/RFMAAC.aac?dist=triton-widget&tdsdk=js-2.9&swm=false&pname=tdwidgets&pversion=2.9&banners=300x250%2C728x90&gdpr=1&gdpr_consent=CQdTAsAQdTAsAAKA9APTCLFgAAAAAAAAAB6YAAAXsgLAA4AGaAZ8BHgCVQHbAQUAjSBIgCSgEowJkgUWAo4BVICrIFYAK5gV9AtWBbwC9gAA.IAAA.YAAAAAAAAAAA&burst-time=15"
    
    print(f"Radio: {name}")
    print(f"URL: {url}")
    print()
    
    try:
        metadata = fetcher.get_metadata(name, url)
        
        print(f"Titre: {metadata.title}")
        print(f"Artiste: {metadata.artist}")
        print(f"Cover: {metadata.cover_url}")
        print(f"Host: {metadata.host}")
        
        if "RADIOSHOW" in metadata.artist or "TOP" in metadata.artist:
            print("✅ SUCCES: RFM Portugal utilise bien l'API animateurs!")
        else:
            print("❌ PROBLEME: RFM Portugal n'utilise pas l'API animateurs")
            
    except Exception as e:
        print(f"ERREUR: {e}")

if __name__ == "__main__":
    test_rfm_portugal()
