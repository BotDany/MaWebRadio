#!/usr/bin/env python3
import time
import json
import requests
from datetime import datetime

def monitor_radio_comercial():
    """Monitoring en continu des métadonnées Radio Comercial"""
    print("🎵 Monitoring Radio Comercial - Démarrage...")
    print("=" * 60)
    
    # URLs à surveiller
    urls = {
        "xml_nowplaying": "https://radiocomercial.pt/nowplaying.xml",
        "json_api": "https://bauermedia.pt/api/radiocomercial.json",
        "json_logs": "https://radiocomercial.pt/now_playing_logs/json/radio-comercial_{}.json"
    }
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': '*/*'
    })
    
    last_song = ""
    last_artist = ""
    last_cover = ""
    
    try:
        while True:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            date_str = datetime.now().strftime('%Y-%m-%d')
            
            print(f"\n🕐 {timestamp} - Vérification des métadonnées...")
            
            # 1. Vérifier le XML nowplaying
            try:
                response = session.get(urls["xml_nowplaying"], timeout=5)
                if response.status_code == 200:
                    content = response.text
                    
                    # Extraire DB_SONG_NAME
                    if "<DB_SONG_NAME>" in content:
                        start = content.find("<DB_SONG_NAME>") + len("<DB_SONG_NAME>")
                        end = content.find("</DB_SONG_NAME>")
                        if start != -1 and end != -1:
                            xml_song = content[start:end].strip()
                            print(f"📄 XML Song: '{xml_song}'")
                            
                            # Extraire DB_DALET_ARTIST_NAME
                            artist = ""
                            if "<DB_DALET_ARTIST_NAME>" in content:
                                start_a = content.find("<DB_DALET_ARTIST_NAME>") + len("<DB_DALET_ARTIST_NAME>")
                                end_a = content.find("</DB_DALET_ARTIST_NAME>")
                                if start_a != -1 and end_a != -1:
                                    artist = content[start_a:end_a].strip()
                                    print(f"📄 XML Artist: '{artist}'")
                            
                            # Extraire l'image de l'animateur
                            cover = ""
                            if "<IMAGE>" in content:
                                start_i = content.find("<IMAGE>") + len("<IMAGE>")
                                end_i = content.find("</IMAGE>")
                                if start_i != -1 and end_i != -1:
                                    img_path = content[start_i:end_i].strip()
                                    if img_path:
                                        cover = f"https://radiocomercial.pt{img_path}"
                                        print(f"📄 XML Cover: '{cover}'")
                            
                            # Vérifier s'il y a du changement
                            if xml_song != last_song or artist != last_artist or cover != last_cover:
                                print(f"🔄 CHANGEMENT DÉTECTÉ!")
                                print(f"   Avant: '{last_song}' par '{last_artist}'")
                                print(f"   Après: '{xml_song}' par '{artist}'")
                                print(f"   Pochette: {last_cover} → {cover}")
                                print("-" * 40)
                            else:
                                print(f"✅ Pas de changement")
                            
                            last_song = xml_song
                            last_artist = artist
                            last_cover = cover
                        else:
                            print("📄 XML: Pas de musique détectée")
                    else:
                        print("📄 XML: Pas de musique détectée")
                        
            except Exception as e:
                print(f"❌ Erreur requête XML: {e}")
            
            # 2. Vérifier le JSON API
            try:
                response = session.get(urls["json_api"], timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    
                    # Chercher la station Radio Comercial
                    for radio in data:
                        if radio.get("title") and ("comercial" in radio["title"].lower() or "90" in radio["title"]):
                            print(f"📡 Station trouvée: {radio['title']}")
                            
                            # Récupérer le now_playing pour cette station
                            now_playing_url = urls["json_logs"].format(date_str)
                            now_response = session.get(now_playing_url, timeout=5)
                            
                            if now_response.status_code == 200:
                                now_data = now_response.json()
                                if now_data and len(now_data) > 0:
                                    current = now_data[0]
                                    
                                    song = current.get("ENON", {}).get("SONG_NAME", "")
                                    artist = current.get("ENON", {}).get("ARTIST_NAME", "")
                                    
                                    # Vérifier les images d'album
                                    album_image = current.get("ENON", {}).get("ALBUM_IMAGE", "")
                                    if album_image:
                                        album_cover = f"https://radiocomercial.pt{album_image}"
                                    else:
                                        album_cover = ""
                                    
                                    print(f"🎵 JSON Chanson: {song}")
                                    print(f"🎤 JSON Artiste: {artist}")
                                    print(f"🖼️ JSON Pochette album: {album_cover}")
                                    
                            break
                    else:
                        print("📡 Station Radio Comercial non trouvée dans l'API")
                else:
                    print(f"📡 Erreur API JSON: {response.status_code}")
                        
            except Exception as e:
                print(f"📡 Erreur requête API: {e}")
            
            # 3. Pause de 10 secondes
            print("⏳ Pause de 10 secondes...")
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoring arrêté par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")

if __name__ == "__main__":
    monitor_radio_comercial()
