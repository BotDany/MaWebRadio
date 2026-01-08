"""
WSGI config pour le déploiement Railway.
Ce fichier est utilisé par Gunicorn pour démarrer l'application.
"""

import os
from final_app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
