#!/usr/bin/env python3
import requests
import ssl
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_chantefrance_metadata():
    url = "https://chantefrance80s.ice.infomaniak.ch/chantefrance80s-128.mp3"
    
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.options |= 0x4
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    session = requests.Session()
    session.verify = False
    
    headers = {
        "Icy-MetaData": "1",
        "User-Agent": "VLC/3.0.18",
        "Connection": "close",
    }
    
    try:
        print("Connexion au flux Chante France-80s...")
        r = session.get(url, stream=True, timeout=10, headers=headers)
        
        print(f"Status: {r.status_code}")
        print(f"Headers: {dict(r.headers)}")
        
        if "icy-metaint" in r.headers:
            meta_int = int(r.headers["icy-metaint"])
            print(f"Méta intervalle: {meta_int} bytes")
            
            # Lire les métadonnées
            for attempt in range(5):
                try:
                    # Sauter les données audio
                    r.raw.read(meta_int)
                    
                    # Lire la longueur des métadonnées
                    meta_len_b = r.raw.read(1)
                    if not meta_len_b:
                        print("Pas de byte de longueur de métadonnées")
                        break
                        
                    meta_len = ord(meta_len_b) * 16
                    print(f"Longueur métadonnées: {meta_len}")
                    
                    if meta_len <= 0:
                        continue
                        
                    # Lire les métadonnées
                    meta = r.raw.read(meta_len).rstrip(b"\x00").decode("utf-8", errors="ignore")
                    print(f"Métadonnées brutes: {repr(meta)}")
                    
                    if "StreamTitle=" in meta:
                        stream_title = meta.split("StreamTitle=")[1].split(";")[0].strip("'\"")
                        print(f"StreamTitle: {repr(stream_title)}")
                        
                        if stream_title and " - " in stream_title:
                            artist, title = stream_title.split(" - ", 1)
                            print(f"Artiste: {artist.strip()}")
                            print(f"Titre: {title.strip()}")
                            return True
                        elif stream_title:
                            print(f"Info: {stream_title}")
                            return True
                    
                except Exception as e:
                    print(f"Erreur tentative {attempt}: {e}")
                    break
                    
        else:
            print("Aucun en-tête icy-metaint trouvé")
            
        r.close()
        
    except Exception as e:
        print(f"Erreur générale: {e}")
        
    return False

if __name__ == "__main__":
    test_chantefrance_metadata()
