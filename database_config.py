# Configuration PostgreSQL pour les radios
import psycopg
import os
from psycopg.rows import dict_row

# Configuration de la base de données
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'database': os.environ.get('DB_NAME', 'ma_webradio'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'port': os.environ.get('DB_PORT', '5432')
}

def get_db_connection():
    """Établir une connexion à la base de données PostgreSQL"""
    try:
        conn = psycopg.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Erreur de connexion à la base de données: {e}")
        return None

def load_radios():
    """Charger la liste des radios depuis PostgreSQL"""
    try:
        conn = get_db_connection()
        if conn is None:
            return []
        
        cursor = conn.cursor(row_factory=dict_row)
        
        cursor.execute("SELECT name, url FROM radios ORDER BY name")
        radios = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Convertir en liste de tuples pour compatibilité
        return [[radio['name'], radio['url']] for radio in radios]
        
    except Exception as e:
        print(f"❌ Erreur chargement radios PostgreSQL: {e}")
        return []

def save_radios(radios):
    """Sauvegarder la liste des radios dans PostgreSQL"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Vider la table
        cursor.execute("DELETE FROM radios")
        
        # Insérer les nouvelles radios
        for name, url in radios:
            cursor.execute("INSERT INTO radios (name, url) VALUES (%s, %s)", (name, url))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ {len(radios)} radios sauvegardées dans PostgreSQL")
        
    except Exception as e:
        print(f"❌ Erreur sauvegarde radios PostgreSQL: {e}")

def init_database():
    """Initialiser la base de données et créer la table si nécessaire"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Créer la table des radios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS radios (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Base de données PostgreSQL initialisée")
        
    except Exception as e:
        print(f"❌ Erreur initialisation DB: {e}")

# Initialiser la base de données au démarrage
init_database()
