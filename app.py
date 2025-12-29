from flask import Flask, render_template, jsonify, request
import os

app = Flask(__name__)

# Données de test pour les métadonnées
test_metadata = {
    "RTL": {"artist": "Laurent Voulzy", "title": "Belle Ile En Mer"},
    "Nostalgie 80": {"artist": "Prince", "title": "Purple Rain"},
    "Chante France-80s": {"artist": "Michaël Lancelot", "title": "Le Grand Journal"},
    "100% Radio 80": {"artist": "Madonna", "title": "Like a Virgin"},
    "RFM 80-90": {"artist": "U2", "title": "With or Without You"}
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
]

current_station = None
is_playing = False

@app.route('/')
def index():
    return render_template('index.html', stations=stations)

@app.route('/api/metadata')
def metadata():
    global current_station, is_playing
    
    print(f"API appelée - station: {current_station}, playing: {is_playing}")
    
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
        
        print(f"API renvoie: {result}")
        return jsonify(result)
    
    result = {
        'status': 'no_data',
        'is_playing': is_playing,
        'station': current_station
    }
    
    print(f"API renvoie (no_data): {result}")
    return jsonify(result)

@app.route('/api/play')
def play():
    global current_station, is_playing
    
    station = request.args.get('station')
    url = request.args.get('url')
    
    if station and url:
        current_station = station
        is_playing = True
        print(f"Play: {station}")
        return jsonify({
            'status': 'playing',
            'station': station,
            'url': url
        })
    
    return jsonify({'status': 'error', 'message': 'Station manquante'})

@app.route('/api/stop')
def stop():
    global current_station, is_playing
    
    station = current_station
    current_station = None
    is_playing = False
    
    print(f"Stop: {station}")
    return jsonify({'status': 'stopped'})

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 App minimaliste démarrée sur port {port}")
    print("🎵 Métadonnées de test pour contourner le problème !")
    app.run(host='0.0.0.0', port=port)
