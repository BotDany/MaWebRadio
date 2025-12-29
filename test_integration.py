#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from radio_metadata_fetcher_fixed_clean import RadioFetcher

def test_radiocomercial():
    print("=== Test Radio Comercial avec parsing HLS ===")
    
    fetcher = RadioFetcher()
    
    # Test avec l'URL standard (ICY)
    print("\n1. Test avec flux ICY standard:")
    metadata = fetcher.get_metadata("Radio Comercial", "https://stream-icy.bauermedia.pt/comercial.aac")
    print(f"   Station: {metadata.station}")
    print(f"   Titre: {metadata.title}")
    print(f"   Artiste: {metadata.artist}")
    print(f"   Cover: {metadata.cover_url}")
    
    # Test avec l'URL HLS
    print("\n2. Test avec flux HLS:")
    metadata = fetcher.get_metadata("Radio Comercial", "https://stream-hls.bauermedia.pt/comercial.aac/playlist.m3u8")
    print(f"   Station: {metadata.station}")
    print(f"   Titre: {metadata.title}")
    print(f"   Artiste: {metadata.artist}")
    print(f"   Cover: {metadata.cover_url}")

if __name__ == "__main__":
    test_radiocomercial()
