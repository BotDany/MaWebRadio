"""
WSGI robuste pour Railway - version ultra-simplifiée
"""

from radio_player_robuste import app

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
