import requests
from urllib.parse import quote
from typing import Optional

def _fetch_album_cover_itunes(artist: str, title: str) -> Optional[str]:
    """Récupère la pochette d'album via l'API iTunes/Apple Music"""
    if not artist or not title:
        return None
    
    try:
        # Nettoyer les termes de recherche
        artist_clean = quote(artist.strip())
        title_clean = quote(title.strip())
        
        # Construire l'URL de recherche iTunes
        search_url = f"https://itunes.apple.com/search?term={artist_clean}+{title_clean}&media=music&entity=song&limit=5"
        
        response = requests.get(search_url, timeout=10)
        if response.status_code != 200:
            return None
            
        data = response.json()
        
        if data.get('resultCount', 0) > 0:
            results = data.get('results', [])
            for result in results:
                # Chercher une correspondance exacte ou proche
                result_artist = result.get('artistName', '').lower()
                result_title = result.get('trackName', '').lower()
                search_artist = artist.lower()
                search_title = title.lower()
                
                # Vérifier si l'artiste et le titre correspondent
                if (search_artist in result_artist or result_artist in search_artist) and \
                   (search_title in result_title or result_title in search_title):
                    
                    # Retourner l'artwork (pochette d'album) avec la meilleure qualité disponible
                    artwork_url = result.get('artworkUrl100')
                    if artwork_url:
                        # Convertir vers une meilleure résolution si possible
                        artwork_url = artwork_url.replace('100x100', '600x600')
                        return artwork_url
            
            # Si aucune correspondance exacte, prendre le premier résultat
            first_result = results[0]
            artwork_url = first_result.get('artworkUrl100')
            if artwork_url:
                artwork_url = artwork_url.replace('100x100', '600x600')
                return artwork_url
                
    except Exception as e:
        print(f"Erreur recherche iTunes pour {artist} - {title}: {e}")
    
    return None

# Test de la fonction
if __name__ == "__main__":
    # Tester avec une chanson connue
    cover_url = _fetch_album_cover_itunes("Queen", "Bohemian Rhapsody")
    print(f"Cover URL: {cover_url}")
    
    # Tester avec une chanson française
    cover_url = _fetch_album_cover_itunes("Stromae", "Alors on danse")
    print(f"Cover URL: {cover_url}")
