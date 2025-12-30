import json
import os
import time
from flask import Flask, render_template, jsonify, request, flash, redirect, url_for
from radio_metadata_fetcher_fixed_clean import RadioFetcher
from database_config import load_radios, save_radios

class RadioState:
    def __init__(self):
        self.current_station = None
        self.current_url = None
        self.is_playing = False
        self.fetcher = RadioFetcher()

app = Flask(__name__)
app.secret_key = 'radio_admin_secret_key_2025'
radio_state = RadioState()

print("🚀 Démarrage de l'application webradio...")

@app.route('/')
def index():
    radios = load_radios()
    return render_template('index.html', stations=radios)

@app.route('/api/metadata')
def metadata():
    import requests
    print(f"🔍 API appelée - station: {radio_state.current_station}, playing: {radio_state.is_playing}")
    
    if radio_state.current_station and radio_state.current_url and radio_state.is_playing:
        try:
            station_lower = radio_state.current_station.lower()
            
            if "generikids" in station_lower or "générikds" in station_lower:
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
                metadata = radio_state.fetcher.get_metadata(radio_state.current_station, radio_state.current_url)
            
            if metadata and metadata.title and metadata.title.lower() != "en direct":
                result = {
                    'status': 'success',
                    'artist': metadata.artist or radio_state.current_station,
                    'title': metadata.title,
                    'cover_url': metadata.cover_url or '',
                    'station': radio_state.current_station,
                    'is_playing': True
                }
                return jsonify(result)
            else:
                result = {
                    'status': 'no_data',
                    'artist': radio_state.current_station,
                    'title': 'En direct',
                    'cover_url': '',
                    'station': radio_state.current_station,
                    'is_playing': True
                }
                return jsonify(result)
        except Exception as e:
            result = {
                'status': 'error',
                'artist': radio_state.current_station,
                'title': 'En direct',
                'cover_url': '',
                'station': radio_state.current_station,
                'is_playing': True
            }
            return jsonify(result)
    
    result = {
        'status': 'no_data',
        'is_playing': False,
        'station': radio_state.current_station
    }
    return jsonify(result)

@app.route('/api/play')
def play():
    station = request.args.get('station')
    url = request.args.get('url')
    
    if station and url:
        radio_state.current_station = station
        radio_state.current_url = url
        radio_state.is_playing = True
        print(f"▶️ Play: {station}")
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

# Routes d'administration
@app.route('/admin')
def admin():
    """Page d'administration des radios"""
    radios = load_radios()
    return render_template('admin.html', stations=radios)

@app.route('/admin/add', methods=['POST'])
def add_radio():
    """Ajouter une nouvelle radio"""
    name = request.form.get('name')
    url = request.form.get('url')
    
    if name and url:
        radios = load_radios()
        radios.append([name, url])
        
        if save_radios(radios):
            flash(f'Radio "{name}" ajoutée avec succès!', 'success')
        else:
            flash(f'Erreur lors de l\'ajout de la radio "{name}"', 'error')
    else:
        flash('Veuillez remplir tous les champs', 'error')
    
    return redirect(url_for('admin'))

@app.route('/admin/edit/<path:radio_name>', methods=['POST'])
@app.route('/admin/edit/<radio_name>', methods=['POST'])
def edit_radio(radio_name):
    """Modifier une radio existante"""
    try:
        # Décoder le nom de la radio (gère les deux cas: encodé et non encodé)
        import urllib.parse
        radio_name = urllib.parse.unquote(radio_name)
        
        # Charger les radios existantes
        radios = load_radios()
        
        # Trouver la radio à modifier
        for i, (name, url) in enumerate(radios):
            if name == radio_name:
                new_url = request.form.get('url')
                if new_url:
                    radios[i] = [name, new_url]
                    
                    if save_radios(radios):
                        flash(f'Radio "{name}" modifiée avec succès!', 'success')
                    else:
                        flash(f'Erreur lors de la modification de la radio "{name}"', 'error')
                break
        else:
            flash(f'Radio "{radio_name}" non trouvée', 'error')
            
    except Exception as e:
        flash(f'Erreur lors de la modification: {str(e)}', 'error')
    
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
        
        if len(updated_radios) < len(radios):
            if save_radios(updated_radios):
                flash(f'Radio "{radio_name}" supprimée avec succès!', 'success')
            else:
                flash(f'Erreur lors de la suppression de la radio "{radio_name}"', 'error')
        else:
            flash(f'Radio "{radio_name}" non trouvée', 'error')
            
    except Exception as e:
        flash(f'Erreur lors de la suppression: {str(e)}', 'error')
    
    return redirect(url_for('admin'))

@app.route('/admin/test/<path:radio_name>')
@app.route('/admin/test/<radio_name>')
def test_radio(radio_name):
    """Tester une radio"""
    try:
        # Décoder le nom de la radio (gère les deux cas: encodé et non encodé)
        import urllib.parse
        radio_name = urllib.parse.unquote(radio_name)
        
        # Charger les radios existantes
        radios = load_radios()
        
        # Trouver l'URL de la radio
        for name, url in radios:
            if name == radio_name:
                return redirect(url_for('admin'))
                # TODO: Ajouter un vrai test de lecture
                # Pour le moment, on redirige vers l'admin
        else:
            flash(f'Radio "{radio_name}" non trouvée', 'error')
            
    except Exception as e:
        flash(f'Erreur lors du test: {str(e)}', 'error')
    
    return redirect(url_for('admin'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
