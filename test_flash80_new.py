#!/usr/bin/env python3
import requests

def test_flash80_new_url():
    url = "https://streamapps.fr/flash80radio"
    print(f"Test de la nouvelle URL Flash 80: {url}")
    
    try:
        headers = {
            "Icy-MetaData": "1",
            "Accept": "*/*",
            "User-Agent": "VLC/3.0.18",
            "Connection": "close",
        }
        
        r = requests.get(url, stream=True, timeout=6, headers=headers)
        
        print("\n--- En-têtes de réponse ---")
        for key, value in r.headers.items():
            print(f"{key}: {value}")
        
        icy_metaint = r.headers.get("icy-metaint")
        if icy_metaint:
            print(f"\n--- Métadonnées ICY trouvées (interval: {icy_metaint}) ---")
            
            meta_int = int(icy_metaint)
            for i in range(3):
                print(f"\nEssai {i+1}:")
                r.raw.read(meta_int)
                meta_len_b = r.raw.read(1)
                if not meta_len_b:
                    print("  Pas de métadonnées reçues")
                    break
                meta_len = ord(meta_len_b) * 16
                if meta_len <= 0:
                    print("  Métadonnées de longueur 0")
                    continue
                meta = r.raw.read(meta_len).rstrip(b"\x00").decode("utf-8", errors="ignore")
                print(f"  Métadonnées brutes: {repr(meta)}")
                if "StreamTitle=" in meta:
                    stream_title = meta.split("StreamTitle=")[1].split(";")[0].strip("'\"")
                    print(f"  StreamTitle: {stream_title}")
                else:
                    print("  Pas de StreamTitle trouvé")
        else:
            print("\n--- Aucun en-tête ICY trouvé ---")
        
        r.close()
        
        # Test avec notre parser
        print("\n--- Test avec notre metadata fetcher ---")
        from radio_metadata_fetcher_fixed_clean import RadioFetcher
        fetcher = RadioFetcher()
        metadata = fetcher.get_metadata("Flash 80 Radio", url)
        print(f"Résultat: {metadata.title} - {metadata.artist}")
        
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    test_flash80_new_url()
