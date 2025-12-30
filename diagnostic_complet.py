import requests
import json
from radio_metadata_fetcher_fixed_clean import RadioFetcher

print('🎵 DIAGNOSTIC COMPLET EN UNE SEULE FOIS')
print('=' * 50)

# 1. Test API RadioKing direct
print('1️⃣ Test API RadioKing direct...')
try:
    api_url = "https://api.radioking.io/widget/radio/generikids/track/current"
    response = requests.get(api_url, timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f'   ✅ API: {data.get("artist")} - {data.get("title")}')
    else:
        print(f'   ❌ API Status: {response.status_code}')
except Exception as e:
    print(f'   ❌ API Erreur: {e}')

# 2. Test fetcher
print('\n2️⃣ Test fetcher.get_metadata...')
try:
    fetcher = RadioFetcher()
    url = 'https://listen.radioking.com/radio/497599/stream/554719'
    metadata = fetcher.get_metadata('Générikds', url)
    if metadata:
        print(f'   ✅ Fetcher: {metadata.artist} - {metadata.title}')
    else:
        print(f'   ❌ Fetcher: Pas de métadonnées')
except Exception as e:
    print(f'   ❌ Fetcher Erreur: {e}')

# 3. Test configuration
print('\n3️⃣ Vérification configuration...')
try:
    with open('radios_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
        for name, url in config:
            if 'Générikds' in name:
                print(f'   📻 Config: {name}')
                print(f'   🔗 URL: {url}')
                break
except Exception as e:
    print(f'   ❌ Config Erreur: {e}')

print('\n🎯 CONCLUSION RAPIDE:')
print('✅ Si API direct fonctionne -> problème fetcher')
print('✅ Si API ne fonctionne pas -> problème RadioKing')
print('✅ Si les deux fonctionnent -> problème interface web')
