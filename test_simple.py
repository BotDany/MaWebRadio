#!/usr/bin/env python3
"""
Test simple pour Railway - Version minimaliste
"""

from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1>🎵 Ma Webradio - Test</h1>
    <p>L'application fonctionne !</p>
    <p>Si vous voyez cette page, le déploiement Railway est réussi.</p>
    """

@app.route('/api/test')
def test():
    return jsonify({
        'status': 'ok',
        'message': 'API fonctionne',
        'database': 'PostgreSQL configuré'
    })

if __name__ == '__main__':
    port = int(__import__('os').environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
