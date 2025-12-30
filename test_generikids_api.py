from radio_metadata_fetcher_fixed_clean import RadioFetcher

# Test Générikds avec l'API RadioKing
station = 'Générikds'
url = 'https://listen.radioking.com/radio/497599/stream/554719'

fetcher = RadioFetcher()
print('🎵 Test Générikds avec API RadioKing:')
print('=' * 50)

try:
    metadata = fetcher.get_metadata(station, url)
    print(f'Titre: {metadata.title}')
    print(f'Artiste: {metadata.artist}')
    cover_status = 'Oui' if metadata.cover_url else 'Non'
    print(f'Pochette: {cover_status}')
    if metadata.cover_url:
        print(f'URL pochette: {metadata.cover_url}')
    print(f'Status: ✅ Succès')
except Exception as e:
    print(f'❌ Erreur: {e}')
