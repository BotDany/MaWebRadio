from flask import Flask, render_template, jsonify, request
import os
from radio_metadata_fetcher_fixed_clean import RadioFetcher

class RadioState:
    def __init__(self):
        self.current_station = None
        self.current_url = None
        self.is_playing = False
        self.fetcher = RadioFetcher()

app = Flask(__name__)
radio_state = RadioState()

# Liste des radios qui fonctionnent
RADIOS = [
    ("RTL", "http://streaming.radio.rtl.fr/rtl-1-44-128"),
    ("Chante France-80s", "https://chantefrance80s.ice.infomaniak.ch/chantefrance80s-128.mp3"),
    ("100% Radio 80", "http://100radio-80.ice.infomaniak.ch/100radio-80-128.mp3"),
    ("Nostalgie 80", "https://scdn.nrjaudio.fm/fr/30601/mp3_128.mp3"),
    ("RFM 80-90", "http://rfm-live-mp3-128.scdn.arkena.com/rfm.mp3"),
    ("RTL2 80s", "http://streaming.radio.rtl2.fr/rtl2-1-44-128"),
    ("NRJ 80s", "https://scdn.nrjaudio.fm/fr/30601/mp3_128.mp3"),
    ("Virgin Radio 80s", "https://ais-live.cloud-services.asso.fr/virginradio.mp3"),
    ("Bide Et Musique", "https://relay1.bide-et-musique.com:9300/bm.mp3"),
    ("Flash 80 Radio", "https://manager7.streamradio.fr:1985/stream"),
    ("Mega Hits", "https://playerservices.streamtheworld.com/api/livestream-redirect/MEGA_HITSAAC_SC"),
    ("Radio Comercial", "https://stream-icy.bauermedia.pt/comercial.mp3"),
    ("Superloustic", "https://radio6.pro-fhi.net/live/SUPERLOUSTIC"),
    ("Génération Dorothée", "https://stream.votreradiosurlenet.eu/generationdorothee.mp3"),
    ("Top 80 Radio", "https://securestreams6.autopo.st:2321/"),
    ("Chansons Oubliées Où Presque", "https://manager7.streamradio.fr:2850/stream"),
    ("Générikds", "https://play.radioking.io/generikids"),
]

@app.route('/')
def index():
    return render_template('index.html', stations=RADIOS)

@app.route('/api/metadata')
def metadata():
    print(f"🔍 API appelée - station: {radio_state.current_station}, playing: {radio_state.is_playing}")
    
    if radio_state.current_station and radio_state.current_url and radio_state.is_playing:
        try:
            # Utiliser le vrai fetcher pour obtenir les métadonnées
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
                
                print(f"📤 API renvoie: {result}")
                return jsonify(result)
            else:
                # Si pas de métadonnées, renvoyer l'état actuel
                result = {
                    'status': 'no_data',
                    'artist': radio_state.current_station,
                    'title': 'En direct',
                    'cover_url': '',
                    'station': radio_state.current_station,
                    'is_playing': True
                }
                
                print(f"📤 API renvoie (no_metadata): {result}")
                return jsonify(result)
                
        except Exception as e:
            print(f"❌ Erreur métadonnées: {e}")
            # En cas d'erreur, renvoyer l'état actuel
            result = {
                'status': 'error',
                'artist': radio_state.current_station,
                'title': 'En direct',
                'cover_url': '',
                'station': radio_state.current_station,
                'is_playing': True
            }
            
            print(f"📤 API renvoie (error): {result}")
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
        radio_state.current_url = url
        radio_state.is_playing = True
        print(f"▶️ Play: {station} - {url}")
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

@app.route('/api/history')
def history():
    if not radio_state.current_station:
        return jsonify({'status': 'error', 'message': 'Aucune radio sélectionnée'})
    
    try:
        # Utiliser le fetcher pour obtenir l'historique
        history_data = radio_state.fetcher.get_history(radio_state.current_station, radio_state.current_url, 10)
        
        if history_data and len(history_data) > 0:
            result = {
                'status': 'success',
                'station': radio_state.current_station,
                'history': history_data
            }
        else:
            result = {
                'status': 'success',
                'station': radio_state.current_station,
                'history': [],
                'message': 'Aucun historique disponible pour cette radio'
            }
        
        print(f"📋 Historique: {len(history_data) if history_data else 0} chansons pour {radio_state.current_station}")
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Erreur historique: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Erreur: {str(e)}',
            'station': radio_state.current_station
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Application finale avec {len(RADIOS)} radios démarrée sur le port {port}")
    app.run(host='0.0.0.0', port=port)
