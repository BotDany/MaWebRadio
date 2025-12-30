from flask import Flask
import os
import sys

app = Flask(__name__)

@app.route('/')
def hello():
    return """
    <h1>🚂 Railway Test App</h1>
    <p>Application is working!</p>
    <ul>
        <li>Python version: {}</li>
        <li>Working directory: {}</li>
        <li>Environment PORT: {}</li>
    </ul>
    """.format(sys.version, os.getcwd(), os.environ.get('PORT', 'Not set'))

@app.route('/health')
def health():
    return {"status": "ok", "python": sys.version}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting diagnostic app on port {port}")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    app.run(host='0.0.0.0', port=port, debug=True)
