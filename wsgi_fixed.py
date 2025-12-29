"""
WSGI config corrigé pour Railway.
Utilise radio_player_web_fixed.py avec initialisation correcte des variables.
"""

from radio_player_web_fixed import app

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
