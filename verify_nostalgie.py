import psycopg
import os

os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_rOwco94kEyLS@ep-nameless-cloud-ahkuz006-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require'

conn = psycopg.connect(os.environ['DATABASE_URL'])
cursor = conn.cursor()

# Vérification finale
cursor.execute("SELECT name, url FROM radios WHERE name LIKE 'Nostalgie%' ORDER BY name")
radios = cursor.fetchall()

print('📊 URLs finales de Nostalgie:')
for name, url in radios:
    print(f'✅ {name}:')
    print(f'   {url}')

cursor.close()
conn.close()
