import psycopg
import os

# Test de connexion à Neon avec logs détaillés
database_url = 'postgresql://neondb_owner:npg_rOwco94kEyLS@ep-nameless-cloud-ahkuz006-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require'
print('🔍 Test de connexion détaillé à Neon...')
print(f'DATABASE_URL: {database_url}')

try:
    print('📡 Tentative de connexion...')
    conn = psycopg.connect(database_url)
    print('✅ Connexion établie!')
    
    cursor = conn.cursor()
    
    # Test simple
    cursor.execute('SELECT version()')
    version = cursor.fetchone()
    print(f'📊 Version PostgreSQL: {version[0]}')
    
    # Vérifier table
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    tables = cursor.fetchall()
    print(f'📋 Tables: {tables}')
    
    # Vérifier radios
    cursor.execute('SELECT COUNT(*) FROM radios')
    count = cursor.fetchone()[0]
    print(f'📊 Nombre de radios: {count}')
    
    # Test d'insertion
    print('📝 Test d\'insertion...')
    cursor.execute("INSERT INTO radios (name, url, logo) VALUES (%s, %s, %s) ON CONFLICT (name) DO NOTHING", 
                   ('Test Radio', 'http://test.com', 'http://test.com/logo.png'))
    conn.commit()
    print('✅ Insertion test réussie!')
    
    # Vérifier l'insertion
    cursor.execute("SELECT name, url, logo FROM radios WHERE name = 'Test Radio'")
    test_radio = cursor.fetchone()
    print(f'📻 Radio test: {test_radio}')
    
    cursor.close()
    conn.close()
    print('✅ Test complet réussi!')
    
except Exception as e:
    print(f'❌ Erreur: {e}')
    import traceback
    print(f'❌ Traceback: {traceback.format_exc()}')
