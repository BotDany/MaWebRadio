#!/usr/bin/env python3
import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return "<h1>🎵 Radio App Works!</h1><p>Python version: 3.9+</p>"

@app.route('/api/metadata')
def metadata():
    return '{"status":"success","artist":"Test Artist","title":"Test Title"}'

@app.route('/health')
def health():
    return '{"status":"ok"}'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
