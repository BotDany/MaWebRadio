from flask import Flask, jsonify, request
import os

app = Flask(__name__)

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
]

@app.route('/')
def home():
    # Générer les boutons pour chaque radio
    radio_buttons = ""
    for name, url in RADIOS:
        radio_buttons += f'<button onclick="playRadio(\'{name}\', \'{url}\')">▶️ {name}</button>\n'
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>🎵 Radio Player - Métadonnées Réelles</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; min-height: 100vh; }}
            .container {{ max-width: 1000px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 30px; border-radius: 20px; backdrop-filter: blur(10px); }}
            h1 {{ text-align: center; margin-bottom: 30px; font-size: 2.5em; }}
            .radio-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin: 30px 0; }}
            button {{ padding: 15px 20px; margin: 5px; background: linear-gradient(45deg, #4CAF50, #45a049); color: white; border: none; border-radius: 10px; font-size: 14px; cursor: pointer; transition: all 0.3s; font-weight: bold; }}
            button:hover {{ transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.3); }}
            button:active {{ transform: translateY(0); }}
            .metadata {{ margin: 30px 0; padding: 30px; background: rgba(255,255,255,0.2); border-radius: 15px; text-align: center; backdrop-filter: blur(10px); }}
            .metadata h3 {{ font-size: 1.8em; margin-bottom: 20px; }}
            .metadata p {{ font-size: 1.2em; margin: 10px 0; }}
            .artist {{ font-size: 1.5em; font-weight: bold; color: #4CAF50; }}
            .title {{ font-size: 1.4em; font-weight: bold; color: #2196F3; }}
            .status {{ font-size: 1.1em; color: #FFC107; }}
            .loading {{ animation: pulse 1.5s infinite; }}
            @keyframes pulse {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} 100% {{ opacity: 1; }} }}
            .success {{ border: 2px solid #4CAF50; }}
            .error {{ border: 2px solid #f44336; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎵 Radio Player - Métadonnées Réelles</h1>
            
            <div class="radio-grid">
                {radio_buttons}
            </div>
            
            <div class="metadata" id="metadata">
                <h3>🎵 Métadonnées en Direct</h3>
                <p class="artist" id="artist">Artiste: --</p>
                <p class="title" id="title">Titre: --</p>
                <p class="status" id="status">Status: Sélectionnez une radio</p>
            </div>
        </div>
        
        <script>
            let currentStation = null;
            let currentUrl = null;
            let updateInterval = null;
            
            function playRadio(station, url) {{
                currentStation = station;
                currentUrl = url;
                
                // Arrêter l'ancien intervalle
                if (updateInterval) {{
                    clearInterval(updateInterval);
                }}
                
                // Mettre à jour l'interface immédiatement
                document.getElementById('status').innerHTML = `<span class="loading">🔄 Connexion à ${{station}}...</span>`;
                document.getElementById('artist').textContent = 'Artiste: --';
                document.getElementById('title').textContent = 'Titre: --';
                
                // Appeler l'API pour obtenir les métadonnées
                updateMetadata();
                
                // Mettre à jour toutes les 5 secondes
                updateInterval = setInterval(updateMetadata, 5000);
            }}
            
            async function updateMetadata() {{
                if (!currentStation || !currentUrl) return;
                
                try {{
                    const response = await fetch('/api/metadata', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{
                            station: currentStation,
                            url: currentUrl
                        }})
                    }});
                    
                    const data = await response.json();
                    console.log('Metadata:', data);
                    
                    const metadataDiv = document.getElementById('metadata');
                    
                    if (data.status === 'success') {{
                        document.getElementById('artist').textContent = `Artiste: ${{data.artist}}`;
                        document.getElementById('title').textContent = `Titre: ${{data.title}}`;
                        document.getElementById('status').innerHTML = `✅ ${{data.station}} - En direct`;
                        metadataDiv.className = 'metadata success';
                    }} else if (data.status === 'no_metadata') {{
                        document.getElementById('artist').textContent = `Artiste: ${{data.artist}}`;
                        document.getElementById('title').textContent = `Titre: ${{data.title}}`;
                        document.getElementById('status').innerHTML = `📻 ${{data.station}} - En direct`;
                        metadataDiv.className = 'metadata';
                    }} else {{
                        document.getElementById('artist').textContent = 'Artiste: --';
                        document.getElementById('title').textContent = 'Titre: --';
                        document.getElementById('status').innerHTML = `❌ Erreur: ${{data.error}}`;
                        metadataDiv.className = 'metadata error';
                    }}
                }} catch (error) {{
                    console.error('Error:', error);
                    document.getElementById('status').innerHTML = `❌ Erreur: ${{error.message}}`;
                    document.getElementById('metadata').className = 'metadata error';
                }}
            }}
        </script>
    </body>
    </html>
    """

@app.route('/api/metadata', methods=['POST'])
def get_metadata():
    try:
        data = request.get_json()
        station = data.get('station')
        url = data.get('url')
        
        if not station or not url:
            return jsonify({'status': 'error', 'error': 'Station ou URL manquante'})
        
        print(f"🔍 Requête métadonnées: {station} - {url}")
        
        # Importer et utiliser le fetcher
        from radio_metadata_fetcher_fixed_clean import RadioFetcher
        fetcher = RadioFetcher()
        
        metadata = fetcher.get_metadata(station, url)
        
        if metadata and metadata.title and metadata.title.lower() != "en direct":
            result = {
                'status': 'success',
                'artist': metadata.artist or station,
                'title': metadata.title,
                'station': station,
                'url': url
            }
            print(f"📤 Succès: {result}")
            return jsonify(result)
        else:
            result = {
                'status': 'no_metadata',
                'artist': station,
                'title': 'En direct',
                'station': station,
                'url': url
            }
            print(f"📤 Pas de métadonnées: {result}")
            return jsonify(result)
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'station': station,
            'url': url
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Application finale avec {len(RADIOS)} radios démarrée sur le port {port}")
    app.run(host='0.0.0.0', port=port)
