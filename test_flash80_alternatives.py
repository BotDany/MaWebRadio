#!/usr/bin/env python3
from radio_metadata_fetcher_fixed_clean import RadioFetcher

def test_flash80_alternatives():
    fetcher = RadioFetcher()
    
    # URLs alternatives à tester pour Flash 80 Radio
    alternatives = [
        "http://stream.flash80.com:8000/flash80",
        "http://flash80.ice.infomaniak.ch/flash80-128.mp3", 
        "http://streaming.flash80.com/flash80.mp3",
        "http://flash80.streamradio.fr:8000/stream",
        "http://listen.flash80.com/stream",
        "https://flash80.radiostream.fr/flash80.mp3",
        "http://stream.flash80radio.com:8000/stream",
        "https://flash80.icecast.fm/flash80",
    ]
    
    print("Test d'URLs alternatives pour Flash 80 Radio:")
    print("=" * 50)
    
    for url in alternatives:
        print(f"\nTest: {url}")
        try:
            metadata = fetcher.get_metadata("Flash 80 Radio", url)
            print(f"  Résultat: {metadata.title} - {metadata.artist}")
            if metadata.title != "En direct" or metadata.artist != "Flash 80 Radio":
                print(f"  *** URL FONCTIONNELLE TROUVÉE! ***")
                return url
        except Exception as e:
            print(f"  Erreur: {e}")
    
    print("\nAucune URL alternative fonctionnelle trouvée.")
    return None

if __name__ == "__main__":
    test_flash80_alternatives()
