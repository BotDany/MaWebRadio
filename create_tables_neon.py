import psycopg
import os

# Forcer le DATABASE_URL de Neon
os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_rOwco94kEyLS@ep-nameless-cloud-ahkuz006-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require'

print('🔍 Création des tables dans Neon...')
print(f'DATABASE_URL: {os.environ["DATABASE_URL"][:50]}...')

try:
    # Connexion directe à Neon
    conn = psycopg.connect(os.environ['DATABASE_URL'])
    cursor = conn.cursor()
    
    print('✅ Connexion à Neon réussie!')
    
    # Créer la table radios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS radios (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) UNIQUE NOT NULL,
            url TEXT NOT NULL,
            logo TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print('✅ Table radios créée!')
    
    # Vérifier si la table est vide
    cursor.execute("SELECT COUNT(*) FROM radios")
    count = cursor.fetchone()[0]
    print(f'📊 Nombre de radios actuelles: {count}')
    
    if count == 0:
        print('📻 Insertion des radios par défaut...')
        
        # Radios par défaut
        default_radios = [
            ["RTL", "http://streaming.radio.rtl.fr/rtl-1-44-128", ""],
            ["Chante France-80s", "https://chantefrance80s.ice.infomaniak.ch/chantefrance80s-128.mp3", ""],
            ["100% Radio 80", "http://100radio-80.ice.infomaniak.ch/100radio-80-128.mp3", ""],
            ["RFM", "https://29043.live.streamtheworld.com/RFMAAC.aac?dist=triton-widget&tdsdk=js-2.9&swm=false&pname=tdwidgets&pversion=2.9&banners=300x250%2C728x90&gdpr=1&gdpr_consent=CQdTAsAQdTAsAAKA9APTCLFgAAAAAAAAAB6YAAAXsgLAA4AGaAZ8BHgCVQHbAQUAjSBIgCSgEowJkgUWAo4BVICrIFYAK5gV9AtWBbwC9gAA.IAAA.YAAAAAAAAAAA&burst-time=15", ""],
            ["Bide Et Musique", "https://relay1.bide-et-musique.com:9300/bm.mp3", "https://www.bide-et-musique.com/images/logo.png"],
            ["Flash 80 Radio", "https://manager7.streamradio.fr:1985/stream", ""],
            ["Mega Hits", "https://playerservices.streamtheworld.com/api/livestream-redirect/MEGA_HITSAAC_SC", ""],
            ["Radio Comercial", "https://stream-icy.bauermedia.pt/comercial.mp3", ""],
            ["Superloustic", "https://radio6.pro-fhi.net/live/SUPERLOUSTIC", ""],
            ["Génération Dorothée", "https://stream.votreradiosurlenet.eu/generationdorothee.mp3", ""],
            ["Top 80 Radio", "https://securestreams6.autopo.st:2321/", ""],
            ["Chansons Oubliées Où Presque", "https://manager7.streamradio.fr:2850/stream", ""],
            ["Générikds", "https://listen.radioking.com/radio/497599/stream/554719", ""],
            ["Nostalgie-Les 80 Plus Grand Tubes", "https://stream.nostalgie.fr/nostalgie-les-80-plus-grand-tubes?id=radio", ""],
            ["Nostalgie-Les Tubes 80 N1", "https://stream.nostalgie.fr/nostalgie-les-tubes-80-n1?id=radio", ""]
        ]
        
        # Insérer toutes les radios
        for name, url, logo in default_radios:
            cursor.execute("INSERT INTO radios (name, url, logo) VALUES (%s, %s, %s)", (name, url, logo))
        
        conn.commit()
        print(f'✅ {len(default_radios)} radios insérées!')
    
    # Vérification finale
    cursor.execute("SELECT COUNT(*) FROM radios")
    final_count = cursor.fetchone()[0]
    print(f'📊 Nombre final de radios: {final_count}')
    
    cursor.close()
    conn.close()
    
    print('🎉 Base de données Neon prête!')
    
except Exception as e:
    print(f'❌ Erreur: {e}')
    import traceback
    print(f'❌ Traceback: {traceback.format_exc()}')
