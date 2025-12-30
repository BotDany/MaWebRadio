#!/usr/bin/env python3
"""
Point d'entrée WSGI pour Railway
"""

import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1>🎵 Ma Webradio - WSGI</h1>
    <p>Application fonctionne via WSGI !</p>
    <p>PORT: {}</p>
    <p>Ready for production!</p>
    """.format(os.environ.get('PORT', 'non défini'))

# Point d'entrée WSGI
application = app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
