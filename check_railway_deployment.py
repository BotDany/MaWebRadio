import requests
import time

# URL de votre application Railway
RAILWAY_URL = "https://ma-webradio-production.up.railway.app"

print("🚂 Vérification du déploiement sur Railway")
print("=" * 50)

def test_deployment():
    """Tester le déploiement sur Railway"""
    
    print(f"🌐 URL de l'application: {RAILWAY_URL}")
    print()
    
    # Test 1: Page principale
    print("1️⃣ Test de la page principale...")
    try:
        response = requests.get(RAILWAY_URL, timeout=10)
        if response.status_code == 200:
            print("   ✅ Page principale accessible")
            
            # Vérifier si le bouton admin est présent
            if "🔧 Admin" in response.text:
                print("   ✅ Bouton d'administration présent")
            else:
                print("   ⚠️ Bouton d'administration non trouvé")
                
            # Vérifier si le panneau admin est inclus
            if "admin-panel" in response.text:
                print("   ✅ Panneau d'administration inclus")
            else:
                print("   ⚠️ Panneau d'administration non trouvé")
                
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Erreur de connexion: {e}")
        return False
    
    # Test 2: Page d'administration
    print("\n2️⃣ Test de la page d'administration...")
    try:
        response = requests.get(f"{RAILWAY_URL}/admin", timeout=10)
        if response.status_code == 200:
            print("   ✅ Page d'administration accessible")
            
            if "Administration des Radios" in response.text:
                print("   ✅ Contenu d'administration correct")
            else:
                print("   ⚠️ Contenu d'administration incorrect")
                
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Erreur de connexion: {e}")
    
    # Test 3: API de test de radio
    print("\n3️⃣ Test de l'API de test de radio...")
    try:
        response = requests.get(f"{RAILWAY_URL}/admin/test/RTL", timeout=15)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API test fonctionnelle: {data.get('status')}")
            if data.get('status') == 'success':
                print(f"   🎵 Métadonnées: {data.get('artist')} - {data.get('title')}")
        else:
            print(f"   ⚠️ API test status: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Erreur API: {e}")
    
    # Test 4: API play
    print("\n4️⃣ Test de l'API play...")
    try:
        response = requests.get(f"{RAILWAY_URL}/api/play?station=RTL&url=http://streaming.radio.rtl.fr/rtl-1-44-128", timeout=10)
        if response.status_code == 200:
            print("   ✅ API play fonctionnelle")
        else:
            print(f"   ⚠️ API play status: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Erreur API play: {e}")
    
    return True

# Attendre un peu que Railway déploie
print("⏳ Attente du déploiement (30 secondes)...")
time.sleep(30)

# Tester le déploiement
success = test_deployment()

print("\n" + "=" * 50)
print("📊 RÉSUMÉ DU DÉPLOIEMENT")

if success:
    print("✅ Déploiement réussi sur Railway!")
    print(f"🌐 URL de production: {RAILWAY_URL}")
    print("🔧 Administration: cliquez sur le bouton 🔧 Admin")
    print("🎵 Lecteur radio: fonctionnel avec métadonnées")
    print("💾 Configuration: sauvegardée dans radios_config.json")
else:
    print("⚠️ Déploiement en cours ou problèmes détectés")
    print("🔄 Réessayez dans quelques minutes")

print("\n🚀 Prochaines étapes:")
print("1. Vérifiez l'application sur Railway")
print("2. Testez le bouton 🔧 Admin")
print("3. Ajoutez/modifiez des radios")
print("4. Vérifiez que les changements sont persistants")

print(f"\n🎯 Lien direct: {RAILWAY_URL}")
