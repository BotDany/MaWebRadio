import psycopg
from psycopg.rows import dict_row

def get_db_connection():
    """Établir une connexion directe à la base de données Neon"""
    try:
        # Configuration directe pour Neon
        conn = psycopg.connect(
            host="ep-nameless-cloud-ahkuz006-pooler.c-3.us-east-1.aws.neon.tech",
            dbname="neondb",
            user="neondb_owner",
            password="npg_rOwco94kEyLS",
            port=5432,
            sslmode="require"
        )
        return conn
    except Exception as e:
        print(f"❌ Erreur de connexion à la base de données: {e}")
        raise

def check_database():
    """Vérifier l'état de la base de données"""
    try:
        print("🔍 Connexion à la base de données...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Vérifier les tables existantes
        print("\n📋 Tables dans la base de données:")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        for table in cursor.fetchall():
            print(f"- {table[0]}")
        
        # Vérifier la structure de la table radios
        print("\n🔍 Structure de la table 'radios':")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'radios'
        """)
        print("Colonnes dans la table 'radios':")
        for col in cursor.fetchall():
            print(f"- {col[0]} ({col[1]}, nullable: {col[2]})")
        
        # Vérifier les données actuelles
        print("\n📊 Données actuelles dans la table 'radios':")
        cursor.execute("SELECT name, url, logo FROM radios ORDER BY name")
        radios = cursor.fetchall()
        
        if not radios:
            print("Aucune radio trouvée dans la base de données.")
        else:
            print(f"{len(radios)} radios trouvées:")
            for radio in radios:
                name, url, logo = radio
                logo_info = f"Logo: {logo[:50]}... ({len(logo)} caractères)" if logo else "Pas de logo"
                print(f"\n📻 {name}")
                print(f"   URL: {url}")
                print(f"   {logo_info}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification de la base de données: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        print("\n🔌 Déconnexion de la base de données")

if __name__ == "__main__":
    print("🔍 Démarrage du diagnostic de la base de données...\n")
    check_database()
    print("\n✅ Diagnostic terminé")
