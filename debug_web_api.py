import requests
import json

# Test de l'API web de l'application
base_url = "http://127.0.0.1:5000"

print("🎵 Test de l'API web pour Générikds")
print("=" * 50)

# 1. Démarrer la lecture de Générikds
print("1️⃣ Démarrage de Générikds...")
try:
    play_response = requests.get(f"{base_url}/api/play?station=Générikds&url=https://play.radioking.io/generikids", timeout=10)
    if play_response.status_code == 200:
        play_data = play_response.json()
        print(f"   ✅ Play: {play_data}")
    else:
        print(f"   ❌ Erreur Play: {play_response.status_code}")
except Exception as e:
    print(f"   ❌ Erreur Play: {e}")

print()

# 2. Récupérer les métadonnées
print("2️⃣ Récupération des métadonnées...")
try:
    metadata_response = requests.get(f"{base_url}/api/metadata", timeout=10)
    if metadata_response.status_code == 200:
        metadata_data = metadata_response.json()
        print(f"   ✅ Status: {metadata_data.get('status')}")
        print(f"   🎵 Artiste: {metadata_data.get('artist')}")
        print(f"   🎵 Titre: {metadata_data.get('title')}")
        print(f"   📻 Station: {metadata_data.get('station')}")
        print(f"   🎧 Playing: {metadata_data.get('is_playing')}")
        
        if metadata_data.get('cover_url'):
            print(f"   📱 Pochette: {metadata_data.get('cover_url')[:50]}...")
        else:
            print(f"   📱 Pochette: Non")
            
        if metadata_data.get('status') == 'success':
            print("   🎉 Succès: Métadonnées complètes!")
        elif metadata_data.get('status') == 'no_data':
            print("   🎙️ Info: En direct (pas de chanson)")
        else:
            print(f"   ❌ Erreur: {metadata_data}")
    else:
        print(f"   ❌ Erreur HTTP: {metadata_response.status_code}")
        print(f"   Response: {metadata_response.text}")
        
except Exception as e:
    print(f"   ❌ Erreur: {e}")

print()

# 3. Test direct du fetcher
print("3️⃣ Test direct du fetcher...")
try:
    from radio_metadata_fetcher_fixed_clean import RadioFetcher
    
    fetcher = RadioFetcher()
    station = "Générikds"
    url = "https://play.radioking.io/generikids"
    
    metadata = fetcher.get_metadata(station, url)
    print(f"   ✅ Fetcher direct:")
    print(f"   🎵 Artiste: {metadata.artist}")
    print(f"   🎵 Titre: {metadata.title}")
    print(f"   📱 Pochette: {'Oui' if metadata.cover_url else 'Non'}")
    
    if metadata.title.lower() != "en direct":
        print("   🎉 Fetcher: Métadonnées détectées!")
    else:
        print("   🎙️ Fetcher: En direct")
        
except Exception as e:
    print(f"   ❌ Erreur fetcher: {e}")

print()
print("📊 Analyse:")
print("- Si le fetcher direct fonctionne mais l'API web non, problème dans final_app.py")
print("- Si les deux fonctionnent, problème de cache ou de synchronisation")
print("- Si aucun ne fonctionne, problème de connexion ou de déploiement")
