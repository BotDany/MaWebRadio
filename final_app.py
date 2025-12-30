from flask import Flask, render_template, jsonify, request, flash, redirect, url_for
import os
import json
from radio_metadata_fetcher_fixed_clean import RadioFetcher

class RadioState:
    def __init__(self):
        self.current_station = None
        self.current_url = None
        self.is_playing = False
        self.fetcher = RadioFetcher()

app = Flask(__name__)
app.secret_key = 'radio_admin_secret_key_2025'
radio_state = RadioState()

# Fichier de configuration pour les radios
RADIOS_FILE = 'radios_config.json'

def load_radios():
    """Charger la liste des radios depuis le fichier JSON"""
    try:
        if os.path.exists(RADIOS_FILE):
            with open(RADIOS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Liste par défaut si le fichier n'existe pas
            default_radios = [
                ("RTL", "http://streaming.radio.rtl.fr/rtl-1-44-128"),
                ("Chante France-80s", "https://chantefrance80s.ice.infomaniak.ch/chantefrance80s-128.mp3"),
                ("100% Radio 80", "http://100radio-80.ice.infomaniak.ch/100radio-80-128.mp3"),
                ("Nostalgie 80", "https://scdn.nrjaudio.fm/fr/30601/mp3_128.mp3"),
                ("RFM 80-90", "http://rfm-live-mp3-128.scdn.arkena.com/rfm.mp3"),
                ("RTL2 80s", "http://streaming.radio.rtl2.fr/rtl2-1-44-128"),
                ("NRJ 80s", "https://scdn.nrjaudio.fm/fr/30601/mp3_128.mp3"),
                ("Virgin Radio 80s", "https://ais-live.cloud-services.asso.fr/virginradio.mp3"),
                ("Bide Et Musique", "https://relay1.bide-et-musique.com:9300/bm.mp3"),
                ("Flash 80 Radio", "https://manager7.streamradio.fr:1985/stream"),
                ("Mega Hits", "https://playerservices.streamtheworld.com/api/livestream-redirect/MEGA_HITSAAC_SC"),
                ("Radio Comercial", "https://stream-icy.bauermedia.pt/comercial.mp3"),
                ("Superloustic", "https://radio6.pro-fhi.net/live/SUPERLOUSTIC"),
                ("Génération Dorothée", "https://stream.votreradiosurlenet.eu/generationdorothee.mp3"),
                ("Top 80 Radio", "https://securestreams6.autopo.st:2321/"),
                ("Chansons Oubliées Où Presque", "https://manager7.streamradio.fr:2850/stream"),
                ("Générikds", "https://listen.radioking.com/radio/49799/stream/554719"),
            ]
            save_radios(default_radios)
            return default_radios
    except Exception as e:
        print(f"Erreur chargement radios: {e}")
        return []

def save_radios(radios_list):
    """Sauvegarder la liste des radios dans le fichier JSON"""
    try:
        with open(RADIOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(radios_list, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Erreur sauvegarde radios: {e}")
        return False

# Liste des radios qui fonctionnent
RADIOS = [
    ("RTL", "http://streaming.radio.rtl.fr/rtl-1-44-128"),
    ("Chante France-80s", "https://chantefrance80s.ice.infomaniak.ch/chantefrance80s-128.mp3"),
    ("100% Radio 80", "http://100radio-80.ice.infomaniak.ch/100radio-80-128.mp3"),
    ("Nostalgie 80", "https://scdn.nrjaudio.fm/fr/30601/mp3_128.mp3"),
    ("RFM 80-90", "http://rfm-live-mp3-128.scdn.arkena.com/rfm.mp3"),
    ("RTL2 80s", "http://streaming.radio.rtl2.fr/rtl2-1-44-128"),
    ("NRJ 80s", "https://scdn.nrjaudio.fm/fr/30601/mp3_128.mp3"),
    ("Virgin Radio 80s", "https://ais-live.cloud-services.asso.fr/virginradio.mp3"),
    ("Bide Et Musique", "https://relay1.bide-et-musique.com:9300/bm.mp3"),
    ("Flash 80 Radio", "https://manager7.streamradio.fr:1985/stream"),
    ("Mega Hits", "https://playerservices.streamtheworld.com/api/livestream-redirect/MEGA_HITSAAC_SC"),
    ("Radio Comercial", "https://stream-icy.bauermedia.pt/comercial.mp3"),
    ("Superloustic", "https://radio6.pro-fhi.net/live/SUPERLOUSTIC"),
    ("Génération Dorothée", "https://stream.votreradiosurlenet.eu/generationdorothee.mp3"),
    ("Top 80 Radio", "https://securestreams6.autopo.st:2321/"),
    ("Chansons Oubliées Où Presque", "https://manager7.streamradio.fr:2850/stream"),
    ("Générikds", "https://listen.radioking.com/radio/49799/stream/554719"),
]

@app.route('/')
def index():
    radios = load_radios()
    return render_template('index.html', stations=radios)

@app.route('/api/metadata')
def metadata():
    print(f"🔍 API appelée - station: {radio_state.current_station}, playing: {radio_state.is_playing}")
    
    if radio_state.current_station and radio_state.current_url and radio_state.is_playing:
        try:
            # Utiliser le vrai fetcher pour obtenir les métadonnées
            print(f"🔍 Appel fetcher.get_metadata pour {radio_state.current_station}")
            
            # SOLUTION RAPIDE: Pour Générikds, utiliser l'API directement
            station_lower = radio_state.current_station.lower()
            print(f"🔍 Station en minuscules: '{station_lower}'")
            print(f"🔍 Contient 'generikids': {'generikids' in station_lower}")
            
            if "generikids" in station_lower:
                try:
                    api_url = "https://api.radioking.io/widget/radio/generikids/track/current"
                    response = requests.get(api_url, timeout=3)
                    
                    if response.status_code == 200:
                        data = response.json()
                        metadata = type('RadioMetadata', (), {
                            'artist': data.get('artist', radio_state.current_station),
                            'title': data.get('title', 'En direct'),
                            'cover_url': data.get('cover', ''),
                            'station': radio_state.current_station,
                            'host': ''
                        })()
                        print(f"🎵 API directe: {metadata.artist} - {metadata.title}")
                    else:
                        metadata = None
                except Exception as e:
                    print(f"❌ Erreur API directe: {e}")
                    metadata = None
            else:
                # Utiliser le fetcher normal pour les autres radios
                metadata = radio_state.fetcher.get_metadata(radio_state.current_station, radio_state.current_url)
            
            print(f"🔍 Résultat final: {metadata}")
            print(f"🔍 Type de metadata: {type(metadata)}")
            
            if metadata and metadata.title and metadata.title.lower() != "en direct":
                result = {
                    'status': 'success',
                    'artist': metadata.artist or radio_state.current_station,
                    'title': metadata.title,
                    'cover_url': metadata.cover_url or '',
                    'station': radio_state.current_station,
                    'is_playing': True
                }
                
                print(f"📤 API renvoie: {result}")
                return jsonify(result)
            else:
                # Si pas de métadonnées, renvoyer l'état actuel
                result = {
                    'status': 'no_data',
                    'artist': radio_state.current_station,
                    'title': 'En direct',
                    'cover_url': '',
                    'station': radio_state.current_station,
                    'is_playing': True
                }
                
                print(f"📤 API renvoie (no_metadata): {result}")
                return jsonify(result)
                
        except Exception as e:
            print(f"❌ Erreur métadonnées: {e}")
            # En cas d'erreur, renvoyer l'état actuel
            result = {
                'status': 'error',
                'artist': radio_state.current_station,
                'title': 'En direct',
                'cover_url': '',
                'station': radio_state.current_station,
                'is_playing': True
            }
            
            print(f"📤 API renvoie (error): {result}")
            return jsonify(result)
    
    result = {
        'status': 'no_data',
        'is_playing': False,
        'station': radio_state.current_station
    }
    
    print(f"📤 API renvoie (no_data): {result}")
    return jsonify(result)

@app.route('/api/play')
def play():
    station = request.args.get('station')
    url = request.args.get('url')
    
    if station and url:
        radio_state.current_station = station
        radio_state.current_url = url
        radio_state.is_playing = True
        print(f"▶️ Play: {station} - {url}")
        return jsonify({
            'status': 'playing',
            'station': station,
            'url': url
        })
    
    return jsonify({'status': 'error', 'message': 'Station manquante'})

@app.route('/api/stop')
def stop():
    station = radio_state.current_station
    radio_state.current_station = None
    radio_state.current_url = None
    radio_state.is_playing = False
    
    print(f"⏹️ Stop: {station}")
    return jsonify({'status': 'stopped'})

@app.route('/api/history')
def history():
    if not radio_state.current_station:
        return jsonify({'status': 'error', 'message': 'Aucune radio sélectionnée'})
    
    try:
        # Utiliser le fetcher pour obtenir l'historique
        history_data = radio_state.fetcher.get_history(radio_state.current_station, radio_state.current_url, 10)
        
        if history_data and len(history_data) > 0:
            result = {
                'status': 'success',
                'station': radio_state.current_station,
                'history': history_data
            }
        else:
            result = {
                'status': 'success',
                'station': radio_state.current_station,
                'history': [],
                'message': 'Aucun historique disponible pour cette radio'
            }
        
        print(f"📋 Historique: {len(history_data) if history_data else 0} chansons pour {radio_state.current_station}")
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Erreur historique: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Erreur: {str(e)}',
            'station': radio_state.current_station
        })

# Routes d'administration
@app.route('/admin')
def admin():
    """Panneau d'administration intégré"""
    radios = load_radios()
    return render_template('index.html', stations=radios, show_admin=True)

@app.route('/admin/add', methods=['POST'])
def add_radio():
    """Ajouter une nouvelle radio"""
    try:
        name = request.form.get('name', '').strip()
        url = request.form.get('url', '').strip()
        
        if not name or not url:
            flash('❌ Le nom et l\'URL sont obligatoires', 'error')
            return redirect(url_for('admin'))
        
        # Charger les radios existantes
        radios = load_radios()
        
        # Vérifier si la radio existe déjà
        for existing_name, existing_url in radios:
            if existing_name.lower() == name.lower():
                flash(f'❌ La radio "{name}" existe déjà', 'error')
                return redirect(url_for('admin'))
        
        # Ajouter la nouvelle radio
        radios.append((name, url))
        
        # Sauvegarder
        if save_radios(radios):
            flash(f'✅ Radio "{name}" ajoutée avec succès', 'success')
        else:
            flash('❌ Erreur lors de la sauvegarde', 'error')
            
    except Exception as e:
        flash(f'❌ Erreur: {str(e)}', 'error')
    
    return redirect(url_for('admin'))

@app.route('/admin/edit/<path:radio_name>', methods=['POST'])
@app.route('/admin/edit/<radio_name>', methods=['POST'])
def edit_radio(radio_name):
    """Modifier une radio existante"""
    try:
        # Décoder le nom de la radio (gère les deux cas: encodé et non encodé)
        import urllib.parse
        radio_name = urllib.parse.unquote(radio_name)
        
        new_name = request.form.get('name', '').strip()
        new_url = request.form.get('url', '').strip()
        
        if not new_name or not new_url:
            flash('❌ Le nom et l\'URL sont obligatoires', 'error')
            return redirect(url_for('admin'))
        
        # Charger les radios existantes
        radios = load_radios()
        
        # Trouver et modifier la radio
        updated_radios = []
        found = False
        for name, url in radios:
            if name == radio_name:
                updated_radios.append((new_name, new_url))
                found = True
            else:
                updated_radios.append((name, url))
        
        if not found:
            flash(f'❌ Radio "{radio_name}" non trouvée', 'error')
            return redirect(url_for('admin'))
        
        # Sauvegarder
        if save_radios(updated_radios):
            flash(f'✅ Radio "{radio_name}" modifiée avec succès', 'success')
        else:
            flash('❌ Erreur lors de la sauvegarde', 'error')
            
    except Exception as e:
        flash(f'❌ Erreur: {str(e)}', 'error')
    
    return redirect(url_for('admin'))

@app.route('/admin/delete/<path:radio_name>', methods=['POST'])
@app.route('/admin/delete/<radio_name>', methods=['POST'])
def delete_radio(radio_name):
    """Supprimer une radio"""
    try:
        # Décoder le nom de la radio (gère les deux cas: encodé et non encodé)
        import urllib.parse
        radio_name = urllib.parse.unquote(radio_name)
        
        # Charger les radios existantes
        radios = load_radios()
        
        # Filtrer pour supprimer la radio
        updated_radios = [(name, url) for name, url in radios if name != radio_name]
        
        if len(updated_radios) == len(radios):
            flash(f'❌ Radio "{radio_name}" non trouvée', 'error')
            return redirect(url_for('admin'))
        
        # Sauvegarder
        if save_radios(updated_radios):
            flash(f'✅ Radio "{radio_name}" supprimée avec succès', 'success')
        else:
            flash('❌ Erreur lors de la sauvegarde', 'error')
            
    except Exception as e:
        flash(f'❌ Erreur: {str(e)}', 'error')
    
    return redirect(url_for('admin'))

@app.route('/admin/test/<path:radio_name>')
@app.route('/admin/test/<radio_name>')
def test_radio(radio_name):
    """Tester une radio"""
    try:
        # Décoder le nom de la radio (gère les deux cas: encodé et non encodé)
        import urllib.parse
        radio_name = urllib.parse.unquote(radio_name)
        radios = load_radios()
        
        # Trouver l'URL de la radio
        radio_url = None
        for name, url in radios:
            if name == radio_name:
                radio_url = url
                break
        
        if not radio_url:
            return jsonify({
                'status': 'error',
                'message': f'Radio "{radio_name}" non trouvée'
            })
        
        # Tester les métadonnées
        fetcher = RadioFetcher()
        metadata = fetcher.get_metadata(radio_name, radio_url)
        
        if metadata:
            return jsonify({
                'status': 'success',
                'station': metadata.station,
                'artist': metadata.artist,
                'title': metadata.title,
                'cover_url': metadata.cover_url,
                'is_live': metadata.title.lower() != "en direct"
            })
        else:
            return jsonify({
                'status': 'no_data',
                'message': 'Aucune métadonnée disponible',
                'station': radio_name,
                'artist': radio_name,
                'title': 'En direct',
                'cover_url': ''
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Erreur: {str(e)}'
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    radios = load_radios()
    print(f"🚀 Application finale avec {len(radios)} radios démarrée sur le port {port}")
    app.run(host='0.0.0.0', port=port)
