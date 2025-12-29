"""
WSGI pour la version originale qui fonctionnait sur Railway
"""

from radio_player_web import app

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
