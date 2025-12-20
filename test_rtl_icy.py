#!/usr/bin/env python3
"""
Script pour tester les métadonnées ICY de RTL
"""

import requests
import time

def test_rtl_icy():
    """Teste les métadonnées ICY du flux RTL"""
    try:
        url = "http://streaming.radio.rtl.fr/rtl-1-44-128"
        headers = {
            "Icy-MetaData": "1",
            "User-Agent": "VLC/3.0.18",
            "Connection": "close",
        }
        
        print(f"Test des métadonnées ICY pour RTL...")
        print(f"URL: {url}")
        
        response = requests.get(url, stream=True, timeout=10, headers=headers)
        
        # Vérifier les en-têtes ICY
        print("\n=== En-têtes de réponse ===")
        for key, value in response.headers.items():
            if 'icy' in key.lower() or key.lower() in ['content-type', 'server']:
                print(f"{key}: {value}")
        
        # Vérifier icy-metaint
        if "icy-metaint" in response.headers:
            print(f"\n=== Métadonnées ICY trouvées ===")
            meta_int = int(response.headers["icy-metaint"])
            print(f"Intervalle de métadonnées: {meta_int} octets")
            
            # Lire quelques métadonnées
            for i in range(3):
                try:
                    # Lire les données audio
                    audio_data = response.raw.read(meta_int)
                    print(f"Lu {len(audio_data)} octets audio")
                    
                    # Lire la longueur des métadonnées
                    meta_len_byte = response.raw.read(1)
                    if not meta_len_byte:
                        break
                    
                    meta_len = ord(meta_len_byte) * 16
                    print(f"Longueur métadonnées: {meta_len}")
                    
                    if meta_len > 0:
                        # Lire les métadonnées
                        meta_data = response.raw.read(meta_len).rstrip(b"\x00")
                        meta_text = meta_data.decode("utf-8", errors="ignore")
                        print(f"Métadonnées brutes: {meta_text}")
                        
                        if "StreamTitle=" in meta_text:
                            stream_title = meta_text.split("StreamTitle=")[1].split(";")[0].strip("'\"")
                            print(f"Titre du flux: '{stream_title}'")
                    
                    print("-" * 50)
                    
                except Exception as e:
                    print(f"Erreur lecture métadonnées: {e}")
                    break
        else:
            print("\n=== Pas de métadonnées ICY trouvées ===")
            print("L'en-tête 'icy-metaint' n'est pas présent")
        
        response.close()
        
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    test_rtl_icy()
