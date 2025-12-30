import requests

base = 'http://127.0.0.1:5000'

print("🧪 Test des routes doubles (encodées/non encodées)")
print("=" * 50)

# Test 1: URL non encodée (comme dans les logs Railway)
print("Test 1: URL non encodée (Générikds)")
try:
    r = requests.get(f'{base}/admin/test/Générikds', timeout=5)
    print(f'   Status: {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        print(f'   Station: {data.get("station")}')
        print(f'   Status: {data.get("status")}')
except Exception as e:
    print(f'   Erreur: {e}')

# Test 2: URL encodée
print("\nTest 2: URL encodée (G%C3%A9n%C3%A9rikds)")
try:
    r = requests.get(f'{base}/admin/test/G%C3%A9n%C3%A9rikds', timeout=5)
    print(f'   Status: {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        print(f'   Station: {data.get("station")}')
        print(f'   Status: {data.get("status")}')
except Exception as e:
    print(f'   Erreur: {e}')

# Test 3: Test de suppression avec URL non encodée
print("\nTest 3: Suppression avec URL non encodée")
try:
    # D'abord ajouter une radio de test
    add_data = {'name': 'Radio Test Été', 'url': 'https://example.com/test.mp3'}
    r = requests.post(f'{base}/admin/add', data=add_data, timeout=5)
    print(f'   Ajout: {r.status_code}')
    
    # Puis supprimer avec URL non encodée
    r = requests.post(f'{base}/admin/delete/Radio Test Été', timeout=5)
    print(f'   Suppression: {r.status_code}')
except Exception as e:
    print(f'   Erreur: {e}')

print("\n✅ Tests terminés !")
