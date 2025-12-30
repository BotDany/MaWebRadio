#!/usr/bin/env python3
"""
Script pour initialiser PostgreSQL avec les radios par défaut
"""

import psycopg2
import os
from psycopg2.extras import RealDictCursor

# Configuration depuis les variables d'environnement Railway
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'database': os.environ.get('DB_NAME', 'ma_webradio'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'port': os.environ.get('DB_PORT', '5432')
}

def init_postgresql():
    """Initialiser PostgreSQL et insérer les radios"""
    try:
        print("🔌 Connexion à PostgreSQL...")
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
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
        
        # Vider la table
        cursor.execute("DELETE FROM radios")
        
        # Liste des radios à insérer
        radios = [
            ("RTL", "http://streaming.radio.rtl.fr/rtl-1-44-128"),
            ("Chante France-80s", "https://chantefrance80s.ice.infomaniak.ch/chantefrance80s-128.mp3"),
            ("100% Radio 80", "http://100radio-80.ice.infomaniak.ch/100radio-80-128.mp3"),
            ("Nostalgie 80", "https://scdn.nrjaudio.fm/fr/30601/mp3_128.mp3"),
            ("RFM 80-90", "http://rfm-live-mp3-128.scdn.arkena.com/rfm.mp3"),
            ("RTL2 80s", "http://streaming.radio.rtl2.fr/rtl2-1-44-128"),
            ("NRJ 80s", "https://scdn.nrjaudio.fm/fr/30601/mp3_128.mp3"),
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
        
        # Insérer les radios
        print(f"📻 Insertion de {len(radios)} radios...")
        for name, url in radios:
            cursor.execute("INSERT INTO radios (name, url) VALUES (%s, %s)", (name, url))
        
        conn.commit()
        
        # Vérifier l'insertion
        cursor.execute("SELECT COUNT(*) FROM radios")
        count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        print(f"✅ Base de données PostgreSQL initialisée avec {count} radios")
        print("📋 Liste des radios insérées:")
        for name, url in radios:
            print(f"   📻 {name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur initialisation PostgreSQL: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Initialisation PostgreSQL pour Ma Webradio")
    print("=" * 50)
    success = init_postgresql()
    
    if success:
        print("\n🎉 Base de données prête !")
        print("💡 L'application peut maintenant utiliser PostgreSQL")
    else:
        print("\n❌ Échec de l'initialisation")
