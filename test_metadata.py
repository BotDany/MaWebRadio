#!/usr/bin/env python3
import os
from flask import Flask, jsonify

app = Flask(__name__)

# Variables globales pour simuler l'état
current_station = None
is_playing = False

@app.route('/')
def index():
    return """
    <h1>🎵 Test Métadonnées Radio</h1>
    <p>Page de test pour les métadonnées</p>
    <a href="/api/metadata">Tester API Métadonnées</a>
    """

@app.route('/api/metadata')
def metadata():
    global current_station, is_playing
    
    print(f"🔍 API appelée - station: {current_station}, playing: {is_playing}")
    
    if is_playing and current_station:
        # Simuler des métadonnées réelles
        test_data = {
            'RTL': {'artist': 'Laurent Voulzy', 'title': 'Belle Ile En Mer'},
            'Nostalgie 80': {'artist': 'Prince', 'title': 'Purple Rain'},
            'Chante France-80s': {'artist': 'Michaël Lancelot', 'title': 'Test Title'}
        }
        
        metadata = test_data.get(current_station, {'artist': 'Artiste Test', 'title': 'Titre Test'})
        
        result = {
            'status': 'success',
            'artist': metadata['artist'],
            'title': metadata['title'],
            'cover_url': 'https://example.com/cover.jpg',
            'station': current_station,
            'is_playing': is_playing
        }
        
        print(f"📤 API renvoie: {result}")
        return jsonify(result)
    else:
        result = {
            'status': 'no_data',
            'is_playing': is_playing,
            'station': current_station
        }
        print(f"📤 API renvoie (no_data): {result}")
        return jsonify(result)

@app.route('/api/play')
def play():
    global current_station, is_playing
    current_station = "RTL"
    is_playing = True
    print(f"▶️ Play: {current_station}")
    return jsonify({'status': 'playing', 'station': current_station})

@app.route('/api/stop')
def stop():
    global current_station, is_playing
    station = current_station
    current_station = None
    is_playing = False
    print(f"⏹️ Stop: {station}")
    return jsonify({'status': 'stopped'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Test app démarrée sur port {port}")
    app.run(host='0.0.0.0', port=port)
