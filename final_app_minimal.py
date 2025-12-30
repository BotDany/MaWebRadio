#!/usr/bin/env python3
"""
Version minimale de final_app.py pour diagnostic Railway
"""

import os
import time
from flask import Flask, render_template

app = Flask(__name__)
app.secret_key = 'radio_admin_secret_key_2025'

# Radios par défaut
DEFAULT_RADIOS = [
    ["RTL", "http://streaming.radio.rtl.fr/rtl-1-44-128"],
    ["Chante France-80s", "https://chantefrance80s.ice.infomaniak.ch/chantefrance80s-128.mp3"],
    ["100% Radio 80", "http://100radio-80.ice.infomaniak.ch/100radio-80-128.mp3"],
    ["RFM 80-90", "http://rfm-live-mp3-128.scdn.arkena.com/rfm.mp3"],
    ["RTL2 80s", "http://streaming.radio.rtl2.fr/rtl2-1-44-128"],
    ["Virgin Radio 80s", "https://ais-live.cloud-services.asso.fr/virginradio.mp3"],
    ["Bide Et Musique", "https://relay1.bide-et-musique.com:9300/bm.mp3"],
    ["Flash 80 Radio", "https://manager7.streamradio.fr:1985/stream"],
    ["Mega Hits", "https://playerservices.streamtheworld.com/api/livestream-redirect/MEGA_HITSAAC_SC"],
    ["Radio Comercial", "https://stream-icy.bauermedia.pt/comercial.mp3"],
    ["Superloustic", "https://radio6.pro-fhi.net/live/SUPERLOUSTIC"],
    ["Génération Dorothée", "https://stream.votreradiosurlenet.eu/generationdorothee.mp3"],
    ["Top 80 Radio", "https://securestreams6.autopo.st:2321/"],
    ["Chansons Oubliées Où Presque", "https://manager7.streamradio.fr:2850/stream"],
    ["Générikds", "https://listen.radioking.com/radio/497599/stream/554719"]
]

@app.route('/')
def index():
    print("🏠 Page d'accueil demandée")
    try:
        return render_template('index.html', stations=DEFAULT_RADIOS)
    except Exception as e:
        print(f"❌ Erreur template: {e}")
        return f"""
        <h1>🎵 Ma Webradio</h1>
        <p>Erreur de template: {e}</p>
        <h2>📻 Radios disponibles:</h2>
        <ul>
        {''.join([f'<li>{radio[0]} - {radio[1]}</li>' for radio in DEFAULT_RADIOS])}
        </ul>
        """

@app.route('/api/test')
def test():
    return {'status': 'ok', 'radios': len(DEFAULT_RADIOS)}

if __name__ == '__main__':
    print("🚀 Démarrage de l'application minimale...")
    time.sleep(1)  # Petit délai
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Démarrage sur le port {port}")
    app.run(host='0.0.0.0', port=port)
