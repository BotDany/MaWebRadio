# Configuration PostgreSQL pour les radios
import psycopg
import os
from psycopg.rows import dict_row

# Configuration de la base de données - Utilisation directe des identifiants
def get_db_config():
    """Récupérer la configuration PostgreSQL"""
    # Essayer DATABASE_URL d'abord (méthode Railway/Vercel)
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url and not '${' in database_url:
        # Parser DATABASE_URL
        import re
        match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', database_url)
        if match:
            print(f"🔌 DATABASE_URL: {match.group(3)}:{match.group(4)}")
            return {
                'host': match.group(3),
                'dbname': match.group(5),
                'user': match.group(1),
                'password': match.group(2),
                'port': int(match.group(4))
            }
    
    # Utiliser les identifiants fournis (fallback Vercel/Neon)
    print("🔌 Utilisation identifiants Neon pour Vercel")
    return {
        'host': os.environ.get('PGHOST', 'ep-nameless-cloud-ahkuz006-pooler.c-3.us-east-1.aws.neon.tech'),
        'dbname': os.environ.get('PGDATABASE', 'neondb'),
        'user': os.environ.get('PGUSER', 'neondb_owner'),
        'password': os.environ.get('PGPASSWORD', 'npg_rOwco94kEyLS'),
        'port': int(os.environ.get('PGPORT', '5432'))
    }

DB_CONFIG = get_db_config()

def get_db_connection():
    """Établir une connexion à la base de données PostgreSQL"""
    try:
        conn = psycopg.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Erreur de connexion à la base de données: {e}")
        return None

def load_radios():
    """Charger la liste des radios depuis PostgreSQL ou fallback immédiat"""
    try:
        # Timeout très court pour éviter le blocage au démarrage
        conn = psycopg.connect(**DB_CONFIG, connect_timeout=1)
        cursor = conn.cursor(row_factory=dict_row)
        
        # Essayer de charger avec logo, si erreur utiliser sans logo
        try:
            cursor.execute("SELECT name, url, logo FROM radios ORDER BY name")
            radios = cursor.fetchall()
        except:
            # Si la colonne logo n'existe pas, utiliser la structure sans logo
            cursor.execute("SELECT name, url FROM radios ORDER BY name")
            radios = cursor.fetchall()
            # Ajouter une colonne logo vide
            radios = [{'name': radio['name'], 'url': radio['url'], 'logo': ''} for radio in radios]
        
        cursor.close()
        conn.close()
        
        if not radios:
            print("⚠️ Aucune radio dans PostgreSQL, utilisation des radios par défaut")
            return get_default_radios()
        
        # Convertir en liste de listes pour compatibilité (toujours 3 éléments)
        result = []
        for radio in radios:
            if len(radio) >= 3:
                result.append([radio['name'], radio['url'], radio.get('logo', '')])
            elif len(radio) == 2:
                result.append([radio['name'], radio['url'], ''])
            else:
                # Format inattendu, créer avec logo vide
                result.append([str(radio), '', ''])
        return result
        
    except Exception as e:
        print(f"❌ Erreur chargement radios PostgreSQL: {e}")
        print("📻 Utilisation immédiate des radios par défaut")
        return get_default_radios()

def get_default_radios():
    """Retourner la liste des radios par défaut avec 3 éléments (name, url, logo)"""
    # Dictionnaire des logos par défaut pour chaque radio
    RADIO_LOGOS = {
        "100% Radio 80": "https://www.centpourcent.com/img/logo-100radio80.png",
        "Bide Et Musique": "https://www.bide-et-musique.com/wp-content/uploads/2021/05/logo-bm-2021.png",
        "Chansons Oubliées Où Presque": "https://www.radio.net/images/broadcasts/4b/6b/14164/1/c300.png",
        "Chante France-80s": "https://chantefrance80s.ice.infomaniak.ch/chantefrance80s-128.jpg",
        "Flash 80 Radio": "https://www.flash80.com/images/logo/2024/logo-flash80-2024.png",
        "Génération Dorothée": "https://generationdoree.fr/wp-content/uploads/2020/06/logo-generation-doree-2020.png",
        "Générikds": "https://www.radioking.com/api/v2/radio/play/logo/1b8d4f5f-9e5f-4f3d-8e5f-1b8d4f5f9e5f/300/300",
        "Made In 80": "https://www.madein80.com/wp-content/uploads/2021/05/logo-madein80-2021.png",
        "Mega Hits": "https://megahits.sapo.pt/wp-content/uploads/2020/06/logo-megahits.png",
        "Nostalgie-Les 80 Plus Grand Tubes": "https://cdn.nrjaudio.fm/radio/200/nostalgie-1.png",
        "Nostalgie-Les Tubes 80 N1": "https://cdn.nrjaudio.fm/radio/200/nostalgie-1.png",
        "Radio Comercial": "https://radiocomercial.pt/wp-content/uploads/2020/06/cropped-rc-favicon-192x192.png",
        "Radio Gérard": "https://radiosurle.net:8765/radiogerard/cover.jpg",
        "RFM": "https://images.rfm.pt/logo-rfm-1200x1200.png",
        "RFM Portugal": "https://images.rfm.pt/logo-rfm-1200x1200.png",
        "Rádio São Miguel": "https://www.radiosaomiguel.pt/images/logo-radiosaomiguel.png",
        "RTL": "https://www.rtl.fr/favicon-192x192.png",
        "Superloustic": "https://www.superloustic.com/wp-content/uploads/2021/09/logo-superloustic-2021.png",
        "Supernana": "https://www.generationdoree.fr/wp-content/uploads/2020/06/logo-generation-doree-2020.png",
        "Top 80 Radio": "https://www.top80radio.com/wp-content/uploads/2021/08/logo-top80-2021.png"
    }
    
    # Liste des radios avec leurs URLs et logos
    radios = [
        ["RTL", "http://streaming.radio.rtl.fr/rtl-1-44-128", RADIO_LOGOS.get("RTL", "")],
        ["Chante France-80s", "https://chantefrance80s.ice.infomaniak.ch/chantefrance80s-128.mp3", RADIO_LOGOS.get("Chante France-80s", "")],
        ["100% Radio 80", "http://100radio-80.ice.infomaniak.ch/100radio-80-128.mp3", RADIO_LOGOS.get("100% Radio 80", "")],
        ["RFM", "https://29043.live.streamtheworld.com/RFMAAC.aac?dist=triton-widget&tdsdk=js-2.9&swm=false&pname=tdwidgets&pversion=2.9&banners=300x250%2C728x90&gdpr=1&gdpr_consent=CQdTAsAQdTAsAAKA9APTCLFgAAAAAAAAAB6YAAAXsgLAA4AGaAZ8BHgCVQHbAQUAjSBIgCSgEowJkgUWAo4BVICrIFYAK5gV9AtWBbwC9gAA.IAAA.YAAAAAAAAAAA&burst-time=15", RADIO_LOGOS.get("RFM", "")],
        ["Bide Et Musique", "https://relay1.bide-et-musique.com:9300/bm.mp3", RADIO_LOGOS.get("Bide Et Musique", "")],
        ["Flash 80 Radio", "https://manager7.streamradio.fr:1985/stream", RADIO_LOGOS.get("Flash 80 Radio", "")],
        ["Mega Hits", "https://playerservices.streamtheworld.com/api/livestream-redirect/MEGA_HITSAAC_SC", RADIO_LOGOS.get("Mega Hits", "")],
        ["Radio Comercial", "https://stream-icy.bauermedia.pt/comercial.mp3", RADIO_LOGOS.get("Radio Comercial", "")],
        ["Superloustic", "https://radio6.pro-fhi.net/radio/9004/stream", RADIO_LOGOS.get("Superloustic", "")],
        ["Génération Dorothée", "https://stream.votreradiosurlenet.eu/generationdorothee.mp3", RADIO_LOGOS.get("Génération Dorothée", "")],
        ["Top 80 Radio", "https://securestreams6.autopo.st:2321/", RADIO_LOGOS.get("Top 80 Radio", "")],
        ["Chansons Oubliées Où Presque", "https://manager7.streamradio.fr:2850/stream", RADIO_LOGOS.get("Chansons Oubliées Où Presque", "")],
        ["Générikds", "https://listen.radioking.com/radio/497599/stream/554719", RADIO_LOGOS.get("Générikds", "")],
        ["Nostalgie-Les 80 Plus Grand Tubes", "https://streaming.nrjaudio.fm/ouwg8usk6j4d?origine=radio.net&aw_0_1st.station=Nostalgie-Les-80-Plus-Grands-Tubes-80", RADIO_LOGOS.get("Nostalgie-Les 80 Plus Grand Tubes", "")],
        ["Nostalgie-Les Tubes 80 N1", "https://streaming.nrjaudio.fm/ouo6im7nfibk?origine=radio.net&aw_0_1st.station=Nostalgie-80-Les-Tubes-N-1", RADIO_LOGOS.get("Nostalgie-Les Tubes 80 N1", "")]
    ]
    
    return radios

def save_radios(radios):
    """Sauvegarder la liste des radios dans PostgreSQL - Version radicale"""
    try:
        print(f"🔍 save_radios: Début sauvegarde de {len(radios)} radios")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Approche radicale : recréer complètement la table
        try:
            # Supprimer la table existante
            cursor.execute("DROP TABLE IF EXISTS radios")
            print("🗑️ save_radios: Table radios supprimée")
            
            # Recréer la table avec la bonne structure
            cursor.execute("""
                CREATE TABLE radios (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) UNIQUE NOT NULL,
                    url TEXT NOT NULL,
                    logo TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ save_radios: Table radios recréée")
            
            # Insérer toutes les radios
            for i, radio in enumerate(radios):
                print(f"🔍 save_radios: Traitement radio {i}: {radio}")
                if len(radio) >= 3:
                    name, url, logo = radio[0], radio[1], radio[2]
                    print(f"📝 save_radios: Radio avec logo: {name}, {url}, {logo}")
                else:
                    name, url = radio[0], radio[1]
                    logo = ''
                    print(f"📝 save_radios: Radio sans logo: {name}, {url}")
                
                cursor.execute("""
                    INSERT INTO radios (name, url, logo) 
                    VALUES (%s, %s, %s)
                """, [name, url, logo])
                print(f"✅ save_radios: Radio {name} insérée")
            
            # Commit
            conn.commit()
            print(f"💾 save_radios: Commit effectué")
            
        except Exception as e:
            # Rollback en cas d'erreur
            conn.rollback()
            print(f"❌ save_radios: Rollback effectué: {e}")
            raise e
            
        finally:
            cursor.close()
            conn.close()
        
        print(f"✅ {len(radios)} radios sauvegardées dans PostgreSQL")
        return True
        
    except Exception as e:
        print(f"❌ Erreur sauvegarde radios PostgreSQL: {e}")
        import traceback
        print(f"❌ Traceback save_radios: {traceback.format_exc()}")
        return False

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
            print("📻 Table vide, insertion automatique des radios par défaut...")
            
            # Utiliser la même liste que get_default_radios()
            default_radios = get_default_radios()
            
            # Insérer toutes les radios avec logo vide par défaut
            for radio in default_radios:
                if len(radio) >= 3:
                    name, url, logo = radio[0], radio[1], radio[2]
                else:
                    name, url = radio[0], radio[1]
                    logo = ''
                cursor.execute("INSERT INTO radios (name, url, logo) VALUES (%s, %s, %s)", (name, url, logo))
            
            conn.commit()
            print(f"✅ {len(default_radios)} radios insérées automatiquement !")
        else:
            print(f"✅ {count} radios déjà présentes, mise à jour avec la nouvelle liste...")
            
            # Vider la table et réinsérer avec la nouvelle liste
            cursor.execute("DELETE FROM radios")
            
            # Utiliser la même liste que get_default_radios()
            default_radios = get_default_radios()
            
            # Insérer toutes les radios avec logo vide par défaut
            for radio in default_radios:
                if len(radio) >= 3:
                    name, url, logo = radio[0], radio[1], radio[2]
                else:
                    name, url = radio[0], radio[1]
                    logo = ''
                cursor.execute("INSERT INTO radios (name, url, logo) VALUES (%s, %s, %s)", (name, url, logo))
            
            conn.commit()
            print(f"✅ {len(default_radios)} radios mises à jour avec la nouvelle liste !")
        
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
