import psycopg
import os

# Test simple de connexion Neon
database_url = 'postgresql://neondb_owner:npg_rOwco94kEyLS@ep-nameless-cloud-ahkuz006-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require'
print('🔍 Test simple de connexion Neon...')

try:
    conn = psycopg.connect(database_url)
    cursor = conn.cursor()
    
    # Test simple
    cursor.execute('SELECT 1')
    result = cursor.fetchone()
    print(f'✅ Test simple réussi: {result}')
    
    # Test d'insertion simple
    cursor.execute('CREATE TABLE IF NOT EXISTS test_table (id SERIAL PRIMARY KEY, name TEXT)')
    cursor.execute('INSERT INTO test_table (name) VALUES (%s)', ('test'))
    conn.commit()
    print('✅ Insertion simple réussie')
    
    # Vérification
    cursor.execute('SELECT COUNT(*) FROM test_table')
    count = cursor.fetchone()[0]
    print(f'✅ Vérification réussie: {count} enregistrements')
    
    # Nettoyage
    cursor.execute('DROP TABLE IF EXISTS test_table')
    conn.commit()
    
    cursor.close()
    conn.close()
    print('✅ Test simple terminé avec succès!')
    
except Exception as e:
    print(f'❌ Erreur: {e}')
    import traceback
    print(f'❌ Traceback: {traceback.format_exc()}')
