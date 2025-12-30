#!/usr/bin/env python3
"""
Script de test pour vérifier que l'application peut démarrer correctement
"""

import sys
import os

def test_imports():
    """Tester que tous les imports nécessaires fonctionnent"""
    print("🔍 Test des imports...")
    
    try:
        from flask import Flask, render_template, jsonify, request, flash, redirect, url_for
        print("   ✅ Flask imports OK")
    except ImportError as e:
        print(f"   ❌ Flask import error: {e}")
        return False
    
    try:
        import json
        print("   ✅ JSON import OK")
    except ImportError as e:
        print(f"   ❌ JSON import error: {e}")
        return False
    
    try:
        from radio_metadata_fetcher_fixed_clean import RadioFetcher
        print("   ✅ RadioFetcher import OK")
    except ImportError as e:
        print(f"   ❌ RadioFetcher import error: {e}")
        return False
    
    return True

def test_app_creation():
    """Tester la création de l'application Flask"""
    print("\n🏗️ Test de création de l'application...")
    
    try:
        from final_app import app, load_radios
        print("   ✅ App importée")
        
        # Tester load_radios
        radios = load_radios()
        print(f"   ✅ load_radios() fonctionne: {len(radios)} radios")
        
        # Tester les routes
        with app.test_client() as client:
            response = client.get('/')
            print(f"   ✅ Route '/' : {response.status_code}")
            
            response = client.get('/admin')
            print(f"   ✅ Route '/admin' : {response.status_code}")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur création app: {e}")
        return False

def test_file_structure():
    """Vérifier que les fichiers nécessaires existent"""
    print("\n📁 Test de structure des fichiers...")
    
    required_files = [
        'final_app.py',
        'radio_metadata_fetcher_fixed_clean.py',
        'templates/index.html',
        'Procfile',
        'requirements.txt',
        'runtime.txt'
    ]
    
    all_good = True
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} manquant")
            all_good = False
    
    return all_good

def test_requirements():
    """Vérifier les requirements"""
    print("\n📦 Test des requirements...")
    
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read().strip()
        
        print("   Contenu de requirements.txt:")
        print(f"   {requirements}")
        
        # Vérifier les packages essentiels
        essential_packages = ['Flask', 'requests']
        for package in essential_packages:
            if package in requirements:
                print(f"   ✅ {package} trouvé")
            else:
                print(f"   ❌ {package} manquant")
                return False
        
        return True
        
    except FileNotFoundError:
        print("   ❌ requirements.txt non trouvé")
        return False

def main():
    """Fonction principale de test"""
    print("🧪 TEST DE DÉMARRAGE DE L'APPLICATION")
    print("=" * 50)
    
    # Tests
    imports_ok = test_imports()
    app_ok = test_app_creation()
    files_ok = test_file_structure()
    requirements_ok = test_requirements()
    
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    
    if all([imports_ok, app_ok, files_ok, requirements_ok]):
        print("✅ Tous les tests sont passés!")
        print("🚀 L'application devrait démarrer correctement")
        return 0
    else:
        print("❌ Certains tests ont échoué")
        print("🔧 Corrigez les problèmes avant de déployer")
        return 1

if __name__ == '__main__':
    sys.exit(main())
