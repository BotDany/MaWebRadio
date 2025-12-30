import os
from final_app import app

# Configuration Railway
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
else:
    # Pour les serveurs WSGI comme Railway
    app = app
