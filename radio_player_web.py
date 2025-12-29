#!/usr/bin/env python3
"""
Interface Web pour Lecteur Radio avec Reprise Instantanée en Direct
Quand on met pause et qu'on appuie sur play, ça reprend instantanément en direct
"""

from flask import Flask, render_template, jsonify, request
import threading
import time
import os
from radio_metadata_fetcher_fixed_clean import RadioFetcher

# Spécifier les chemins pour templates et static
template_dir = os.path.join(os.getcwd(), 'templates')
static_dir = os.path.join(os.getcwd(), 'static')
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# Logs au démarrage de l'application
print("🎵 Démarrage du serveur web du lecteur radio...")
print(f"📁 Répertoire courant: {os.getcwd()}")
print(f"📂 Templates folder: {app.template_folder}")
print(f"📂 Static folder: {app.static_folder}")

# Vérifier si le template existe
template_path = os.path.join(app.template_folder, 'index.html')
print(f"📄 Template path: {template_path}")
print(f"✅ Template exists: {os.path.exists(template_path)}")

print("⚡ Reprise instantanée en direct activée!")
print("🚀 Application Flask prête!")

# Variables globales
fetcher = RadioFetcher()
current_station = None
current_url = None
is_playing = False
last_metadata = None

def update_metadata_loop():
    """Thread qui met à jour les métadonnées en continu"""
    while True:
        try:
            if is_playing and current_station and current_url:
                # Les métadonnées sont mises à jour via l'API
                pass
            time.sleep(5)
        except Exception as e:
            print(f"Erreur dans la boucle de métadonnées: {e}")
            time.sleep(10)

# Le thread sera démarré plus tard si nécessaire
# metadata_thread = threading.Thread(target=update_metadata_loop, daemon=True)
# metadata_thread.start()

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
    ("Superloustic", "https://radio6.pro-fhi.net/live/SUPERLOUSTIC"),
    ("Radio Gérard", "https://radiosurle.net:8765/radiogerard"),
    ("Supernana", "https://radiosurle.net:8765/showsupernana"),
    ("Génération Dorothée", "https://stream.votreradiosurlenet.eu/generationdorothee.mp3"),
    ("Made In 80", "https://listen.radioking.com/radio/260719/stream/305509"),
    ("Top 80 Radio", "https://securestreams6.autopo.st:2321/"),
    ("Générikds", "https://www.radioking.com/play/generikids"),
    ("Chansons Oubliées Où Presque", "https://manager7.streamradio.fr:2850/stream"),
    ("Nostalgie-Les Tubes 80 N1", "https://streaming.nrjaudio.fm/ouo6im7nfibk"),
]

@app.route('/')
def index():
    """Page principale du lecteur radio"""
    try:
        return render_template('index.html', stations=stations)
    except Exception as e:
        print(f"Erreur template: {e}")
        return f"Erreur template: {e}", 500

@app.route('/health')
def health():
    """Route de santé pour Railway"""
    return {"status": "ok", "message": "Radio Player is running"}

@app.route('/api/radios')
def api_radios():
    """Route pour le healthcheck Railway - retourne la liste des radios"""
    print("📡 Route /api/radios appelée - Healthcheck Railway")
    return {"status": "ok", "radios": [{"name": station[0], "url": station[1]} for station in stations]}

@app.route('/api/play')
def play():
    global is_playing, current_station, current_url
    station = request.args.get('station')
    url = request.args.get('url')
    
    if station and url:
        current_station = station
        current_url = url
        is_playing = True
        print(f"▶️  Lecture: {station}")
        return jsonify({
            'status': 'playing',
            'station': station,
            'url': url,
            'message': f'Lecture de {station}'
        })
    
    return jsonify({'status': 'error', 'message': 'Station manquante'})

@app.route('/api/pause')
def pause():
    global is_playing
    is_playing = False
    print(f"⏸️  Pause: {current_station}")
    return jsonify({
        'status': 'paused',
        'station': current_station,
        'message': 'Pause'
    })

@app.route('/api/resume')
def resume():
    global is_playing
    if current_station:
        is_playing = True
        print(f"▶️  Reprise en direct: {current_station}")
        return jsonify({
            'status': 'playing',
            'station': current_station,
            'url': current_url,
            'message': f'Reprise en direct de {current_station}'
        })
    
    return jsonify({'status': 'error', 'message': 'Aucune radio sélectionnée'})

@app.route('/api/stop')
def stop():
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
    global last_metadata
    
    if is_playing and current_station and current_url:
        try:
            metadata = fetcher.get_metadata_with_history(current_station, current_url)
            
            if metadata:
                # Vérifier si les métadonnées ont changé
                current = (metadata.artist, metadata.title)
                if last_metadata != current:
                    last_metadata = current
                    print(f"🎵 [{current_station}] {metadata.artist} - {metadata.title}")
                
                return jsonify({
                    'status': 'success',
                    'artist': metadata.artist,
                    'title': metadata.title,
                    'cover_url': metadata.cover_url,
                    'station': current_station,
                    'is_playing': is_playing
                })
        except Exception as e:
            print(f"Erreur métadonnées: {e}")
    
    return jsonify({
        'status': 'no_data',
        'is_playing': is_playing,
        'station': current_station
    })

@app.route('/api/history')
def get_history():
    if not current_station:
        return jsonify({'status': 'error', 'message': 'Aucune radio sélectionnée'})
    
    try:
        history = fetcher.get_history(current_station, current_url, 20)
        return jsonify({
            'status': 'success',
            'history': history,
            'station': current_station
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    # Configuration pour Railway
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"🌐 Port: {port}")
    print(f"🐛 Debug: {debug}")
    
    app.run(debug=debug, host='0.0.0.0', port=port)
