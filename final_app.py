import json
import os
from flask import Flask, render_template, jsonify, request, flash, redirect, url_for
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

def load_radios():
    """Charger la liste des radios depuis le fichier JSON"""
    try:
        if os.path.exists('radios_config.json'):
            with open('radios_config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return []
    except Exception as e:
        print(f"Erreur chargement radios: {e}")
        return []

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
