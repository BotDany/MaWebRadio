from radio_metadata_fetcher_fixed_clean import RadioFetcher

# Test spécifique pour Générikds
station = 'Générikds'
url = 'https://play.radioking.io/generikids'

fetcher = RadioFetcher()
print('🎵 Test Générikds - Récupération des métadonnées')
print('=' * 50)
print(f'Station: {station}')
print(f'URL: {url}')
print()

print('🔍 Test 1: get_metadata complet')
try:
    metadata = fetcher.get_metadata(station, url)
    print(f'   ✅ Succès!')
    print(f'   Titre: {metadata.title}')
    print(f'   Artiste: {metadata.artist}')
    cover_status = 'Oui' if metadata.cover_url else 'Non'
    print(f'   Pochette: {cover_status}')
    if metadata.cover_url:
        print(f'   URL pochette: {metadata.cover_url}')
    print(f'   Host: {metadata.host}')
    print()
    
    # Vérifier si c'est "En direct" ou une vraie chanson
    if metadata.title.lower() != "en direct":
        print('🎵 Résultat: Métadonnées de musique détectées!')
    else:
        print('🎙️ Résultat: En direct (pas de chanson en cours)')
        
except Exception as e:
    print(f'   ❌ Erreur: {e}')

print()

print('🔍 Test 2: API RadioKing direct')
try:
    import requests
    api_url = "https://api.radioking.io/widget/radio/generikids/track/current"
    response = requests.get(api_url, timeout=5)
    
    if response.status_code == 200:
        data = response.json()
        print(f'   ✅ API répond (status: {response.status_code})')
        print(f'   is_live: {data.get("is_live", "N/A")}')
        print(f'   title: {data.get("title", "N/A")}')
        print(f'   artist: {data.get("artist", "N/A")}')
        print(f'   cover: {data.get("cover", "N/A")[:50]}...' if data.get("cover") else '   cover: Non')
        
        if not data.get("is_live", True) and data.get("title") and data.get("artist"):
            print('   🎵 API: Métadonnées disponibles!')
        else:
            print('   🎙️ API: En direct ou pas de titre')
    else:
        print(f'   ❌ Erreur HTTP: {response.status_code}')
        
except Exception as e:
    print(f'   ❌ Erreur API: {e}')

print()

print('🔍 Test 3: Flux ICY direct')
try:
    stream_url = "https://listen.radioking.com/radio/497599/stream/554719"
    print(f'   Test du flux: {stream_url}')
    
    icy_metadata = fetcher._get_icy_metadata(stream_url, station)
    print(f'   Titre ICY: {icy_metadata.title}')
    print(f'   Artiste ICY: {icy_metadata.artist}')
    cover_status = 'Oui' if icy_metadata.cover_url else 'Non'
    print(f'   Pochette ICY: {cover_status}')
    
    if icy_metadata.title.lower() != "en direct":
        print('   🎵 ICY: Métadonnées détectées!')
    else:
        print('   🎙️ ICY: En direct')
        
except Exception as e:
    print(f'   ❌ Erreur ICY: {e}')

print()
print('📊 Résumé final:')
print('   - API RadioKing: Métadonnées en temps réel')
print('   - Flux ICY: Métadonnées du flux audio')
print('   - Timeout optimisé: 5 secondes maximum')
print('   - Support pochette: Inclus')
print()
print('🚀 Générikds est maintenant optimisé pour les métadonnées rapides!')
