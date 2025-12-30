from radio_metadata_fetcher_fixed_clean import RadioFetcher
import requests

# Test direct de l'API RadioKing pour Générikds
print('🔍 TEST DIRECT API RADIOKING')
print('=' * 40)

fetcher = RadioFetcher()

# Test 1: API directe
print('1. Test API directe...')
try:
    api_url = "https://api.radioking.io/widget/radio/generikids/track/current"
    response = requests.get(api_url, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        print(f'   ✅ API Status: {response.status_code}')
        print(f'   🎤 Artiste: {data.get("artist")}')
        print(f'   🎵 Titre: {data.get("title")}')
        print(f'   💿 Album: {data.get("album")}')
        print(f'   🎙️ Direct: {data.get("is_live")}')
    else:
        print(f'   ❌ API Status: {response.status_code}')
        
except Exception as e:
    print(f'   ❌ Erreur API: {e}')

print()

# Test 2: Via fetcher.get_metadata
print('2. Test via fetcher.get_metadata...')
try:
    url = 'https://listen.radioking.com/radio/497599/stream/554719'
    metadata = fetcher.get_metadata('Générikds', url)
    
    if metadata:
        print(f'   ✅ Fetcher OK')
        print(f'   🎤 Artiste: {metadata.artist}')
        print(f'   🎵 Titre: {metadata.title}')
        print(f'   🖼️ Cover: {metadata.cover_url}')
    else:
        print(f'   ❌ Fetcher retourne None')
        
except Exception as e:
    print(f'   ❌ Erreur fetcher: {e}')

print()
print('🎯 CONCLUSION:')
print('Si API directe fonctionne mais pas fetcher -> problème dans le code fetcher')
print('Si les deux ne fonctionnent pas -> problème API RadioKing')
print('=' * 40)
