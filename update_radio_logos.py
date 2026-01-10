import psycopg
from database_config import get_db_connection

def update_radio_logos():
    """Met à jour les logos des radios dans la base de données"""
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
    
    try:
        print("🔍 Connexion à la base de données...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Mettre à jour chaque radio avec son logo
        updated_count = 0
        for name, logo_url in RADIO_LOGOS.items():
            try:
                cursor.execute(
                    "UPDATE radios SET logo = %s WHERE name = %s AND (logo IS NULL OR logo = '' OR logo != %s)",
                    (logo_url, name, logo_url)
                )
                if cursor.rowcount > 0:
                    print(f"✅ Logo mis à jour pour {name}")
                    updated_count += 1
                else:
                    # Vérifier si la radio existe
                    cursor.execute("SELECT 1 FROM radios WHERE name = %s", (name,))
                    if cursor.fetchone():
                        print(f"ℹ️  Logo déjà à jour pour {name}")
                    else:
                        print(f"⚠️  Radio non trouvée: {name}")
            except Exception as e:
                print(f"❌ Erreur lors de la mise à jour de {name}: {e}")
        
        conn.commit()
        print(f"\n✅ {updated_count} logos mis à jour avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour des logos: {e}")
        if conn:
            conn.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        print("🔌 Déconnexion de la base de données")

if __name__ == "__main__":
    print("🔄 Début de la mise à jour des logos des radios...\n")
    update_radio_logos()
    print("\n✅ Mise à jour des logos terminée")
