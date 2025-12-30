# Configuration PostgreSQL pour les radios
import psycopg
import os
from psycopg.rows import dict_row

# Configuration de la base de données - Variables Railway internes (nouveau projet)
DB_CONFIG = {
    'host': os.environ.get('PGHOST'),  # Pas de fallback pour forcer les bonnes variables
    'dbname': os.environ.get('PGDATABASE'),
    'user': os.environ.get('PGUSER'),
    'password': os.environ.get('PGPASSWORD'),  # Utiliser le vrai password de Railway
    'port': os.environ.get('PGPORT')
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
    """Charger la liste des radios depuis PostgreSQL ou fallback"""
    try:
        conn = get_db_connection()
        if conn is None:
            print("⚠️ PostgreSQL inaccessible, utilisation des radios par défaut")
            return get_default_radios()
        
        cursor = conn.cursor(row_factory=dict_row)
        
        cursor.execute("SELECT name, url FROM radios ORDER BY name")
        radios = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        if not radios:
            print("⚠️ Aucune radio dans PostgreSQL, utilisation des radios par défaut")
            return get_default_radios()
        
        # Convertir en liste de tuples pour compatibilité
        return [[radio['name'], radio['url']] for radio in radios]
        
    except Exception as e:
        print(f"❌ Erreur chargement radios PostgreSQL: {e}")
        print("📻 Utilisation des radios par défaut")
        return get_default_radios()

def get_default_radios():
    """Retourner la liste des radios par défaut"""
    return [
        ["RTL", "http://streaming.radio.rtl.fr/rtl-1-44-128"],
        ["Chante France-80s", "https://chantefrance80s.ice.infomaniak.ch/chantefrance80s-128.mp3"],
        ["100% Radio 80", "http://100radio-80.ice.infomaniak.ch/100radio-80-128.mp3"],
        ["RFM 80-90", "http://rfm-live-mp3-128.scdn.arkena.com/rfm.mp3"],
        ["RTL2 80s", "http://streaming.radio.rtl2.fr/rtl2-1-44-128"],
        ["Virgin Radio 80s", "https://ais-live.cloud-services.asso.fr/virginradio.mp3"],
        ["Bide Et Musique", "https://relay1.bide-et-musique.com:9300/bm.mp3"],
        ["Flash 80 Radio", "https://manager7.streamradio.fr:1985/stream"],
        ["Mega Hits", "https://playerservices.streamtheworld.com/api/livestream-redirect/MEGA_HITSAAC_SC"],
        ["Radio Comercial", "https://stream-icy.bauermedia.pt/comercial.mp3"],
        ["Superloustic", "https://radio6.pro-fhi.net/live/SUPERLOUSTIC"],
        ["Génération Dorothée", "https://stream.votreradiosurlenet.eu/generationdorothee.mp3"],
        ["Top 80 Radio", "https://securestreams6.autopo.st:2321/"],
        ["Chansons Oubliées Où Presque", "https://manager7.streamradio.fr:2850/stream"],
        ["Générikds", "https://listen.radioking.com/radio/497599/stream/554719"]
    ]

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
        print("🔌 Tentative de connexion à PostgreSQL...")
        conn = get_db_connection()
        if conn is None:
            print("⚠️ Impossible de se connecter à PostgreSQL, utilisation du mode fallback")
            return False
            
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
        
        # Vérifier si la table est vide et insérer les radios par défaut
        cursor.execute("SELECT COUNT(*) as count FROM radios")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("📻 Table vide, insertion automatique des 15 radios...")
            
            # Liste complète des radios par défaut
            default_radios = [
                ("RTL", "http://streaming.radio.rtl.fr/rtl-1-44-128"),
                ("Chante France-80s", "https://chantefrance80s.ice.infomaniak.ch/chantefrance80s-128.mp3"),
                ("100% Radio 80", "http://100radio-80.ice.infomaniak.ch/100radio-80-128.mp3"),
                ("RFM 80-90", "http://rfm-live-mp3-128.scdn.arkena.com/rfm.mp3"),
                ("RTL2 80s", "http://streaming.radio.rtl2.fr/rtl2-1-44-128"),
                ("Virgin Radio 80s", "https://ais-live.cloud-services.asso.fr/virginradio.mp3"),
                ("Bide Et Musique", "https://relay1.bide-et-musique.com:9300/bm.mp3"),
                ("Flash 80 Radio", "https://manager7.streamradio.fr:1985/stream"),
                ("Mega Hits", "https://playerservices.streamtheworld.com/api/livestream-redirect/MEGA_HITSAAC_SC"),
                ("Radio Comercial", "https://stream-icy.bauermedia.pt/comercial.mp3"),
                ("Superloustic", "https://radio6.pro-fhi.net/live/SUPERLOUSTIC"),
                ("Génération Dorothée", "https://stream.votreradiosurlenet.eu/generationdorothee.mp3"),
                ("Top 80 Radio", "https://securestreams6.autopo.st:2321/"),
                ("Chansons Oubliées Où Presque", "https://manager7.streamradio.fr:2850/stream"),
                ("Générikds", "https://listen.radioking.com/radio/497599/stream/554719")
            ]
            
            # Insérer toutes les radios
            for name, url in default_radios:
                cursor.execute("INSERT INTO radios (name, url) VALUES (%s, %s)", (name, url))
            
            conn.commit()
            print(f"✅ {len(default_radios)} radios insérées automatiquement !")
        else:
            print(f"✅ {count} radios déjà présentes dans la base")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Base de données PostgreSQL initialisée")
        return True
        
    except Exception as e:
        print(f"⚠️ Erreur initialisation DB: {e}")
        print("📻 L'application continuera en mode fallback")
        return False

# Initialiser la base de données au démarrage (non bloquant)
print("🚀 Démarrage de l'application webradio...")
init_database()
