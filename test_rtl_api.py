#!/usr/bin/env python3
import requests
import json
import sys

def test_radio_metadata_service():
    """Test radio-metadata.fr service for RTL"""
    urls = [
        "https://radio-metadata.fr/api/v1/nowplaying/rtl",
        "https://radio-metadata.fr/api/v1/station/rtl",
        "https://radio-metadata.fr/api/v1/rtl",
        "https://api.radio-metadata.fr/v1/nowplaying/rtl",
        "https://api.radio-metadata.fr/v1/station/rtl",
    ]
    
    for url in urls:
        try:
            print(f"Testing: {url}")
            r = requests.get(url, timeout=5)
            print(f"  Status: {r.status_code}")
            if r.status_code == 200:
                try:
                    data = r.json()
                    print(f"  Response: {json.dumps(data, indent=2)[:300]}...")
                except:
                    print(f"  Response: {r.text[:200]}...")
            else:
                print(f"  Error: {r.text[:100]}")
            print()
        except Exception as e:
            print(f"  Exception: {e}")
            print()

def test_rtl_website():
    """Test RTL website for embedded metadata"""
    urls = [
        "https://www.rtl.fr/direct",
        "https://www.rtl.fr/radio/direct",
        "https://www.rtl.fr/api/direct/now-playing",
        "https://www.rtl.fr/api/radio/now-playing",
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "fr-FR,fr;q=0.9",
    }
    
    for url in urls:
        try:
            print(f"Testing: {url}")
            r = requests.get(url, timeout=5, headers=headers)
            print(f"  Status: {r.status_code}")
            if r.status_code == 200:
                content = r.text
                if "artist" in content.lower() or "title" in content.lower():
                    print("  ✓ Contains artist/title keywords")
                    # Look for JSON patterns
                    import re
                    json_patterns = re.findall(r'\{[^{}]*["\']artist["\'][^{}]*\}', content, re.IGNORECASE)
                    if json_patterns:
                        print(f"  Found JSON: {json_patterns[0][:200]}...")
                else:
                    print("  - No artist/title keywords found")
            else:
                print(f"  Error: {r.text[:100]}")
            print()
        except Exception as e:
            print(f"  Exception: {e}")
            print()

def main():
    print("=== Testing radio-metadata.fr service ===")
    test_radio_metadata_service()
    
    print("=== Testing RTL website ===")
    test_rtl_website()

if __name__ == "__main__":
    main()
