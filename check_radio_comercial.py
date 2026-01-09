#!/usr/bin/env python3
import requests
from datetime import datetime

def check_radio_comercial():
    """Vérification unique des métadonnées Radio Comercial"""
    print("🎵 Vérification Radio Comercial - " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 60)
    
    # URLs à vérifier
    urls = {
        "xml_nowplaying": "https://radiocomercial.pt/nowplaying.xml",
        "json_api": "https://bauermedia.pt/api/radiocomercial.json",
        "json_logs": f"https://radiocomercial.pt/now_playing_logs/json/radio-comercial_{datetime.now().strftime('%Y-%m-%d')}.json"
    }
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': '*/*'
    })
    
    print("\n📄 1. Vérification XML nowplaying:")
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
                    print(f"   🎵 Song: '{xml_song}'")
                    
                    # Extraire DB_DALET_ARTIST_NAME
                    if "<DB_DALET_ARTIST_NAME>" in content:
                        start_a = content.find("<DB_DALET_ARTIST_NAME>") + len("<DB_DALET_ARTIST_NAME>")
                        end_a = content.find("</DB_DALET_ARTIST_NAME>")
                        if start_a != -1 and end_a != -1:
                            artist = content[start_a:end_a].strip()
                            print(f"   🎤 Artist: '{artist}'")
                        else:
                            print(f"   🎤 Artist: '(vide)'")
                    else:
                        print(f"   🎤 Artist: '(non trouvé)'")
                    
                    # Extraire l'image de l'animateur
                    if "<IMAGE>" in content:
                        start_i = content.find("<IMAGE>") + len("<IMAGE>")
                        end_i = content.find("</IMAGE>")
                        if start_i != -1 and end_i != -1:
                            img_path = content[start_i:end_i].strip()
                            if img_path:
                                cover = f"https://radiocomercial.pt{img_path}"
                                print(f"   🖼️ Cover: '{cover}'")
                        else:
                            print(f"   🖼️ Cover: '(vide)'")
                    else:
                        print(f"   🖼️ Cover: '(non trouvé)'")
                else:
                    print("   ❌ Pas de musique détectée")
            else:
                print("   ❌ Pas de musique détectée")
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    print("\n📡 2. Vérification JSON API:")
    try:
        response = session.get(urls["json_api"], timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            # Chercher la station Radio Comercial
            for radio in data:
                if radio.get("title") and ("comercial" in radio["title"].lower() or "90" in radio["title"]):
                    print(f"   📡 Station: {radio['title']}")
                    
                    # Récupérer le now_playing
                    now_response = session.get(urls["json_logs"], timeout=5)
                    
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
                            
                            print(f"   🎵 Song: '{song}'")
                            print(f"   🎤 Artist: '{artist}'")
                            print(f"   🖼️ Album Cover: '{album_cover}'")
                        else:
                            print("   ❌ Pas de données now_playing")
                    else:
                        print(f"   ❌ Erreur now_playing: {now_response.status_code}")
                    
                    break
            else:
                print("   ❌ Station Radio Comercial non trouvée")
        else:
            print(f"   ❌ Erreur API: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    print("\n✅ Vérification terminée!")

if __name__ == "__main__":
    check_radio_comercial()
