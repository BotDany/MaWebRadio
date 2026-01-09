import psycopg
import os

# Configuration Neon
os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_rOwco94kEyLS@ep-nameless-cloud-ahkuz006-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require'

# Importer les fonctions de database_config
from database_config import get_db_connection, load_radios, save_radios

print('🔍 Test de edit_radio avec Neon...')

try:
    # 1. Charger les radios existantes
    print('📡 Étape 1: Chargement des radios...')
    radios = load_radios()
    print(f'📊 {len(radios)} radios chargées')
    
    # 2. Trouver "Chansons Oubliées Où Presque"
    print('🔍 Étape 2: Recherche de la radio...')
    radio_index = -1
    for i, radio in enumerate(radios):
        if radio[0] == 'Chansons Oubliées Où Presque':
            radio_index = i
            print(f'✅ Radio trouvée à l\'index {i}: {radio}')
            break
    
    if radio_index == -1:
        print('❌ Radio non trouvée')
        exit()
    
    # 3. Modifier la radio
    print('📝 Étape 3: Modification de la radio...')
    new_logo = 'https://static.mytuner.mobi/media/tvos_radios/490/chansons-oubliees-ou-presque.0afbdb09.png'
    radios[radio_index] = ['Chansons Oubliées Où Presque', 'https://manager7.streamradio.fr:2850/stream', new_logo]
    print(f'📝 Radio modifiée: {radios[radio_index]}')
    
    # 4. Sauvegarder dans Neon
    print('💾 Étape 4: Sauvegarde dans Neon...')
    success = save_radios(radios)
    
    if success:
        print('✅ Sauvegarde réussie!')
        
        # 5. Vérification
        print('🔍 Étape 5: Vérification...')
        updated_radios = load_radios()
        for radio in updated_radios:
            if radio[0] == 'Chansons Oubliées Où Presque':
                print(f'✅ Radio vérifiée: {radio}')
                print(f'🎯 Logo final: {radio[2]}')
                break
        
        print('🎉 Test edit_radio avec Neon réussi!')
    else:
        print('❌ Erreur lors de la sauvegarde')
        
except Exception as e:
    print(f'❌ Erreur: {e}')
    import traceback
    print(f'❌ Traceback: {traceback.format_exc()}')
