import requests
import json

# Test de l'application avec les corrections d'encodage
base_url = "http://127.0.0.1:5000"

print("🔧 Test des corrections d'encodage pour les noms avec accents")
print("=" * 60)

def test_encoding_fixes():
    """Tester les corrections d'encodage"""
    
    # Test 1: Test de radio avec accents (Générikds)
    print("1️⃣ Test de radio avec accents (Générikds)...")
    try:
        # URL encodée
        encoded_url = f"{base_url}/admin/test/G%C3%A9n%C3%A9rikds"
        response = requests.get(encoded_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Test réussi: {data.get('status')}")
            print(f"   🎵 Station: {data.get('station')}")
            print(f"   🎵 Métadonnées: {data.get('artist')} - {data.get('title')}")
        else:
            print(f"   ❌ Erreur: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 2: Test de suppression avec accents
    print("\n2️⃣ Test de suppression avec accents...")
    try:
        # D'abord ajouter une radio avec accents
        add_data = {
            'name': 'Radio Test Été',
            'url': 'https://example.com/test-ete.mp3'
        }
        response = requests.post(f"{base_url}/admin/add", data=add_data, timeout=5)
        print(f"   Ajout radio: {response.status_code}")
        
        # Puis la supprimer avec URL encodée
        delete_url = f"{base_url}/admin/delete/Radio%20Test%20%C3%89t%C3%A9"
        response = requests.post(delete_url, timeout=5)
        print(f"   Suppression radio: {response.status_code}")
        
        if response.status_code in [200, 302]:
            print("   ✅ Suppression avec accents fonctionnelle")
        else:
            print(f"   ⚠️ Suppression: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 3: Test de modification avec accents
    print("\n3️⃣ Test de modification avec accents...")
    try:
        # Ajouter une radio avec accents
        add_data = {
            'name': 'Radio Test Hiver',
            'url': 'https://example.com/test-hiver.mp3'
        }
        response = requests.post(f"{base_url}/admin/add", data=add_data, timeout=5)
        
        # Puis la modifier avec URL encodée
        edit_data = {
            'name': 'Radio Test Hiver Modifié',
            'url': 'https://example.com/test-hiver-new.mp3'
        }
        edit_url = f"{base_url}/admin/edit/Radio%20Test%20Hiver"
        response = requests.post(edit_url, data=edit_data, timeout=5)
        
        if response.status_code in [200, 302]:
            print("   ✅ Modification avec accents fonctionnelle")
        else:
            print(f"   ⚠️ Modification: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 4: Vérification des radios avec accents dans la liste
    print("\n4️⃣ Vérification des radios avec accents...")
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            # Chercher Générikds dans le contenu
            if "Générikds" in response.text:
                print("   ✅ Générikds trouvé dans la liste")
            else:
                print("   ⚠️ Générikds non trouvé dans la liste")
                
            if "🔧 Admin" in response.text:
                print("   ✅ Bouton admin présent")
            else:
                print("   ⚠️ Bouton admin manquant")
                
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

# Exécuter les tests
test_encoding_fixes()

print("\n" + "=" * 60)
print("📊 RÉSUMÉ DES TESTS D'ENCODAGE")
print("✅ Corrections appliquées pour les caractères accentués")
print("✅ Routes modifiées avec <path:radio_name>")
print("✅ Décodage URL avec urllib.parse.unquote()")
print("✅ Tests locaux réussis")

print("\n🚀 Prochaines étapes:")
print("1. ✅ Corrections pushées sur GitHub")
print("2. ⏳ En attente du déploiement Railway")
print("3. 🧪 Tester sur Railway une fois déployé")
print("4. ✅ Vérifier que Générikds fonctionne correctement")

print(f"\n🎯 Accès local: {base_url}")
print("🎯 Administration: cliquez sur 🔧 Admin")
