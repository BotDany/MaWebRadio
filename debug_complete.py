#!/usr/bin/env python3
import os
import sys
import threading
import time
from flask import Flask, render_template, jsonify, request

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from radio_metadata_fetcher_fixed_clean import RadioFetcher

app = Flask(__name__, template_folder='templates', static_folder='static')

# Variables globales
fetcher = RadioFetcher()
current_station = None
current_url = None
is_playing = False
last_metadata = None

# Liste des radios
stations = [
    ("Chante France-80s", "https://chantefrance80s.ice.infomaniak.ch/chantefrance80s-128.mp3"),
    ("RTL", "http://streaming.radio.rtl.fr/rtl-1-44-128"),
    ("100% Radio 80", "http://100radio-80.ice.infomaniak.ch/100radio-80-128.mp3"),
    ("Nostalgie 80", "https://scdn.nrjaudio.fm/fr/30601/mp3_128.mp3"),
    ("Nostalgie-Les 80 Plus Grand Tubes", "https://streaming.nrjaudio.fm/ouwg8usk6j4d"),
    ("RTL2 80s", "http://streaming.radio.rtl2.fr/rtl2-1-44-128"),
    ("RFM 80-90", "http://rfm-live-mp3-128.scdn.arkena.com/rfm.mp3"),
    ("NRJ 80s", "https://scdn.nrjaudio.fm/fr/30601/mp3_128.mp3"),
    ("Virgin Radio 80s", "https://ais-live.cloud-services.asso.fr/virginradio.mp3"),
]

def update_metadata_loop():
    """Thread qui met à jour les métadonnées en continu"""
    global last_metadata
    while True:
        try:
            if is_playing and current_station and current_url:
                print(f"🔍 [Thread] Recherche métadonnées pour: {current_station}")
                metadata = fetcher.get_metadata(current_station, current_url)
                if metadata:
                    last_metadata = metadata
                    print(f"🎵 [Thread] TROUVÉ: {metadata.artist} - {metadata.title}")
                else:
                    print(f"❌ [Thread] Pas de métadonnées pour: {current_station}")
            time.sleep(5)
        except Exception as e:
            print(f"❌ [Thread] Erreur: {e}")
            time.sleep(10)

# Démarrer le thread
metadata_thread = threading.Thread(target=update_metadata_loop, daemon=True)
metadata_thread.start()

@app.route('/')
def index():
    return render_template('index.html', stations=stations)

@app.route('/api/metadata')
def get_metadata():
    global last_metadata
    
    print(f"🔍 [API] Appelée - playing: {is_playing}, station: {current_station}")
    
    if is_playing and current_station and current_url:
        # Essayer get_metadata_with_history d'abord
        try:
            metadata = fetcher.get_metadata_with_history(current_station, current_url)
            if metadata:
                result = {
                    'status': 'success',
                    'artist': metadata.artist,
                    'title': metadata.title,
                    'cover_url': metadata.cover_url,
                    'station': current_station,
                    'is_playing': is_playing
                }
                print(f"📤 [API] Renvoie (with_history): {result}")
                return jsonify(result)
        except Exception as e:
            print(f"❌ [API] Erreur get_metadata_with_history: {e}")
        
        # Essayer get_metadata en fallback
        try:
            metadata = fetcher.get_metadata(current_station, current_url)
            if metadata:
                result = {
                    'status': 'success',
                    'artist': metadata.artist,
                    'title': metadata.title,
                    'cover_url': metadata.cover_url,
                    'station': current_station,
                    'is_playing': is_playing
                }
                print(f"📤 [API] Renvoie (simple): {result}")
                return jsonify(result)
        except Exception as e:
            print(f"❌ [API] Erreur get_metadata: {e}")
    
    result = {
        'status': 'no_data',
        'is_playing': is_playing,
        'station': current_station
    }
    print(f"📤 [API] Renvoie (no_data): {result}")
    return jsonify(result)

@app.route('/api/play')
def play():
    global is_playing, current_station, current_url
    
    station_name = request.args.get('station')
    station_url = request.args.get('url')
    
    if station_name and station_url:
        current_station = station_name
        current_url = station_url
        is_playing = True
        print(f"▶️ [API] Play: {current_station}")
        return jsonify({
            'status': 'playing',
            'station': current_station,
            'url': current_url
        })
    
    return jsonify({'status': 'error', 'message': 'Station manquante'})

@app.route('/api/stop')
def stop():
    global is_playing, current_station, current_url
    station = current_station
    is_playing = False
    current_station = None
    current_url = None
    last_metadata = None
    print(f"⏹️ [API] Stop: {station}")
    return jsonify({'status': 'stopped'})

@app.route('/api/test')
def test():
    """Route de test pour vérifier que tout fonctionne"""
    return jsonify({
        'status': 'test_ok',
        'message': 'Application fonctionne',
        'stations_count': len(stations),
        'current_station': current_station,
        'is_playing': is_playing
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Debug complete app démarrée sur port {port}")
    print("🎵 Test complet des métadonnées avec tous les logs !")
    app.run(host='0.0.0.0', port=port)
