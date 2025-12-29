#!/usr/bin/env python3
import time
from radio_metadata_fetcher_fixed_clean import RadioFetcher

def monitor_flash80():
    fetcher = RadioFetcher()
    url = "http://manager7.streamradio.fr:1985/stream"
    
    print("Surveillance de Flash 80 Radio pendant 10 secondes...")
    print("=" * 50)
    
    for i in range(10):
        try:
            metadata = fetcher.get_metadata("Flash 80 Radio", url)
            print(f"[{i+1:02d}/10] {metadata.title} - {metadata.artist}")
            
            if metadata.title != "En direct" and metadata.artist != "Flash 80 Radio":
                print(f"  *** MÉTADONNÉES TROUVÉES! ***")
                break
        except Exception as e:
            print(f"[{i+1:02d}/10] Erreur: {e}")
        
        time.sleep(1)
    
    print("\nSurveillance terminée.")

if __name__ == "__main__":
    monitor_flash80()
