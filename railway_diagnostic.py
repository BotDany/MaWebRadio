import requests
import json
import time

# URL de votre application Railway
RAILWAY_URL = "https://ma-webradio-production.up.railway.app"

print("🔍 DIAGNOSTIC COMPLET RAILWAY")
print("=" * 50)

def diagnose_railway():
    """Diagnostic complet du déploiement Railway"""
    
    print(f"🌐 URL testée: {RAILWAY_URL}")
    print()
    
    # Test 1: Vérification de base
    print("1️⃣ Test de connectivité de base...")
    try:
        response = requests.get(RAILWAY_URL, timeout=10)
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 404:
            print("   ❌ 404 - L'application n'est pas trouvée")
            print("   🔍 Causes possibles:")
            print("      - Procfile incorrect")
            print("      - Application qui ne démarre pas")
            print("      - Route incorrecte")
            print("      - Problème de dépendances")
            
        elif response.status_code == 500:
            print("   ❌ 500 - Erreur serveur interne")
            print("   🔍 Causes possibles:")
            print("      - Erreur dans le code")
            print("      - Dépendances manquantes")
            print("      - Variables d'environnement")
            
        elif response.status_code == 200:
            print("   ✅ Application accessible!")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Erreur de connexion - Service indisponible")
        print("   🔍 Causes possibles:")
        print("      - Application en cours de déploiement")
        print("      - Service arrêté")
        print("      - Configuration réseau")
        
    except requests.exceptions.Timeout:
        print("   ❌ Timeout - L'application met trop temps à répondre")
        
    except Exception as e:
        print(f"   ❌ Erreur inattendue: {e}")
    
    print()
    
    # Test 2: Vérification des routes spécifiques
    print("2️⃣ Test des routes spécifiques...")
    
    routes_to_test = [
        "/",
        "/admin",
        "/api/metadata",
        "/api/play?station=RTL&url=http://streaming.radio.rtl.fr/rtl-1-44-128"
    ]
    
    for route in routes_to_test:
        try:
            full_url = f"{RAILWAY_URL}{route}"
            response = requests.get(full_url, timeout=10)
            print(f"   {route}: {response.status_code}")
            
            if response.status_code == 200 and route == "/":
                # Vérifier le contenu
                if "🔧 Admin" in response.text:
                    print("      ✅ Bouton admin trouvé")
                else:
                    print("      ⚠️ Bouton admin non trouvé")
                    
        except Exception as e:
            print(f"   {route}: Erreur - {e}")
    
    print()
    
    # Test 3: Vérification du domaine
    print("3️⃣ Vérification du domaine...")
    try:
        # Essayer avec et sans https
        urls_to_test = [
            "https://ma-webradio-production.up.railway.app",
            "http://ma-webradio-production.up.railway.app"
        ]
        
        for url in urls_to_test:
            try:
                response = requests.get(url, timeout=5, allow_redirects=False)
                print(f"   {url}: {response.status_code}")
            except:
                print(f"   {url}: Erreur de connexion")
                
    except Exception as e:
        print(f"   ❌ Erreur test domaine: {e}")
    
    print()
    
    # Test 4: Informations sur le déploiement
    print("4️⃣ Informations de déploiement...")
    print("   📋 Vérifications à faire sur Railway:")
    print("      1. Allez sur railway.app")
    print("      2. Vérifiez le statut du service")
    print("      3. Consultez les logs de build")
    print("      4. Consultez les logs d'exécution")
    print("      5. Vérifiez les variables d'environnement")
    print("      6. Vérifiez le domaine configuré")
    
    print()
    print("🔧 Actions recommandées:")
    print("   1. Vérifier les logs Railway pour les erreurs")
    print("   2. Redémarrer le service manuellement")
    print("   3. Vérifier que final_app.py est bien exécutable")
    print("   4. Confirmer que toutes les dépendances sont installées")
    print("   5. S'assurer que le port $PORT est bien utilisé")

# Exécuter le diagnostic
diagnose_railway()

print("\n" + "=" * 50)
print("📊 RÉSUMÉ DU DIAGNOSTIC")
print("❌ L'application n'est pas accessible sur Railway")
print("🔄 Le déploiement semble avoir échoué")
print("🔍 Consultez les logs Railway pour plus de détails")
print("\n🚀 Prochaines étapes:")
print("1. Connectez-vous à railway.app")
print("2. Vérifiez le statut de votre service")
print("3. Consultez les logs de build et d'exécution")
print("4. Corrigez les erreurs identifiées")
print("5. Redéployez si nécessaire")
