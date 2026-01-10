import psycopg
from psycopg.rows import dict_row

def get_db_connection():
    """Établir une connexion directe à la base de données Neon"""
    try:
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

def force_update_logos():
    """Forcer la mise à jour de tous les logos"""
    # Nouveaux logos
    NEW_LOGOS = {
        "100% Radio 80": "https://static.mytuner.mobi/media/tvos_radios/927/100-radio-80s.86b964dd.png",
        "Bide Et Musique": "https://www.radio.fr/300/bideetmusique.png?version=4933916e31ca4540ecc654651ece65a451b1b39c",
        "Chante France-80s": "https://i.ibb.co/0jQYJYv/generation-doree-logo.png",
        "Génération Dorothée": "https://i.ibb.co/0jQYJYv/generation-doree-logo.png",
        "Générikds": "https://i.ibb.co/0jQYJYv/generation-doree-logo.png",
        "Mega Hits": "https://i.ibb.co/0jQYJYv/generation-doree-logo.png",
        "Nostalgie-Les 80 Plus Grand Tubes": "https://i.ibb.co/0jQYJYv/generation-doree-logo.png",
        "Nostalgie-Les Tubes 80 N1": "https://i.ibb.co/0jQYJYv/generation-doree-logo.png",
        "RFM": "https://i.ibb.co/0jQYJYv/generation-doree-logo.png"
    }
    
    try:
        print("🔍 Connexion à la base de données...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Mettre à jour chaque radio avec son nouveau logo
        updated_count = 0
        for name, logo_url in NEW_LOGOS.items():
            try:
                # Forcer la mise à jour même si le logo est identique
                cursor.execute(
                    "UPDATE radios SET logo = %s WHERE name = %s",
                    (logo_url, name)
                )
                
                if cursor.rowcount > 0:
                    print(f"✅ Logo mis à jour pour {name}")
                    updated_count += 1
                else:
                    # Vérifier si la radio existe
                    cursor.execute("SELECT 1 FROM radios WHERE name = %s", (name,))
                    if cursor.fetchone():
                        print(f"ℹ️  Logo identique pour {name}")
                    else:
                        print(f"⚠️  Radio non trouvée: {name}")
                            
            except Exception as e:
                print(f"❌ Erreur lors de la mise à jour de {name}: {e}")
                conn.rollback()
                raise
        
        # Valider les modifications
        conn.commit()
        print(f"\n✅ {updated_count} logos mis à jour avec succès!")
        
        # Vérifier les mises à jour
        print("\n🔍 Vérification des mises à jour...")
        for name in NEW_LOGOS:
            cursor.execute("SELECT logo FROM radios WHERE name = %s", (name,))
            result = cursor.fetchone()
            if result:
                logo = result[0]
                print(f"📻 {name}: {logo[:50]}...")
            else:
                print(f"❌ {name}: non trouvée")
        
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour des logos: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        print("\n🔌 Déconnexion de la base de données")

if __name__ == "__main__":
    print("🔄 Démarrage de la mise à jour forcée des logos...\n")
    force_update_logos()
    print("\n✅ Mise à jour terminée")
