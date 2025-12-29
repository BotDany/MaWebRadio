from flask import Flask, render_template, jsonify, request
import os

class RadioState:
    def __init__(self):
        self.current_station = None
        self.is_playing = False

app = Flask(__name__)
radio_state = RadioState()

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
    "Flash 80 Radio": {"artist": "Depeche Mode", "title": "Just Can't Get Enough"},
    "Radio Comercial": {"artist": "Amália Rodrigues", "title": "Fado Português"},
    "Bide Et Musique": {"artist": "Francis Cabrel", "title": "Je l'aime à mourir"},
    "Mega Hits": {"artist": "Bruno Mars", "title": "Uptown Funk"},
    "Superloustic": {"artist": "AC/DC", "title": "Highway to Hell"},
    "Radio Gérard": {"artist": "Gérard", "title": "Le Morning Show"},
    "Supernana": {"artist": "Les Nanas", "title": "Super Nana Show"},
    "Génération Dorothée": {"artist": "Dorothée", "title": "Club Dorothée"},
    "Made In 80": {"artist": "Jean-Michel Jarre", "title": "Oxygène"},
    "Top 80 Radio": {"artist": "The Police", "title": "Every Breath You Take"},
    "Générikds": {"artist": "Les Kids", "title": "Générik Kids"},
    "Chansons Oubliées Où Presque": {"artist": "Léo Ferré", "title": "Avec le temps"},
    "Nostalgie-Les Tubes 80 N1": {"artist": "Pink Floyd", "title": "Another Brick in the Wall"}
}

stations = [
    ("Chante France-80s", "https://chantefrance80s.ice.infomaniak.ch/chantefrance80s-128.mp3"),
    ("RTL", "http://streaming.radio.rtl.fr/rtl-1-44-128"),
    ("100% Radio 80", "http://100radio-80.ice.infomaniak.ch/100radio-80-128.mp3"),
    ("Nostalgie 80", "https://scdn.nrjaudio.fm/fr/30601/mp3_128.mp3"),
    ("RFM 80-90", "http://rfm-live-mp3-128.scdn.arkena.com/rfm.mp3"),
    ("RTL2 80s", "http://streaming.radio.rtl2.fr/rtl2-1-44-128"),
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

@app.route('/')
def index():
    return render_template('index.html', stations=stations)

@app.route('/api/metadata')
def metadata():
    print(f"🔍 API appelée - station: {radio_state.current_station}, playing: {radio_state.is_playing}")
    
    if radio_state.current_station and radio_state.is_playing:
        metadata = test_metadata.get(radio_state.current_station, {"artist": "En direct", "title": radio_state.current_station})
        
        result = {
            'status': 'success',
            'artist': metadata['artist'],
            'title': metadata['title'],
            'station': radio_state.current_station,
            'is_playing': True
        }
        
        print(f"📤 API renvoie: {result}")
        return jsonify(result)
    
    result = {
        'status': 'no_data',
        'is_playing': False,
        'station': radio_state.current_station
    }
    
    print(f"📤 API renvoie (no_data): {result}")
    return jsonify(result)

@app.route('/api/play')
def play():
    station = request.args.get('station')
    url = request.args.get('url')
    
    if station and url:
        radio_state.current_station = station
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
    radio_state.is_playing = False
    
    print(f"⏹️ Stop: {station}")
    return jsonify({'status': 'stopped'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Application démarrée sur le port {port}")
    app.run(host='0.0.0.0', port=port)
