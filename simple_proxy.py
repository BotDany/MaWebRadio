#!/usr/bin/env python3
import http.server
import socketserver
import urllib.request
import json
from datetime import datetime

class MyTunerProxy(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if 'metadata-api.mytuner.mobi' in self.path:
            print(f"\n=== Requête myTuner capturée ===")
            print(f"URL: {self.path}")
            print(f"Headers:")
            for header, value in self.headers.items():
                print(f"  {header}: {value}")
            print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Extraire timestamp et signature
            if 'time=' in self.path:
                import re
                timestamp_match = re.search(r'time=(\d+)', self.path)
                if timestamp_match:
                    timestamp = timestamp_match.group(1)
                    print(f"Timestamp extrait: {timestamp}")
            
            if 'Authorization' in self.headers:
                auth = self.headers['Authorization']
                print(f"Authorization: {auth}")
                
                # Extraire signature
                if 'HMAC' in auth:
                    parts = auth.split(':')
                    if len(parts) >= 3:
                        signature = parts[2].strip()
                        print(f"Signature HMAC: {signature}")
            
            print("=" * 40)
        
        # Forward la requête
        try:
            response = urllib.request.urlopen(self.path)
            self.send_response(response.getcode())
            
            # Copier les headers
            for header, value in response.headers.items():
                self.send_header(header, value)
            self.end_headers()
            
            # Copier le body
            self.wfile.write(response.read())
            
        except Exception as e:
            self.send_error(500, str(e))

if __name__ == "__main__":
    import socket
    
    # Trouver un port libre automatiquement
    def find_free_port():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port
    
    PORT = find_free_port()
    with socketserver.TCPServer(("", PORT), MyTunerProxy) as httpd:
        print(f"Proxy démarré sur le port {PORT}")
        print("Configurez votre mobile pour utiliser ce proxy")
        print(f"IP de votre PC + port {PORT}")
        print("CTRL+C pour arrêter")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nProxy arrêté")
