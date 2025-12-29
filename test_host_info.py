#!/usr/bin/env python3
"""
Script de test pour vérifier la gestion des animateurs
"""

from radio_metadata_fetcher_fixed_clean import RadioFetcher

def test_host_info():
    print("=== Test de la gestion des animateurs ===\n")
    
    fetcher = RadioFetcher()
    
    # Test de Mega Hits (qui devrait afficher un message informatif)
    print("--- Mega Hits ---")
    metadata = fetcher.get_metadata("Mega Hits", "https://playerservices.streamtheworld.com/api/livestream-redirect/MEGA_HITSAAC_SC?csegid=2&dist=rmultimedia_apps&gdpr=1&bundle-id=pt.megahits.ios")
    print(f"Titre: {metadata.title}")
    print(f"Artiste: {metadata.artist}")
    print(f"Animateur: {metadata.host}")
    print(f"Pochette: {metadata.cover_url}")
    print()
    
    # Test de Radio Comercial (qui peut avoir des animateurs)
    print("--- Radio Comercial ---")
    metadata = fetcher.get_metadata("Radio Comercial", "https://stream-icy.bauermedia.pt/comercial.mp3")
    print(f"Titre: {metadata.title}")
    print(f"Artiste: {metadata.artist}")
    print(f"Animateur: {metadata.host}")
    print(f"Pochette: {metadata.cover_url}")
    print()
    
    # Test d'une radio avec des chansons (pas d'animateur)
    print("--- Flash 80 Radio ---")
    metadata = fetcher.get_metadata("Flash 80 Radio", "https://manager7.streamradio.fr:1985/stream")
    print(f"Titre: {metadata.title}")
    print(f"Artiste: {metadata.artist}")
    print(f"Animateur: {metadata.host}")
    print(f"Pochette: {metadata.cover_url}")
    print()
    
    # Test de RTL (qui peut avoir des émissions en direct)
    print("--- RTL ---")
    metadata = fetcher.get_metadata("RTL", "http://streaming.radio.rtl.fr/rtl-1-44-128")
    print(f"Titre: {metadata.title}")
    print(f"Artiste: {metadata.artist}")
    print(f"Animateur: {metadata.host}")
    print(f"Pochette: {metadata.cover_url}")
    print()

if __name__ == "__main__":
    test_host_info()
