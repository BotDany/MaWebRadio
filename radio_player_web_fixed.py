#!/usr/bin/env python3
"""
Interface Web pour Lecteur Radio avec Reprise Instantanée en Direct - VERSION CORRIGÉE
Quand on met pause et qu'on appuie sur play, ça reprend instantanément en direct
"""

from flask import Flask, render_template, jsonify, request
import threading
import time
import os

# Spécifier les chemins pour templates et static
template_dir = os.path.join(os.getcwd(), 'templates')
static_dir = os.path.join(os.getcwd(), 'static')
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# Variables globales - initialisées correctement
fetcher = None
current_station = None
current_url = None
is_playing = False
last_metadata = None
last_metadata_obj = None
metadata_thread = None

def init_globals():
    """Initialiser les variables globales au bon moment"""
    global fetcher, metadata_thread
    if fetcher is None:
        from radio_metadata_fetcher_fixed_clean import RadioFetcher
        fetcher = RadioFetcher()
        print("📡 RadioFetcher initialisé")
        
        # Démarrer le thread de métadonnées
        if metadata_thread is None:
            metadata_thread = threading.Thread(target=update_metadata_loop, daemon=True)
            metadata_thread.start()
            print("🔄 Thread de métadonnées démarré")

def update_metadata_loop():
    """Thread qui met à jour les métadonnées en continu"""
    while True:
        try:
            if is_playing and current_station and current_url:
                # Récupérer les métadonnées
                metadata = fetcher.get_metadata_with_history(current_station, current_url)
                
                if metadata:
                    # Vérifier si les métadonnées ont changé
                    current = (metadata.artist, metadata.title)
                    if last_metadata != current:
                        last_metadata = current
                        print(f"🎵 [{current_station}] {metadata.artist} - {metadata.title}")
                        
                        # Mettre à jour la variable globale pour l'API
                        global last_metadata_obj
                        last_metadata_obj = metadata
            time.sleep(5)
        except Exception as e:
            print(f"Erreur dans la boucle de métadonnées: {e}")
            time.sleep(10)

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

# Initialiser les globals dès l'import pour éviter les problèmes avec Gunicorn
init_globals()

@app.route('/')
def index():
    """Page principale du lecteur radio"""
    try:
        return render_template('index.html', stations=stations)
    except Exception as e:
        print(f"Erreur template: {e}")
        # Fallback pour healthcheck
        return jsonify({
            'status': 'ok',
            'message': 'Radio Player is running',
            'service': 'Ma Web Radio'
        }), 200

@app.route('/health')
def health():
    """Route de santé pour Railway"""
    return jsonify({
        'status': 'ok',
        'message': 'Radio Player is running',
        'service': 'Ma Web Radio'
    })

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
        print(f"▶️  Play: {station}")
        
        return jsonify({
            'status': 'playing',
            'station': current_station,
            'url': current_url
        })
    
    return jsonify({'status': 'error', 'message': 'Paramètres manquants'})

@app.route('/api/pause')
def pause():
    global is_playing
    is_playing = False
    print(f"⏸️  Pause: {current_station}")
    
    return jsonify({
        'status': 'paused',
        'station': current_station
    })

@app.route('/api/resume')
def resume():
    global is_playing
    if current_station and current_url:
        is_playing = True
        print(f"▶️  Resume: {current_station} (reprise instantanée en direct)")
        
        return jsonify({
            'status': 'playing',
            'station': current_station,
            'url': current_url,
            'message': 'Reprise instantanée en direct'
        })
    
    return jsonify({'status': 'error', 'message': 'Aucune radio à reprendre'})

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
    global last_metadata_obj
    
    if is_playing and current_station and current_url:
        # Utiliser les métadonnées en cache mises à jour par le thread
        if last_metadata_obj:
            return jsonify({
                'status': 'success',
                'artist': last_metadata_obj.artist,
                'title': last_metadata_obj.title,
                'cover_url': last_metadata_obj.cover_url,
                'station': current_station,
                'is_playing': is_playing
            })
        else:
            # Fallback si pas encore de métadonnées en cache
            try:
                metadata = fetcher.get_metadata_with_history(current_station, current_url)
                if metadata:
                    last_metadata_obj = metadata
                    return jsonify({
                        'status': 'success',
                        'artist': metadata.artist,
                        'title': metadata.title,
                        'cover_url': metadata.cover_url,
                        'station': current_station,
                        'is_playing': is_playing
                    })
            except Exception as e:
                print(f"Erreur métadonnées fallback: {e}")
    
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
            'history': history
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    # Configuration pour Railway
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"🌐 Port: {port}")
    print(f"🐛 Debug: {debug}")
    
    # Initialiser les variables globales
    init_globals()
    
    app.run(debug=debug, host='0.0.0.0', port=port)
