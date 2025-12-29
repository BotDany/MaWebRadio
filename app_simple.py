#!/usr/bin/env python3
"""
Version simplifiée pour Railway - sans métadonnées complexes
"""

import os
from flask import Flask, jsonify, render_template, request

# Configuration Flask
app = Flask(__name__)

# Liste des radios
stations = [
    ("Chante France-80s", "https://chantefrance80s.ice.infomaniak.ch/chantefrance80s-128.mp3"),
    ("RTL", "http://streaming.radio.rtl.fr/rtl-1-44-128"),
    ("100% Radio 80", "http://100radio-80.ice.infomaniak.ch/100radio-80-128.mp3"),
    ("Nostalgie-Les 80 Plus Grand Tubes", "https://streaming.nrjaudio.fm/ouwg8usk6j4d"),
    ("Flash 80 Radio", "https://manager7.streamradio.fr:1985/stream"),
    ("Radio Comercial", "https://stream-icy.bauermedia.pt/comercial.mp3"),
    ("Bide Et Musique", "https://relay1.bide-et-musique.com:9300/bm.mp3"),
    ("Mega Hits", "https://playerservices.streamtheworld.com/api/livestream-redirect/MEGA_HITSAAC_SC"),
    ("Radio Nova", "https://novazz.ice.infomaniak.ch/novazz-128.mp3"),
    ("FIP", "http://direct.fipradio.fr/live/fip-midfi.mp3"),
    ("France Inter", "http://direct.franceinter.fr/live/franceinter-midfi.mp3"),
    ("France Culture", "http://direct.franceculture.fr/live/franceculture-midfi.mp3"),
    ("France Musique", "http://direct.francemusique.fr/live/francemusique-midfi.mp3"),
    ("OUI FM", "https://ouifm.ice.infomaniak.ch/ouifm-high.mp3"),
    ("Radio Classique", "https://radioclassique.ice.infomaniak.ch/radioclassique-128.mp3"),
    ("TSF Jazz", "https://tsfjazz.ice.infomaniak.ch/tsfjazz-128.mp3"),
    ("Jazz Radio", "https://jazzradio.ice.infomaniak.ch/jazzradio-128.mp3")
]

# Variables globales
current_station = None
current_url = None
is_playing = False

@app.route('/')
def index():
    """Page principale"""
    return render_template('index.html', stations=stations)

@app.route('/health')
def health():
    """Health check"""
    return {"status": "ok", "message": "Radio Player is running"}

@app.route('/api/radios')
def api_radios():
    """API pour le healthcheck Railway"""
    print("📡 Route /api/radios appelée - Healthcheck Railway")
    return {"status": "ok", "radios": [{"name": station[0], "url": station[1]} for station in stations]}

@app.route('/api/play')
def play():
    """API pour jouer une radio"""
    global is_playing, current_station, current_url
    
    station = request.args.get('station')
    url = request.args.get('url')
    
    if station and url:
        current_station = station
        current_url = url
        is_playing = True
        print(f"▶️  Play: {station}")
        
        return jsonify({
            'status': 'playing',
            'station': current_station,
            'url': current_url
        })
    
    return jsonify({'status': 'error', 'message': 'Paramètres manquants'})

@app.route('/api/pause')
def pause():
    """API pour mettre en pause"""
    global is_playing
    is_playing = False
    print(f"⏸️  Pause: {current_station}")
    
    return jsonify({
        'status': 'paused',
        'station': current_station
    })

@app.route('/api/stop')
def stop():
    """API pour arrêter"""
    global is_playing, current_station, current_url
    is_playing = False
    station = current_station
    current_station = None
    current_url = None
    print(f"⏹️  Stop: {station}")
    
    return jsonify({
        'status': 'stopped',
        'message': 'Arrêt'
    })

@app.route('/api/metadata')
def get_metadata():
    """API simplifiée sans métadonnées"""
    return jsonify({
        'status': 'no_data',
        'is_playing': is_playing,
        'station': current_station,
        'message': 'Version simplifiée sans métadonnées'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"🎵 Application simplifiée démarrée sur port {port}")
    print(f"🐛 Debug: {debug}")
    
    app.run(debug=debug, host='0.0.0.0', port=port)
