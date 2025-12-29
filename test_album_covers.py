#!/usr/bin/env python3
from radio_metadata_fetcher_fixed_clean import RadioFetcher, RADIOS

def main():
    fetcher = RadioFetcher()
    
    print("=== Test des pochettes d'album ===\n")
    
    for station_name, url in RADIOS:
        print(f"\n--- {station_name} ---")
        try:
            md = fetcher.get_metadata(station_name, url)
            
            # Afficher les infos de base
            print(f"Titre: {md.title}")
            print(f"Artiste: {md.artist}")
            
            # Vérifier et afficher la pochette
            if md.cover_url:
                source = "iTunes" if "itunes" in md.cover_url.lower() else "Source intégrée"
                print(f"✅ Pochette trouvée ({source}): {md.cover_url[:80]}...")
            else:
                print("❌ Aucune pochette trouvée")
                
        except Exception as e:
            print(f"❌ Erreur: {str(e)}")

if __name__ == "__main__":
    main()
