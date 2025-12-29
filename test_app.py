from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Radio Test</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; background: #333; color: white; }
            .container { max-width: 600px; margin: 0 auto; }
            button { padding: 15px 30px; margin: 10px; background: #4CAF50; color: white; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; }
            button:hover { background: #45a049; }
            .result { margin: 20px 0; padding: 20px; background: #555; border-radius: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎵 Radio Test</h1>
            <button onclick="testRTL()">▶️ Test RTL</button>
            <button onclick="testChante()">▶️ Test Chante France</button>
            <div class="result" id="result">
                <p>Cliquez sur un bouton pour tester</p>
            </div>
        </div>
        
        <script>
            async function testRTL() {
                document.getElementById('result').innerHTML = '<p>🔄 Test RTL en cours...</p>';
                
                try {
                    const response = await fetch('/test/rtl');
                    const data = await response.json();
                    
                    document.getElementById('result').innerHTML = `
                        <h3>✅ RTL Test Result</h3>
                        <p><strong>Artiste:</strong> ${data.artist}</p>
                        <p><strong>Titre:</strong> ${data.title}</p>
                        <p><strong>Status:</strong> ${data.status}</p>
                        <p><strong>URL:</strong> ${data.url}</p>
                    `;
                } catch (error) {
                    document.getElementById('result').innerHTML = `<p>❌ Erreur: ${error.message}</p>`;
                }
            }
            
            async function testChante() {
                document.getElementById('result').innerHTML = '<p>🔄 Test Chante France en cours...</p>';
                
                try {
                    const response = await fetch('/test/chante');
                    const data = await response.json();
                    
                    document.getElementById('result').innerHTML = `
                        <h3>✅ Chante France Test Result</h3>
                        <p><strong>Artiste:</strong> ${data.artist}</p>
                        <p><strong>Titre:</strong> ${data.title}</p>
                        <p><strong>Status:</strong> ${data.status}</p>
                        <p><strong>URL:</strong> ${data.url}</p>
                    `;
                } catch (error) {
                    document.getElementById('result').innerHTML = `<p>❌ Erreur: ${error.message}</p>`;
                }
            }
        </script>
    </body>
    </html>
    """

@app.route('/test/rtl')
def test_rtl():
    try:
        from radio_metadata_fetcher_fixed_clean import RadioFetcher
        fetcher = RadioFetcher()
        
        url = "http://streaming.radio.rtl.fr/rtl-1-44-128"
        metadata = fetcher.get_metadata("RTL", url)
        
        if metadata and metadata.title and metadata.title.lower() != "en direct":
            return jsonify({
                'status': 'success',
                'artist': metadata.artist,
                'title': metadata.title,
                'url': url
            })
        else:
            return jsonify({
                'status': 'no_metadata',
                'artist': 'RTL',
                'title': 'En direct',
                'url': url
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'artist': 'RTL',
            'title': 'Erreur',
            'url': url
        })

@app.route('/test/chante')
def test_chante():
    try:
        from radio_metadata_fetcher_fixed_clean import RadioFetcher
        fetcher = RadioFetcher()
        
        url = "https://chantefrance80s.ice.infomaniak.ch/chantefrance80s-128.mp3"
        metadata = fetcher.get_metadata("Chante France-80s", url)
        
        if metadata and metadata.title and metadata.title.lower() != "en direct":
            return jsonify({
                'status': 'success',
                'artist': metadata.artist,
                'title': metadata.title,
                'url': url
            })
        else:
            return jsonify({
                'status': 'no_metadata',
                'artist': 'Chante France',
                'title': 'En direct',
                'url': url
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'artist': 'Chante France',
            'title': 'Erreur',
            'url': url
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Test app démarrée sur le port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
