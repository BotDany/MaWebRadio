#!/usr/bin/env python3
"""
Version ultra-robuste pour Railway - sans dépendances complexes
"""

from flask import Flask, jsonify, render_template, request
import os

# Configuration Flask avec chemins explicites
template_dir = os.path.join(os.getcwd(), 'templates')
static_dir = os.path.join(os.getcwd(), 'static')
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

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

# Variables globales simples
current_station = None
current_url = None
is_playing = False

@app.route('/')
def index():
    """Page principale"""
    try:
        return render_template('index.html', stations=stations)
    except Exception as e:
        print(f"Erreur template: {e}")
        # Fallback JSON pour healthcheck
        return jsonify({
            'status': 'ok',
            'message': 'Ma Web Radio - Service Actif',
            'stations_count': len(stations)
        })

@app.route('/health')
def health():
    """Health check simple"""
    return jsonify({
        'status': 'ok',
        'message': 'Ma Web Radio - Service Actif',
        'version': 'robuste'
    })

@app.route('/api/radios')
def api_radios():
    """API pour healthcheck"""
    return jsonify({
        'status': 'ok',
        'radios': [{"name": station[0], "url": station[1]} for station in stations]
    })

@app.route('/api/play')
def play():
    """API play simple"""
    global is_playing, current_station, current_url
    
    station = request.args.get('station')
    url = request.args.get('url')
    
    if station and url:
        current_station = station
        current_url = url
        is_playing = True
        return jsonify({
            'status': 'playing',
            'station': current_station,
            'url': current_url
        })
    
    return jsonify({'status': 'error', 'message': 'Paramètres manquants'})

@app.route('/api/stop')
def stop():
    """API stop simple"""
    global is_playing, current_station, current_url
    is_playing = False
    current_station = None
    current_url = None
    return jsonify({'status': 'stopped'})

@app.route('/api/metadata')
def metadata():
    """API metadata simple"""
    return jsonify({
        'status': 'no_data',
        'message': 'Version robuste sans métadonnées complexes',
        'is_playing': is_playing,
        'station': current_station
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Application robuste démarrée sur port {port}")
    app.run(host='0.0.0.0', port=port)
