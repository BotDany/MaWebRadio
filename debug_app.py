#!/usr/bin/env python3
import os
import sys
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return """
    <h1>🎵 Application Radio Debug</h1>
    <p>Application fonctionne!</p>
    <p>Python: {}</p>
    <p>Port: {}</p>
    """.format(sys.version, os.environ.get('PORT', '5000'))

@app.route('/api/metadata')
def metadata():
    return jsonify({
        'status': 'debug',
        'message': 'API fonctionne',
        'artist': 'Test Artist',
        'title': 'Test Title'
    })

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Debug app démarrée sur port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
