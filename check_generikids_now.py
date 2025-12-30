import requests
import json

# API pour les métadonnées en temps réel de Générikds
api_url = 'https://api.radioking.io/widget/radio/generikids/track/current'

print('🎵 CE QUI PASSE SUR GÉNÉRIKDS EN CE MOMENT')
print('=' * 50)

try:
    response = requests.get(api_url, timeout=5)
    if response.status_code == 200:
        data = response.json()
        
        print('📻 RADIO:', 'Générikds')
        print('🎤 ARTISTE:', data.get('artist', 'Non disponible'))
        print('🎵 TITRE:', data.get('title', 'Non disponible'))
        print('💿 ALBUM:', data.get('album', 'Non disponible'))
        print('⏱️ DURÉE:', f"{data.get('duration', 0):.1f} secondes" if data.get('duration') else 'Non disponible')
        print('🕐 DÉBUT:', data.get('started_at', 'Non disponible'))
        print('🕐 FIN:', data.get('end_at', 'Non disponible'))
        print('🎙️ EN DIRECT:', 'Oui' if data.get('is_live') else 'Non')
        print('🖼️ COVER:', data.get('cover', 'Non disponible'))
        
        if data.get('buy_link'):
            print('🛒 ACHAT:', data.get('buy_link'))
        else:
            print('🛒 ACHAT: Non disponible')
            
    else:
        print(f'❌ Erreur API: {response.status_code}')
        
except Exception as e:
    print(f'❌ Erreur: {e}')

print()
print('✅ Métadonnées temps réel récupérées avec succès !')
