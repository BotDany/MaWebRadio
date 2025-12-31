#!/usr/bin/env python3
"""
Script pour ajouter RFM à la base de données PostgreSQL
"""

import psycopg
from database_config import get_db_connection, load_radios, save_radios

def add_rfm_to_postgres():
    """Ajouter RFM à la base de données PostgreSQL"""
    try:
        print("🔌 Connexion à PostgreSQL...")
        conn = get_db_connection()
        if conn is None:
            print("❌ Impossible de se connecter à PostgreSQL")
            return False
        
        cursor = conn.cursor()
        
        # Vérifier si RFM existe déjà
        cursor.execute("SELECT * FROM radios WHERE name = %s", ("RFM",))
        existing = cursor.fetchone()
        
        if existing:
            print("✅ RFM existe déjà dans PostgreSQL")
            print(f"   Nom: {existing[1]}")
            print(f"   URL: {existing[2]}")
        else:
            # Ajouter RFM
            rfm_url = "https://29043.live.streamtheworld.com/RFMAAC.aac?dist=triton-widget&tdsdk=js-2.9&swm=false&pname=tdwidgets&pversion=2.9&banners=300x250%2C728x90&gdpr=1&gdpr_consent=CQdTAsAQdTAsAAKA9APTCLFgAAAAAAAAAB6YAAAXsgLAA4AGaAZ8BHgCVQHbAQUAjSBIgCSgEowJkgUWAo4BVICrIFYAK5gV9AtWBbwC9gAA.IAAA.YAAAAAAAAAAA&burst-time=15"
            cursor.execute("INSERT INTO radios (name, url) VALUES (%s, %s)", ("RFM", rfm_url))
            conn.commit()
            print("✅ RFM ajoutée à PostgreSQL")
        
        # Afficher toutes les radios
        cursor.execute("SELECT name, url FROM radios ORDER BY name")
        radios = cursor.fetchall()
        
        print(f"\n📻 Liste des radios dans PostgreSQL ({len(radios)}):")
        for name, url in radios:
            print(f"   • {name}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    print("📻 Ajout de RFM à PostgreSQL...")
    success = add_rfm_to_postgres()
    
    if success:
        print("\n✅ Opération terminée avec succès!")
    else:
        print("\n❌ Erreur lors de l'opération")
