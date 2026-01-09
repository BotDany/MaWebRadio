import psycopg

# Test de connexion à Neon
database_url = 'postgresql://neondb_owner:npg_rOwco94kEyLS@ep-nameless-cloud-ahkuz006-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require'
print('🔍 Test de connexion à Neon...')
print(f'DATABASE_URL: {database_url[:50]}...')

try:
    conn = psycopg.connect(database_url)
    cursor = conn.cursor()
    
    # Vérifier si la table radios existe
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'radios'")
    tables = cursor.fetchall()
    print(f'📋 Tables trouvées: {tables}')
    
    if tables:
        # Vérifier les colonnes
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'radios' AND table_schema = 'public'")
        columns = cursor.fetchall()
        print(f'📋 Colonnes dans radios: {columns}')
        
        # Compter les radios
        cursor.execute("SELECT COUNT(*) FROM radios")
        count = cursor.fetchone()[0]
        print(f'📊 Nombre de radios: {count}')
        
        # Afficher quelques radios
        cursor.execute("SELECT name, url, logo FROM radios LIMIT 3")
        radios = cursor.fetchall()
        print(f'📻 Exemples de radios: {radios}')
    else:
        print('📋 Table radios non trouvée')
    
    cursor.close()
    conn.close()
    print('✅ Connexion Neon réussie!')
    
except Exception as e:
    print(f'❌ Erreur connexion Neon: {e}')
