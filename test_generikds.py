from radio_metadata_fetcher_fixed_clean import RadioFetcher
import time

# Test spécifique pour Générikds
station = 'Générikds'
url = 'https://www.radioking.com/play/generikids'

fetcher = RadioFetcher()
print('🎵 Test approfondi pour Générikds (RadioKing):')
print('=' * 60)
print(f'Station: {station}')
print(f'URL: {url}')
print()

# Test 1: Méthode standard get_metadata
print('1️⃣ Test avec get_metadata():')
try:
    metadata = fetcher.get_metadata(station, url)
    print(f'   Titre: {metadata.title}')
    print(f'   Artiste: {metadata.artist}')
    cover_status = 'Oui' if metadata.cover_url else 'Non'
    print(f'   Pochette: {cover_status}')
    print(f'   Host: {metadata.host}')
    if metadata.cover_url:
        print(f'   URL pochette: {metadata.cover_url[:100]}...')
except Exception as e:
    print(f'   ❌ Erreur: {e}')

print()

# Test 2: Test direct de la méthode RadioKing
print('2️⃣ Test direct de _get_radioking_metadata():')
try:
    radioking_metadata = fetcher._get_radioking_metadata(station, url)
    if radioking_metadata:
        print(f'   Titre: {radioking_metadata.title}')
        print(f'   Artiste: {radioking_metadata.artist}')
        cover_status = 'Oui' if radioking_metadata.cover_url else 'Non'
        print(f'   Pochette: {cover_status}')
        print(f'   Host: {radioking_metadata.host}')
    else:
        print('   ⚠️ Aucune métadonnée trouvée')
except Exception as e:
    print(f'   ❌ Erreur: {e}')

print()

# Test 3: Vérifier si on peut accéder à la page web
print('3️⃣ Test d\'accès à la page web RadioKing:')
try:
    import requests
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
    }
    response = requests.get(url, headers=headers, timeout=10)
    print(f'   Status HTTP: {response.status_code}')
    if response.status_code == 200:
        content = response.text
        print(f'   Taille du contenu: {len(content)} caractères')
        
        # Chercher des indices de musique
        if 'stream_url' in content.lower():
            print('   ✅ Contient "stream_url"')
        if 'current' in content.lower() and 'title' in content.lower():
            print('   ✅ Contient des infos de titre actuel')
        if 'playing' in content.lower():
            print('   ✅ Contient des infos de lecture')
    else:
        print(f'   ❌ Erreur HTTP: {response.status_code}')
except Exception as e:
    print(f'   ❌ Erreur de connexion: {e}')
