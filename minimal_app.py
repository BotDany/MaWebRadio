from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello Railway! App is working!"

@app.route('/health')
def health():
    return {"status": "ok", "message": "App is healthy"}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting app on port {port}")
    app.run(host='0.0.0.0', port=port)
