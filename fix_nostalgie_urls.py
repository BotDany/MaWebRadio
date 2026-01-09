import psycopg
import os

# Configuration Neon
os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_rOwco94kEyLS@ep-nameless-cloud-ahkuz006-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require'

# URLs correctes pour Nostalgie
nostalgie_urls = {
    "Nostalgie-Les 80 Plus Grand Tubes": "https://stream.nostalgie.fr/nostalgie-les-80-plus-grand-tubes?id=radio",
    "Nostalgie-Les Tubes 80 N1": "https://scdn.nrjaudio.fm/adwv1/ps/46633/mp3_128.mp3?origine=fluxradios&awparams=platform:web;player:triton;player_version:5.31.0"
}

print('🔍 Correction des URLs Nostalgie dans Neon...')

try:
    conn = psycopg.connect(os.environ['DATABASE_URL'])
    cursor = conn.cursor()
    
    # Vérifier les URLs actuelles
    cursor.execute("SELECT name, url FROM radios WHERE name LIKE 'Nostalgie%'")
    current_radios = cursor.fetchall()
    
    print('📊 URLs actuelles de Nostalgie:')
    for name, url in current_radios:
        print(f'   - {name}: {url}')
    
    # Mettre à jour les URLs
    for station_name, correct_url in nostalgie_urls.items():
        print(f'📝 Mise à jour de {station_name}: {correct_url}')
        
        cursor.execute("""
            UPDATE radios 
            SET url = %s 
            WHERE name = %s
        """, [correct_url, station_name])
        
        if cursor.rowcount > 0:
            print(f'✅ {station_name} mis à jour')
        else:
            print(f'❌ {station_name} non trouvé')
    
    conn.commit()
    
    # Vérification finale
    cursor.execute("SELECT name, url FROM radios WHERE name LIKE 'Nostalgie%'")
    updated_radios = cursor.fetchall()
    
    print('📊 URLs finales de Nostalgie:')
    for name, url in updated_radios:
        print(f'   - {name}: {url}')
    
    cursor.close()
    conn.close()
    
    print('🎉 URLs Nostalgie corrigées avec succès!')
    
except Exception as e:
    print(f'❌ Erreur: {e}')
    import traceback
    print(f'❌ Traceback: {traceback.format_exc()}')
