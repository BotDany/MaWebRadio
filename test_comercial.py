#!/usr/bin/env python3
import requests
import ssl
import sys

def main():
    url = "https://stream-icy.bauermedia.pt/comercial.mp3"
    
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.options |= 0x4
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    session = requests.Session()
    session.trust_env = False
    session.verify = False
    
    headers = {
        "Icy-MetaData": "1",
        "Accept": "*/*",
        "User-Agent": "VLC/3.0.18",
        "Connection": "close",
    }
    
    print(f"Testing {url}")
    print("=" * 50)
    
    try:
        r = session.get(url, stream=True, timeout=8, headers=headers)
        print(f"Status: {r.status_code}")
        
        icy_headers = {}
        for k, v in r.headers.items():
            if k.lower().startswith('icy-'):
                icy_headers[k] = v
        print(f"ICY headers: {icy_headers}")
        
        if "icy-metaint" in r.headers:
            meta_int = int(r.headers["icy-metaint"])
            print(f"Metadata interval: {meta_int}")
            
            for i in range(5):  # Try 5 times
                print(f"\n--- Block {i+1} ---")
                data = r.raw.read(meta_int)
                meta_len_b = r.raw.read(1)
                if not meta_len_b:
                    print("No metadata byte")
                    break
                meta_len = (meta_len_b[0] if isinstance(meta_len_b, (bytes, bytearray)) else ord(meta_len_b)) * 16
                print(f"Metadata length: {meta_len}")
                if meta_len > 0:
                    meta = r.raw.read(meta_len).rstrip(b"\x00").decode("utf-8", errors="ignore")
                    print(f"Raw metadata: {repr(meta)}")
                    if "StreamTitle=" in meta:
                        stream_title = meta.split("StreamTitle=")[1].split(";")[0].strip("'\"")
                        print(f"StreamTitle: {repr(stream_title)}")
        else:
            print("No ICY metadata available")
            
        r.close()
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
