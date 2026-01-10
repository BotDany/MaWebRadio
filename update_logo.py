import psycopg
from database_config import get_db_config

def update_logo():
    config = get_db_config()
    try:
        with psycopg.connect(**config) as conn:
            with conn.cursor() as cur:
                # Mettre à jour le logo de Génération Dorothée
                cur.execute(
                    """
                    UPDATE radios 
                    SET logo = %s 
                    WHERE name = %s
                    """,
                    ("https://www.radio.net/images/broadcasts/7b/6f/11125/c300.png", "Génération Dorothée")
                )
                print("✅ Logo mis à jour pour Génération Dorothée")
                
                # Vérifier la mise à jour
                cur.execute("SELECT name, logo FROM radios WHERE name = %s", ("Génération Dorothée",))
                result = cur.fetchone()
                if result:
                    print(f"Vérification - Nom: {result[0]}, Logo: {result[1]}")
                else:
                    print("❌ La radio n'a pas été trouvée dans la base de données")
                
                conn.commit()
                
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour: {e}")

if __name__ == "__main__":
    update_logo()
