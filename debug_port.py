#!/usr/bin/env python3
"""
Debug pour trouver le problème de port sur Railway
"""

import os
import sys
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    port = os.environ.get('PORT', 'non défini')
    return f"""
    <h1>🔍 Debug Port Railway</h1>
    <p>PORT d'environnement: {port}</p>
    <p>Python version: {sys.version}</p>
    <p>Application fonctionne !</p>
    """

@app.route('/health')
def health():
    return {'status': 'ok', 'port': os.environ.get('PORT', 'non défini')}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))  # Essayer 8080 par défaut
    print(f"🔍 Debug: Tentative de démarrage sur le port {port}")
    print(f"🔍 Debug: PORT env = {os.environ.get('PORT')}")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=True)
    except Exception as e:
        print(f"❌ Erreur: {e}")
        # Essayer un autre port
        print("🔄 Tentative sur le port 8080...")
        app.run(host='0.0.0.0', port=8080, debug=True)
