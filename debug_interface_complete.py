import requests
import json
import time

# Test de l'interface web complète
base_url = "http://127.0.0.1:5000"

print("🎵 Test complet de l'interface web pour Générikds")
print("=" * 60)

# 1. Vérifier que l'application est en ligne
print("1️⃣ Vérification de l'application...")
try:
    home_response = requests.get(base_url, timeout=5)
    if home_response.status_code == 200:
        print("   ✅ Application accessible")
    else:
        print(f"   ❌ Erreur: {home_response.status_code}")
        exit(1)
except Exception as e:
    print(f"   ❌ Erreur de connexion: {e}")
    exit(1)

print()

# 2. Démarrer Générikds
print("2️⃣ Démarrage de Générikds...")
try:
    play_response = requests.get(f"{base_url}/api/play?station=Générikds&url=https://play.radioking.io/generikids", timeout=10)
    if play_response.status_code == 200:
        play_data = play_response.json()
        print(f"   ✅ Play: {play_data}")
        print(f"   📻 Station: {play_data.get('station')}")
        print(f"   🎧 Status: {play_data.get('status')}")
    else:
        print(f"   ❌ Erreur Play: {play_response.status_code}")
        print(f"   Response: {play_response.text}")
except Exception as e:
    print(f"   ❌ Erreur Play: {e}")

print()

# 3. Attendre un peu et vérifier les métadonnées
print("3️⃣ Test des métadonnées (plusieurs tentatives)...")
for i in range(3):
    print(f"   Tentative {i+1}/3:")
    try:
        metadata_response = requests.get(f"{base_url}/api/metadata", timeout=10)
        if metadata_response.status_code == 200:
            data = metadata_response.json()
            print(f"      Status: {data.get('status')}")
            print(f"      Artiste: {data.get('artist')}")
            print(f"      Titre: {data.get('title')}")
            print(f"      Station: {data.get('station')}")
            print(f"      Playing: {data.get('is_playing')}")
            
            if data.get('status') == 'success':
                print("      🎉 Succès: Métadonnées complètes!")
                break
            elif data.get('status') == 'no_data':
                print("      🎙️ Info: En direct (pas de chanson)")
            else:
                print(f"      ❌ Erreur: {data}")
        else:
            print(f"      ❌ Erreur HTTP: {metadata_response.status_code}")
            
    except Exception as e:
        print(f"      ❌ Erreur: {e}")
    
    if i < 2:
        print("      ⏳ Attente 3 secondes...")
        time.sleep(3)

print()

# 4. Vérifier l'état de la radio
print("4️⃣ Vérification de l'état actuel...")
try:
    metadata_response = requests.get(f"{base_url}/api/metadata", timeout=10)
    if metadata_response.status_code == 200:
        data = metadata_response.json()
        print(f"   📻 Station actuelle: {data.get('station')}")
        print(f"   🎧 Lecture en cours: {data.get('is_playing')}")
        print(f"   📊 Status API: {data.get('status')}")
        
        if data.get('status') == 'success':
            print(f"   🎵 Dernière chanson: {data.get('artist')} - {data.get('title')}")
        else:
            print(f"   🎙️ Actuellement: En direct")
    else:
        print(f"   ❌ Erreur: {metadata_response.status_code}")
        
except Exception as e:
    print(f"   ❌ Erreur: {e}")

print()

# 5. Test direct du fetcher pour comparaison
print("5️⃣ Test direct du fetcher...")
try:
    from radio_metadata_fetcher_fixed_clean import RadioFetcher
    
    fetcher = RadioFetcher()
    station = "Générikds"
    url = "https://play.radioking.io/generikids"
    
    metadata = fetcher.get_metadata(station, url)
    print(f"   🎵 Artiste (fetcher): {metadata.artist}")
    print(f"   🎵 Titre (fetcher): {metadata.title}")
    print(f"   📱 Pochette (fetcher): {'Oui' if metadata.cover_url else 'Non'}")
    
    if metadata.title.lower() != "en direct":
        print("   🎉 Fetcher: Métadonnées détectées!")
    else:
        print("   🎙️ Fetcher: En direct")
        
except Exception as e:
    print(f"   ❌ Erreur fetcher: {e}")

print()
print("📊 Analyse du problème:")
print("- Si le fetcher direct fonctionne mais l'API web non → problème dans final_app.py")
print("- Si l'API web renvoie 'no_data' → problème de timing ou de synchronisation")
print("- Si les deux fonctionnent → problème d'affichage dans le navigateur")
print("- Solution: Vérifier la console du navigateur (F12) pour les erreurs JavaScript")
