import psycopg
import os

# Configuration Neon
os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_rOwco94kEyLS@ep-nameless-cloud-ahkuz006-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require'

# Importer les fonctions de database_config
from database_config import init_database, get_db_connection

print('🔍 Initialisation de la base de données Neon...')

try:
    # Test de connexion
    conn = get_db_connection()
    if conn:
        print('✅ Connexion Neon réussie!')
        
        # Initialiser la base de données
        success = init_database()
        if success:
            print('✅ Base de données Neon initialisée avec succès!')
            
            # Vérifier la table
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM radios")
            count = cursor.fetchone()[0]
            print(f'📊 Nombre de radios insérées: {count}')
            
            # Afficher quelques radios
            cursor.execute("SELECT name, url, logo FROM radios LIMIT 3")
            radios = cursor.fetchall()
            print(f'📻 Exemples de radios: {radios}')
            
            cursor.close()
        else:
            print('❌ Erreur lors de l\'initialisation')
        
        conn.close()
    else:
        print('❌ Erreur de connexion')
        
except Exception as e:
    print(f'❌ Erreur: {e}')
