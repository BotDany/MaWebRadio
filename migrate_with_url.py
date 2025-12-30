#!/usr/bin/env python3
"""
Migration en utilisant directement les URLs de connexion
"""

import psycopg
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from urllib.parse import urlparse

# Ancienne base (source) - URL que vous avez montrée
OLD_URL = "postgresql://postgres:LwAVoXBRvbvKpZKDLVBojSQXqFzNGeoe@trolley.proxy.rlwy.net:27920/railway"

# Nouvelle base (destination) - DATABASE_URL de Railway
NEW_URL = os.environ.get('DATABASE_URL')

def parse_url(url):
    """Parser une URL PostgreSQL"""
    parsed = urlparse(url)
    return {
        'host': parsed.hostname,
        'dbname': parsed.path[1:],  # Enlever le /
        'user': parsed.username,
        'password': parsed.password,
        'port': parsed.port
    }

def migrate():
    try:
        print("🔌 Connexion à l'ancienne base...")
        old_config = parse_url(OLD_URL)
        old_conn = psycopg2.connect(**old_config, cursor_factory=RealDictCursor)
        old_cursor = old_conn.cursor()
        
        print("📋 Lecture des radios...")
        old_cursor.execute("SELECT name, url FROM radios ORDER BY name")
        radios = old_cursor.fetchall()
        
        if not radios:
            print("⚠️ Aucune radio trouvée")
            return
        
        print(f"✅ {len(radios)} radios trouvées")
        
        old_cursor.close()
        old_conn.close()
        
        print("🔌 Connexion à la nouvelle base...")
        if not NEW_URL:
            print("❌ DATABASE_URL non trouvé")
            return
            
        new_config = parse_url(NEW_URL)
        print(f"📍 Connexion vers: {new_config['host']}:{new_config['port']}")
        
        new_conn = psycopg.connect(**new_config)
        new_cursor = new_conn.cursor()
        
        # Créer table
        new_cursor.execute("""
            CREATE TABLE IF NOT EXISTS radios (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Vider table
        new_cursor.execute("DELETE FROM radios")
        
        print("📻 Insertion des radios...")
        success_count = 0
        for radio in radios:
            try:
                new_cursor.execute("INSERT INTO radios (name, url) VALUES (%s, %s)", 
                                  (radio['name'], radio['url']))
                success_count += 1
                print(f"   ✅ {radio['name']}")
            except Exception as e:
                print(f"   ❌ {radio['name']}: {e}")
        
        new_conn.commit()
        new_cursor.close()
        new_conn.close()
        
        print(f"\n🎉 Migration terminée ! {success_count}/{len(radios)} radios transférées")
        print("🌐 Rafraîchissez votre application webradio")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    print("🚀 Migration avec URLs de connexion")
    print("=" * 50)
    print("📍 Source: trolley.proxy.rlwy.net:27920")
    print("📍 Destination: DATABASE_URL")
    print("=" * 50)
    
    migrate()
