from flask import Flask, render_template, jsonify, request, session
import os
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Clé secrète pour les sessions

# Données de test pour les métadonnées
test_metadata = {
    "RTL": {"artist": "Laurent Voulzy", "title": "Belle Ile En Mer"},
    "Nostalgie 80": {"artist": "Prince", "title": "Purple Rain"},
    "Chante France-80s": {"artist": "Michaël Lancelot", "title": "Le Grand Journal"},
    "100% Radio 80": {"artist": "Madonna", "title": "Like a Virgin"},
    "RFM 80-90": {"artist": "U2", "title": "With or Without You"},
    "RTL2 80s": {"artist": "Sting", "title": "Englishman in New York"},
    "NRJ 80s": {"artist": "Michael Jackson", "title": "Billie Jean"},
    "Virgin Radio 80s": {"artist": "David Bowie", "title": "Let's Dance"},
    "Nostalgie-Les 80 Plus Grand Tubes": {"artist": "Queen", "title": "Bohemian Rhapsody"},
    "Flash 80 Radio": {"artist": "Depeche Mode", "title": "Just Can't Get Enough"}
}

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

def get_current_station():
    """Récupérer la station actuelle depuis la session"""
    return session.get('current_station')

def get_is_playing():
    """Récupérer l'état de lecture depuis la session"""
    return session.get('is_playing', False)

def set_current_station(station):
    """Définir la station actuelle dans la session"""
    session['current_station'] = station

def set_is_playing(playing):
    """Définir l'état de lecture dans la session"""
    session['is_playing'] = playing

@app.route('/')
def index():
    return render_template('index.html', stations=stations)

@app.route('/api/metadata')
def metadata():
    current_station = get_current_station()
    is_playing = get_is_playing()
    
    print(f"🔍 API appelée - station: {current_station}, playing: {is_playing}")
    
    if current_station and is_playing:
        # Utiliser les métadonnées de test
        metadata = test_metadata.get(current_station, {"artist": "Artiste inconnu", "title": "Titre inconnu"})
        
        result = {
            'status': 'success',
            'artist': metadata['artist'],
            'title': metadata['title'],
            'cover_url': '',
            'station': current_station,
            'is_playing': is_playing
        }
        
        print(f"📤 API renvoie: {result}")
        return jsonify(result)
    
    result = {
        'status': 'no_data',
        'is_playing': is_playing,
        'station': current_station
    }
    
    print(f"📤 API renvoie (no_data): {result}")
    return jsonify(result)

@app.route('/api/play')
def play():
    station = request.args.get('station')
    url = request.args.get('url')
    
    if station and url:
        set_current_station(station)
        set_is_playing(True)
        print(f"▶️ Play: {station}")
        return jsonify({
            'status': 'playing',
            'station': station,
            'url': url
        })
    
    return jsonify({'status': 'error', 'message': 'Station manquante'})

@app.route('/api/stop')
def stop():
    station = get_current_station()
    set_current_station(None)
    set_is_playing(False)
    
    print(f"⏹️ Stop: {station}")
    return jsonify({'status': 'stopped'})

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Application avec métadonnées de test démarrée sur port {port}")
    print("🎵 Les métadonnées s'afficheront immédiatement !")
    app.run(host='0.0.0.0', port=port)
