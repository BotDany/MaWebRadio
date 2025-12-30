from radio_metadata_fetcher_fixed_clean import RadioFetcher

# Test détaillé pour Générikds
station = 'Générikds'
url = 'https://play.radioking.io/generikids'

fetcher = RadioFetcher()
print('🎵 Test détaillé Générikds:')
print('=' * 50)
print(f'Station: {station}')
print(f'URL: {url}')
print()

# Test 1: Vérifier la détection
print('1️⃣ Test détection RadioKing:')
station_lower = station.lower()
print(f'   Station lower: {station_lower}')
print(f'   "generikids" in station_lower: {"generikids" in station_lower}')
print()

# Test 2: Appel direct de l'API
print('2️⃣ Test API RadioKing direct:')
try:
    import requests
    api_url = "https://api.radioking.io/widget/radio/generikids/track/current"
    response = requests.get(api_url, timeout=10)
    print(f'   Status API: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        print(f'   Données API: {data}')
        if not data.get("is_live", True) and data.get("title") and data.get("artist"):
            print(f'   ✅ Métadonnées disponibles: {data["artist"]} - {data["title"]}')
        else:
            print(f'   ⚠️ En direct ou pas de titre')
    else:
        print(f'   ❌ Erreur API: {response.text}')
except Exception as e:
    print(f'   ❌ Erreur: {e}')

print()

# Test 3: Appel get_metadata complet
print('3️⃣ Test get_metadata complet:')
try:
    metadata = fetcher.get_metadata(station, url)
    print(f'   Titre: {metadata.title}')
    print(f'   Artiste: {metadata.artist}')
    cover_status = 'Oui' if metadata.cover_url else 'Non'
    print(f'   Pochette: {cover_status}')
    if metadata.cover_url:
        print(f'   URL pochette: {metadata.cover_url}')
except Exception as e:
    print(f'   ❌ Erreur: {e}')

print()

# Test 4: Appel direct _get_radioking_metadata
print('4️⃣ Test _get_radioking_metadata direct:')
try:
    radioking_metadata = fetcher._get_radioking_metadata(station, url)
    if radioking_metadata:
        print(f'   ✅ Métadonnées trouvées:')
        print(f'   Titre: {radioking_metadata.title}')
        print(f'   Artiste: {radioking_metadata.artist}')
        cover_status = 'Oui' if radioking_metadata.cover_url else 'Non'
        print(f'   Pochette: {cover_status}')
    else:
        print(f'   ⚠️ Aucune métadonnée trouvée')
except Exception as e:
    print(f'   ❌ Erreur: {e}')
