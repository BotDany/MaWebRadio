#!/usr/bin/env python3
"""
Script pour ajouter Nostalgie Romania directement dans PostgreSQL
"""

import psycopg
import os
from urllib.parse import urlparse

# Configuration PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    parsed = urlparse(DATABASE_URL)
    DB_CONFIG = {
        'host': parsed.hostname,
        'dbname': parsed.path[1:],
        'user': parsed.username,
        'password': parsed.password,
        'port': parsed.port
    }
else:
    # Configuration fallback
    DB_CONFIG = {
        'host': os.environ.get('DB_HOST', 'trolley.proxy.rlwy.net'),
        'dbname': os.environ.get('DB_NAME', 'railway'),
        'user': os.environ.get('DB_USER', 'postgres'),
        'password': os.environ.get('DB_PASSWORD', 'LwAVoXBRvbvKpZKDLVBojSQXqFzNGeoe'),
        'port': os.environ.get('DB_PORT', '27920')
    }

def add_nostalgie_romania():
    """Ajouter Nostalgie Romania à la base de données"""
    try:
        print("🔌 Connexion à PostgreSQL...")
        conn = psycopg.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Insérer la nouvelle radio
        cursor.execute("""
            INSERT INTO radios (name, url) 
            VALUES (%s, %s)
            ON CONFLICT (name) DO NOTHING
        """, ("Nostalgie Romania", "https://nl.digitalrm.pt:8140/stream"))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Nostalgie Romania ajoutée avec succès !")
        print("🌐 Rafraîchissez votre application webradio")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    print("🎵 Ajout de Nostalgie Romania dans PostgreSQL")
    print("=" * 50)
    add_nostalgie_romania()
