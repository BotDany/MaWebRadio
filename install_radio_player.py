#!/usr/bin/env python3
"""
Script d'installation pour le Lecteur Radio avec SON
"""

import subprocess
import sys
import os

def install_package(package):
    """Installe un package avec pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} installé avec succès")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Erreur lors de l'installation de {package}")
        return False

def check_package(package):
    """Vérifie si un package est installé"""
    try:
        __import__(package)
        print(f"✅ {package} est déjà installé")
        return True
    except ImportError:
        print(f"⚠️ {package} n'est pas installé")
        return False

def main():
    print("🎵 Installation du Lecteur Radio avec SON")
    print("=" * 50)
    
    # Packages requis pour l'audio
    packages = {
        'pygame': 'Pour le son dans l\'interface Tkinter',
        'flask': 'Pour l\'interface web',
        'requests': 'Pour les métadonnées (déjà requis)',
        'beautifulsoup4': 'Pour Bide Et Musique (optionnel)'
    }
    
    print("\n📦 Vérification des packages requis:")
    
    missing_packages = []
    for package, description in packages.items():
        if not check_package(package):
            missing_packages.append((package, description))
    
    if not missing_packages:
        print("\n🎉 Tous les packages sont déjà installés!")
        print("🎵 Vous pouvez lancer le lecteur radio:")
        print("   • Interface graphique: python radio_player_sound.py")
        print("   • Interface web: python radio_player_web.py")
        return
    
    print(f"\n📦 Installation des {len(missing_packages)} packages manquants:")
    
    success_count = 0
    for package, description in missing_packages:
        print(f"\n📥 Installation de {package} - {description}")
        if install_package(package):
            success_count += 1
    
    print(f"\n📊 Résultat: {success_count}/{len(missing_packages)} packages installés")
    
    if success_count == len(missing_packages):
        print("\n🎉 Installation réussie!")
        print("\n🎵 Vous pouvez maintenant lancer le lecteur radio:")
        print("   • Interface graphique avec son: python radio_player_sound.py")
        print("   • Interface web avec audio HTML5: python radio_player_web.py")
        print("   • Version simple sans son: python radio_player_simple.py")
    else:
        print("\n⚠️ Certains packages n'ont pas pu être installés")
        print("📋 Le lecteur fonctionnera toujours, mais sans certaines fonctionnalités")
    
    print("\n💡 Note: Pour le son dans l'interface graphique, pygame est requis")
    print("💡 Note: L'interface web utilise HTML5 audio (pas besoin de pygame)")

if __name__ == "__main__":
    main()
