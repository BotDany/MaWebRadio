#!/usr/bin/env python3
"""
Script pour migrer les radios - À exécuter SUR Railway (pas en local)
"""

import psycopg
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from urllib.parse import urlparse

# Ancienne configuration (source) - Ancien projet
OLD_DB_CONFIG = {
    'host': 'trolley.proxy.rlwy.net',
    'database': 'railway',
    'user': 'postgres',
    'password': 'LwAVoXBRvbvKpZKDLVBojSQXqFzNGeoe',
    'port': '27920'
}

# Nouvelle configuration (destination) - Variables Railway
NEW_DB_CONFIG = {
    'host': os.environ.get('PGHOST'),
    'dbname': os.environ.get('PGDATABASE'),
    'user': os.environ.get('PGUSER'),
    'password': os.environ.get('PGPASSWORD'),
    'port': os.environ.get('PGPORT')
}

def migrate_radios():
    """Migrer les radios de l'ancien vers le nouveau PostgreSQL"""
    try:
        print("🔌 Connexion à l'ancienne base de données...")
        old_conn = psycopg2.connect(**OLD_DB_CONFIG, cursor_factory=RealDictCursor)
        old_cursor = old_conn.cursor()
        
        print("📋 Lecture des radios depuis l'ancienne base...")
        old_cursor.execute("SELECT name, url FROM radios ORDER BY name")
        radios = old_cursor.fetchall()
        
        if not radios:
            print("⚠️ Aucune radio trouvée dans l'ancienne base")
            old_cursor.close()
            old_conn.close()
            return False
        
        print(f"✅ {len(radios)} radios trouvées dans l'ancienne base")
        
        old_cursor.close()
        old_conn.close()
        
        print("🔌 Connexion à la nouvelle base de données...")
        new_conn = psycopg.connect(**NEW_DB_CONFIG)
        new_cursor = new_conn.cursor()
        
        # Créer la table si elle n'existe pas
        new_cursor.execute("""
            CREATE TABLE IF NOT EXISTS radios (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Vider la table (au cas où)
        new_cursor.execute("DELETE FROM radios")
        
        print("📻 Insertion des radios dans la nouvelle base...")
        inserted_count = 0
        for radio in radios:
            try:
                new_cursor.execute("INSERT INTO radios (name, url) VALUES (%s, %s)", 
                                  (radio['name'], radio['url']))
                inserted_count += 1
                print(f"   ✅ {radio['name']}")
            except Exception as e:
                print(f"   ❌ Erreur insertion {radio['name']}: {e}")
        
        new_conn.commit()
        new_cursor.close()
        new_conn.close()
        
        print(f"\n🎉 Migration réussie ! {inserted_count}/{len(radios)} radios transférées")
        
        # Afficher les radios migrées
        print("\n📋 Radios migrées avec succès :")
        for radio in radios:
            print(f"   🎵 {radio['name']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur de migration: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Migration PostgreSQL - À exécuter SUR Railway")
    print("=" * 50)
    print("📍 Source : trolley.proxy.rlwy.net:27920")
    print("📍 Destination : Variables Railway internes")
    print("=" * 50)
    
    success = migrate_radios()
    
    if success:
        print("\n✅ Migration terminée !")
        print("🌐 Rafraîchissez votre application pour voir les radios migrées")
    else:
        print("\n❌ Migration échouée")
