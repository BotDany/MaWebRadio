#!/usr/bin/env python3
import requests
import sys

def debug_icy_headers(url, station_name):
    print(f"\n=== Analyse de {station_name} ===")
    print(f"URL: {url}")
    
    try:
        headers = {
            "Icy-MetaData": "1",
            "Accept": "*/*",
            "User-Agent": "VLC/3.0.18",
            "Connection": "close",
        }
        
        # Headers spécifiques pour Infomaniak
        if "ice.infomaniak.ch" in url:
            headers.update({
                "User-Agent": "AIM",
                "Referer": "apli",
                "Accept-Encoding": "identity",
                "Accept-Language": "fr-FR,fr;q=0.9",
                "Connection": "keep-alive",
                "icy-metadata": "1",
            })
        
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
            print("Cette radio n'envoie probablement pas de métadonnées ICY")
        
        r.close()
        
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    # Tester les radios qui affichent "En direct"
    stations = [
        ("RTL", "http://streaming.radio.rtl.fr/rtl-1-44-128"),
        ("Bide Et Musique", "https://relay1.bide-et-musique.com:9300/bm.mp3"),
        ("Flash 80 Radio", "http://manager7.streamradio.fr:1985/stream"),
        ("Mega Hits", "https://playerservices.streamtheworld.com/api/livestream-redirect/MEGA_HITSAAC.aac"),
    ]
    
    for name, url in stations:
        debug_icy_headers(url, name)
