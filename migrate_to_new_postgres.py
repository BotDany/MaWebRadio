#!/usr/bin/env python3
"""
Script pour migrer les données de l'ancien PostgreSQL vers le nouveau
"""

import psycopg
import psycopg2
from psycopg2.extras import RealDictCursor

# Ancienne configuration (source)
OLD_DB_CONFIG = {
    'host': 'trolley.proxy.rlwy.net',
    'database': 'railway',
    'user': 'postgres',
    'password': 'LwAVoXBRvbvKpZKDLVBojSQXqFzNGeoe',
    'port': '27920'
}

# Nouvelle configuration (destination) - À MODIFIER
NEW_DB_CONFIG = {
    'host': 'NOUVEAU_HOST',  # Remplacer avec le nouveau host
    'dbname': 'NOUVEAU_DB',  # Remplacer avec le nouveau nom de base
    'user': 'NOUVEAU_USER',  # Remplacer avec le nouvel utilisateur
    'password': 'NOUVEAU_PASSWORD',  # Remplacer avec le nouveau password
    'port': 'NOUVEAU_PORT'  # Remplacer avec le nouveau port
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
        
        print(f"✅ {len(radios)} radios trouvées")
        
        old_cursor.close()
        old_conn.close()
        
        print("🔌 Connexion à la nouvelle base de données...")
        new_conn = psycopg.connect(**NEW_DB_CONFIG)
        new_cursor = new_conn.cursor()
        
        # Créer la table
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
        for radio in radios:
            new_cursor.execute("INSERT INTO radios (name, url) VALUES (%s, %s)", 
                              (radio['name'], radio['url']))
        
        new_conn.commit()
        new_cursor.close()
        new_conn.close()
        
        print(f"🎉 Migration réussie ! {len(radios)} radios transférées")
        
        # Afficher les radios migrées
        print("\n📋 Radios migrées :")
        for radio in radios:
            print(f"   📻 {radio['name']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur de migration: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Migration PostgreSQL vers nouveau projet")
    print("=" * 50)
    
    print("⚠️  MODIFIEZ NEW_DB_CONFIG avec vos nouveaux identifiants !")
    print("⚠️  Commentez cette ligne après avoir modifié la configuration")
    
    # Décommentez la ligne suivante après avoir configuré NEW_DB_CONFIG
    # migrate_radios()
