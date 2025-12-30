#!/usr/bin/env python3
"""
Script pour créer les tables et insérer les radios dans le nouveau PostgreSQL
"""

import psycopg
import os

# Configuration du nouveau PostgreSQL - Utilise les variables externes Railway
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'trolley.proxy.rlwy.net'),
    'dbname': os.environ.get('DB_NAME', 'railway'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', 'LwAVoXBRvbvKpZKDLVBojSQXqFzNGeoe'),
    'port': os.environ.get('DB_PORT', '27920')
}

def setup_database():
    """Créer la table et insérer les radios par défaut"""
    try:
        print("🔌 Connexion à PostgreSQL...")
        conn = psycopg.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Créer la table des radios
        print("📋 Création de la table radios...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS radios (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Vérifier si la table est vide
        cursor.execute("SELECT COUNT(*) as count FROM radios")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("📻 Insertion des 15 radios par défaut...")
            
            # Liste complète des radios
            radios = [
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
            for name, url in radios:
                cursor.execute("INSERT INTO radios (name, url) VALUES (%s, %s)", (name, url))
            
            conn.commit()
            print(f"✅ {len(radios)} radios insérées avec succès !")
        else:
            print(f"✅ La table contient déjà {count} radios")
        
        # Vérifier le contenu
        cursor.execute("SELECT name, url FROM radios ORDER BY name")
        all_radios = cursor.fetchall()
        
        print("\n📋 Radios dans la base de données :")
        for radio in all_radios:
            print(f"   🎵 {radio[0]}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Configuration PostgreSQL terminée !")
        print("🌐 Rafraîchissez votre application Railway pour voir les radios")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Configuration PostgreSQL pour Ma Webradio")
    print("=" * 50)
    print("⚠️  Assurez-vous d'avoir configuré les variables d'environnement")
    print("⚠️  Ou modifiez DB_CONFIG dans ce script")
    print("=" * 50)
    
    setup_database()
