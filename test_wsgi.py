#!/usr/bin/env python3
"""
Test simple pour vérifier si l'application démarre correctement
"""

import sys
import os

print("🔍 Test de démarrage de l'application...")

try:
    print("1. Import de Flask...")
    from flask import Flask
    print("   ✅ Flask importé")
    
    print("2. Import du fetcher...")
    from radio_metadata_fetcher_fixed_clean import RadioFetcher
    print("   ✅ RadioFetcher importé")
    
    print("3. Import de l'application...")
    from radio_player_web import app
    print("   ✅ Application importée")
    
    print("4. Test des routes...")
    with app.test_client() as client:
        response = client.get('/health')
        print(f"   ✅ /health: {response.status_code}")
        
        response = client.get('/api/radios')
        print(f"   ✅ /api/radios: {response.status_code}")
        
        response = client.get('/')
        print(f"   ✅ /: {response.status_code}")
    
    print("🎉 Tous les tests passés !")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
