#!/usr/bin/env python3
"""
Script pour vérifier la connexion PostgreSQL et afficher les radios
"""

import psycopg
from psycopg.rows import dict_row

# Configuration Railway
DB_CONFIG = {
    'host': 'trolley.proxy.rlwy.net',
    'database': 'railway',
    'user': 'postgres',
    'password': 'LwAVoXBRvbvKpZKDLVBojSQXqFzNGeoe',
    'port': '27920'
}

def check_radios():
    """Vérifier la connexion et afficher les radios"""
    try:
        print("🔌 Connexion à PostgreSQL Railway...")
        conn = psycopg.connect(**DB_CONFIG)
        cursor = conn.cursor(row_factory=dict_row)
        
        # Vérifier la table
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'radios'
        """)
        
        if cursor.fetchone() is None:
            print("❌ La table 'radios' n'existe pas")
            return False
            
        # Compter les radios
        cursor.execute("SELECT COUNT(*) as count FROM radios")
        count = cursor.fetchone()['count']
        print(f"✅ {count} radios trouvées dans la table")
        
        # Afficher les 5 premières
        cursor.execute("SELECT name, url FROM radios ORDER BY name LIMIT 5")
        print("\n📻 Exemple de radios:")
        for radio in cursor.fetchall():
            print(f"   - {radio['name']}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Vérification de la base de données PostgreSQL")
    print("=" * 60)
    
    if check_radios():
        print("\n✅ La base de données est accessible !")
    else:
        print("\n❌ Problème avec la base de données")
