import re
import xml.etree.ElementTree as ET
from typing import Optional, Tuple

def parse_hls_metadata(hls_content: str, station_name: str) -> Optional[Tuple[str, str, str]]:
    """Parse les métadonnées XML depuis le contenu HLS"""
    try:
        # Chercher les métadonnées XML dans les segments EXTINF
        xml_pattern = r'#EXTINF:.*?(<\?xml.*?</RadioInfo>)'
        xml_matches = re.findall(xml_pattern, hls_content, re.DOTALL)
        
        if not xml_matches:
            print("Aucune balise XML trouvée dans le contenu HLS")
            return None
            
        # Prendre le premier XML trouvé
        xml_content = xml_matches[0]
        print("XML trouvé, longueur:", len(xml_content))
        
        # Parser le XML
        try:
            root = ET.fromstring(xml_content)
            
            # Extraire les informations de la table
            table = root.find('.//Table')
            if table is not None:
                song_name = table.findtext('.//DB_SONG_NAME', '').strip()
                artist_name = table.findtext('.//DB_DALET_ARTIST_NAME', '').strip()
                album_name = table.findtext('.//DB_ALBUM_NAME', '').strip()
                
                print("Données extraites du XML:")
                print(f"- Chanson: {song_name}")
                print(f"- Artiste: {artist_name}")
                print(f"- Album: {album_name}")
                
                # Extraire les informations de l'animateur
                animador = root.find('.//AnimadorInfo')
                host_name = animador.findtext('.//TITLE', '').strip() if animador is not None else ''
                show_name = animador.findtext('.//SHOW_NAME', '').strip() if animador is not None else ''
                
                print(f"- Animateur: {host_name}")
                print(f"- Émission: {show_name}")
                
                # Priorité: chanson > animateur > émission
                if song_name and artist_name:
                    title = song_name
                    artist = artist_name
                elif host_name:
                    title = show_name or host_name
                    artist = host_name
                else:
                    title = show_name or "En direct"
                    artist = station_name
                
                # URL de couverture par défaut
                cover_url = "https://radiocomercial.pt/wp-content/uploads/2020/06/cropped-rc-favicon-192x192.png"
                
                return title, artist, cover_url
                
        except ET.ParseError as e:
            print(f"Erreur de parsing XML: {e}")
            # Fallback: extraire avec des regex
            try:
                song_match = re.search(r'<DB_SONG_NAME>(.*?)</DB_SONG_NAME>', xml_content)
                artist_match = re.search(r'<DB_DALET_ARTIST_NAME>(.*?)</DB_DALET_ARTIST_NAME>', xml_content)
                host_match = re.search(r'<TITLE>(.*?)</TITLE>', xml_content)
                
                if song_match and artist_match:
                    title = song_match.group(1).strip()
                    artist = artist_match.group(1).strip()
                elif host_match:
                    title = host_match.group(1).strip()
                    artist = station_name
                else:
                    title = "En direct"
                    artist = station_name
                
                print(f"Fallback regex - Titre: {title}, Artiste: {artist}")
                return title, artist, "https://radiocomercial.pt/wp-content/uploads/2020/06/cropped-rc-favicon-192x192.png"
                
            except Exception as e2:
                print(f"Erreur lors du fallback regex: {e2}")
                
    except Exception as e:
        print(f"Erreur lors du parsing HLS: {e}")
    
    return None

# Exemple d'utilisation avec un contenu HLS simulé
def test_with_sample_data():
    # Données HLS simulées basées sur la capture
    sample_hls = """
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXT-X-MEDIA-SEQUENCE:12345
#EXTINF:10.000,
#EXT-X-PROGRAM-DATE-TIME:2025-12-20T15:30:00Z
#EXT-X-DISCONTINUITY
#EXTINF:10.000,
#EXT-X-PROGRAM-DATE-TIME:2025-12-20T15:30:10Z
#EXT-X-DISCONTINUITY
#EXTINF:10.000,
#EXT-X-PROGRAM-DATE-TIME:2025-12-20T15:30:20Z
#EXT-X-DISCONTINUITY
#EXTINF:10.000,
#EXT-X-PROGRAM-DATE-TIME:2025-12-20T15:30:30Z
#EXT-X-DISCONTINUITY
#EXTINF:10.000,
#EXT-X-PROGRAM-DATE-TIME:2025-12-20T15:30:40Z
#EXT-X-DISCONTINUITY
#EXTINF:10.000,
#EXT-X-PROGRAM-DATE-TIME:2025-12-20T15:30:50Z
#EXT-X-DISCONTINUITY
#EXTINF:10.000,
#EXT-X-PROGRAM-DATE-TIME:2025-12-20T15:31:00Z
#EXT-X-DISCONTINUITY
#EXTINF:10.000,
#EXT-X-PROGRAM-DATE-TIME:2025-12-20T15:31:10Z
#EXT-X-DISCONTINUITY
#EXTINF:10.000,
#EXT-X-PROGRAM-DATE-TIME:2025-12-20T15:31:20Z
#EXT-X-DISCONTINUITY
#EXTINF:10.000,
#EXT-X-PROGRAM-DATE-TIME:2025-12-20T15:31:30Z
#EXT-X-DISCONTINUITY
#EXTINF:10.000,
#EXT-X-PROGRAM-DATE-TIME:2025-12-20T15:31:40Z
#EXT-X-DISCONTINUITY
#EXTINF:10.000,<?xml version="1.0" encoding="utf-8"?><RadioInfo><Table><DB_SONG_NAME>Superheroes</DB_SONG_NAME><DB_DALET_ARTIST_NAME>The Script</DB_DALET_ARTIST_NAME><DB_ALBUM_NAME>No Sound Without Silence</DB_ALBUM_NAME></Table><AnimadorInfo><TITLE>Filipa Galrão</TITLE><SHOW_NAME>Filipa Galrão (13:00-16:00)</SHOW_NAME></AnimadorInfo></RadioInfo>
#EXT-X-PROGRAM-DATE-TIME:2025-12-20T15:31:50Z
#EXT-X-DISCONTINUITY
#EXTINF:10.000,
#EXT-X-PROGRAM-DATE-TIME:2025-12-20T15:32:00Z
#EXT-X-DISCONTINUITY
#EXTINF:10.000,
#EXT-X-PROGRAM-DATE-TIME:2025-12-20T15:32:10Z
#EXT-X-DISCONTINUITY
#EXTINF:10.000,
#EXT-X-PROGRAM-DATE-TIME:2025-12-20T15:32:20Z
#EXT-X-DISCONTINUITY
#EXTINF:10.000,
#EXT-X-PROGRAM-DATE-TIME:2025-12-20T15:32:30Z
#EXT-X-DISCONTINUITY
#EXTINF:10.000,
#EXT-X-PROGRAM-DATE-TIME:2025-12-20T15:32:40Z
#EXT-X-DISCONTINUITY
#EXTINF:10.000,
#EXT-X-PROGRAM-DATE-TIME:2025-12-20T15:32:50Z
#EXT-X-DISCONTINUITY
#EXTINF:10.000,
#EXT-X-PROGRAM-DATE-TIME:2025-12-20T15:33:00Z
#EXT-X-DISCONTINUITY
#EXTINF:10.000,
#EXT-X-PROGRAM-DATE-TIME:2025-12-20T15:33:10Z
#EXT-X-DISCONTINUITY
#EXTINF:10.000,
#EXT-X-PROGRAM-DATE-TIME:2025-12-20T15:33:20Z
#EXT-X-DISCONTINUITY
#EXTINF:10.000,
#EXT-X-PROGRAM-DATE-TIME:2025-12-20T15:33:30Z
#EXT-X-DISCONTINUITY
#EXTINF:10.000,
#EXT-X-PROGRAM-DATE-TIME:2025-12-20T15:33:40Z
#EXT-X-DISCONTINUITY
#EXTINF:10.000,
#EXT-X-PROGRAM-DATE-TIME:2025-12-20T15:33:50Z
#EXT-X-ENDLIST
"""
    
    print("=== TEST PARSING HLS RADIO COMERCIAL ===")
    result = parse_hls_metadata(sample_hls, "Rádio Comercial")
    
    if result:
        title, artist, cover_url = result
        print("\nRésultat du parsing HLS:")
        print(f"Titre: {title}")
        print(f"Artiste: {artist}")
        print(f"Cover: {cover_url}")
    else:
        print("Aucune métadonnée trouvée dans le flux HLS")

if __name__ == "__main__":
    test_with_sample_data()
