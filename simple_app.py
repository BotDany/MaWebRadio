from flask import Flask, jsonify, request
import os

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
    <head>
        <title>Radio Player Test</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
            .container { max-width: 800px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 30px; border-radius: 20px; }
            .radio-list { margin: 20px 0; }
            .radio-item { margin: 10px 0; padding: 15px; background: rgba(255,255,255,0.1); border-radius: 10px; }
            button { padding: 10px 20px; margin: 5px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background: #45a049; }
            .metadata { margin: 20px 0; padding: 20px; background: rgba(255,255,255,0.2); border-radius: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎵 Radio Player Test</h1>
            <div class="radio-list">
                <div class="radio-item">
                    <h3>RTL</h3>
                    <button onclick="playRadio('RTL', 'http://streaming.radio.rtl.fr/rtl-1-44-128')">▶️ Play RTL</button>
                </div>
                <div class="radio-item">
                    <h3>Chante France-80s</h3>
                    <button onclick="playRadio('Chante France-80s', 'https://chantefrance80s.ice.infomaniak.ch/chantefrance80s-128.mp3')">▶️ Play Chante France</button>
                </div>
                <div class="radio-item">
                    <h3>Nostalgie 80</h3>
                    <button onclick="playRadio('Nostalgie 80', 'https://scdn.nrjaudio.fm/fr/30601/mp3_128.mp3')">▶️ Play Nostalgie</button>
                </div>
            </div>
            <div class="metadata" id="metadata">
                <h3>🎵 Métadonnées</h3>
                <p id="artist">Artiste: --</p>
                <p id="title">Titre: --</p>
                <p id="status">Status: Arrêté</p>
            </div>
        </div>
        
        <script>
            let currentStation = null;
            let currentUrl = null;
            
            function playRadio(station, url) {
                currentStation = station;
                currentUrl = url;
                
                // Appeler l'API pour démarrer
                fetch(`/api/play?station=${encodeURIComponent(station)}&url=${encodeURIComponent(url)}`)
                    .then(response => response.json())
                    .then(data => {
                        console.log('Play response:', data);
                        document.getElementById('status').textContent = `Status: Playing - ${station}`;
                        updateMetadata();
                    });
            }
            
            function updateMetadata() {
                if (!currentStation) return;
                
                fetch('/api/metadata')
                    .then(response => response.json())
                    .then(data => {
                        console.log('Metadata:', data);
                        document.getElementById('artist').textContent = `Artiste: ${data.artist || '--'}`;
                        document.getElementById('title').textContent = `Titre: ${data.title || '--'}`;
                        
                        if (data.status === 'success') {
                            document.getElementById('status').textContent = `Status: Playing - ${data.station}`;
                        }
                    })
                    .catch(error => console.error('Error:', error));
            }
            
            // Mettre à jour les métadonnées toutes les 5 secondes
            setInterval(updateMetadata, 5000);
        </script>
    </body>
    </html>
    """

@app.route('/api/play')
def play():
    station = request.args.get('station')
    url = request.args.get('url')
    
    print(f"▶️ Play: {station} - {url}")
    
    return jsonify({
        'status': 'playing',
        'station': station,
        'url': url
    })

@app.route('/api/metadata')
def metadata():
    # Simuler des métadonnées pour le test
    if request.args.get('station') or True:  # Temporaire pour test
        return jsonify({
            'status': 'success',
            'artist': 'Artiste Test',
            'title': 'Titre Test',
            'station': 'Radio Test',
            'is_playing': True
        })
    
    return jsonify({
        'status': 'no_data',
        'is_playing': False
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Simple app démarrée sur le port {port}")
    app.run(host='0.0.0.0', port=port)
