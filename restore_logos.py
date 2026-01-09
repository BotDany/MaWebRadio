import psycopg
import os

# Configuration Neon
os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_rOwco94kEyLS@ep-nameless-cloud-ahkuz006-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require'

# Logos à restaurer
logos_to_restore = {
    "RTL": "https://www.rtl.fr/medias/radio/logo-rtl-2018-rectangle-850x480.jpg",
    "Chante France-80s": "https://www.chante.fr/src/assets/logo-dovendi.png",
    "100% Radio 80": "https://medias.lesindesradios.fr/t:app(web)/t:r(98lIT4zPKC)/fit-in/300x2000/filters:format(webp)/radios/centpourcent/radiostream/sz9KS9uVGI/vignette_eePvE5Vu1o.png",
    "RFM": "https://cdn-icons-png.flaticon.com/512/2965/2965274.png",
    "Flash 80 Radio": "https://www.flash80.com/images/logo/2024/logo-flash80-2024.png",
    "Mega Hits": "https://megasite-images.azureedge.net/images/webradios/logo-megahits-w-xl.svg",
    "Radio Comercial": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRPakNfQWw2DLir11Y47PSQUw2qGJj_OSuxmw&s",
    "Superloustic": "https://www.liveradio.ie/files/images/361213/resized/180x172c/logosl.jpg",
    "Génération Dorothée": "https://cdn-icons-png.flaticon.com/512/2965/2965274.png",
    "Top 80 Radio": "https://www.top80radio.com/wp-content/uploads/2023/09/Logo-carre-transparent-1000.png",
    "Chansons Oubliées Où Presque": "https://static.wixstatic.com/media/d6936f_f558dd3a9c0c4807a1cdf71a0e329e54~mv2.png/v1/fill/w_497,h_497,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/Capture%20d'%C3%A9cran%202024-04-16%20212006.png",
    "Générikds": "https://cdn-icons-png.flaticon.com/512/2965/2965274.png",
    "Nostalgie-Les 80 Plus Grand Tubes": "https://players.nrjaudio.fm/live-metadata/player/img/player-files/nosta/logos/173x173/NOSTA_WR_BEST-OF-80.jpg",
    "Nostalgie-Les Tubes 80 N1": "https://players.nrjaudio.fm/live-metadata/player/img/player-files/nosta/logos/173x173/NOSTA_WR_MINI-MIX.jpg"
}

print('🔍 Restauration des logos dans Neon...')

try:
    conn = psycopg.connect(os.environ['DATABASE_URL'])
    cursor = conn.cursor()
    
    restored_count = 0
    
    for station_name, logo_url in logos_to_restore.items():
        print(f'📝 Restauration de {station_name}: {logo_url}')
        
        cursor.execute("""
            UPDATE radios 
            SET logo = %s 
            WHERE name = %s
        """, [logo_url, station_name])
        
        if cursor.rowcount > 0:
            restored_count += 1
            print(f'✅ {station_name} restauré')
        else:
            print(f'❌ {station_name} non trouvé')
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f'🎉 {restored_count} logos restaurés avec succès!')
    
except Exception as e:
    print(f'❌ Erreur: {e}')
    import traceback
    print(f'❌ Traceback: {traceback.format_exc()}')
