import os
from database_config import get_db_connection

def check_radio_logos():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Vérifier si la colonne logo existe
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='radios' AND column_name='logo'
        """)
        has_logo_column = cursor.fetchone() is not None
        
        if not has_logo_column:
            print("❌ La colonne 'logo' n'existe pas dans la table 'radios'")
            return
            
        # Récupérer les données des radios
        cursor.execute("SELECT name, url, logo FROM radios ORDER BY name")
        radios = cursor.fetchall()
        
        if not radios:
            print("ℹ️ Aucune radio trouvée dans la base de données")
            return
            
        print(f"🔍 {len(radios)} radios trouvées dans la base de données")
        print("-" * 80)
        
        # Afficher les informations sur chaque radio
        for radio in radios:
            name, url, logo = radio
            logo_info = f"Logo: {logo[:50]}... ({len(logo)} caractères)" if logo else "Pas de logo"
            print(f"📻 {name}")
            print(f"   URL: {url}")
            print(f"   {logo_info}")
            print("-" * 80)
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des logos: {str(e)}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_radio_logos()
