#!/usr/bin/env python3
import requests
import re
import json
import sys
from bs4 import BeautifulSoup

def test_rtl_direct_page():
    """Extract metadata from RTL direct page"""
    url = "https://www.rtl.fr/direct"
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9",
    }
    
    try:
        print(f"Fetching: {url}")
        r = requests.get(url, timeout=10, headers=headers)
        print(f"Status: {r.status_code}")
        
        if r.status_code != 200:
            print("Failed to fetch page")
            return
        
        content = r.text
        
        # Look for JSON data in script tags
        json_patterns = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL | re.IGNORECASE)
        
        for i, script_content in enumerate(json_patterns):
            # Look for JSON objects with artist/title
            if '"artist"' in script_content or '"title"' in script_content:
                print(f"\n=== Script {i+1} contains artist/title ===")
                
                # Try to extract JSON patterns
                json_matches = re.findall(r'\{[^{}]*["\']artist["\'][^{}]*\}', script_content, re.IGNORECASE)
                for match in json_matches:
                    try:
                        data = json.loads(match)
                        print(f"Found JSON: {json.dumps(data, indent=2)}")
                    except:
                        print(f"Raw JSON pattern: {match[:200]}...")
        
        # Look for specific RTL patterns
        rtl_patterns = [
            r'"currentSong":\s*\{[^}]+\}',
            r'"nowPlaying":\s*\{[^}]+\}',
            r'"track":\s*\{[^}]+\}',
            r'"song":\s*\{[^}]+\}',
            r'currentTrack[^}]*\{[^}]+\}',
            r'nowPlaying[^}]*\{[^}]+\}',
        ]
        
        print(f"\n=== Looking for RTL patterns ===")
        for pattern in rtl_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                print(f"Pattern {pattern}:")
                for match in matches[:3]:  # First 3 matches
                    try:
                        # Try to parse as JSON
                        json_str = re.search(r'\{.*\}', match, re.DOTALL)
                        if json_str:
                            data = json.loads(json_str.group())
                            print(f"  Parsed: {json.dumps(data, indent=4)}")
                        else:
                            print(f"  Raw: {match[:200]}...")
                    except:
                        print(f"  Raw: {match[:200]}...")
                print()
        
        # Look for HTML elements with specific classes
        soup = BeautifulSoup(content, 'html.parser')
        
        # Common selectors for now playing info
        selectors = [
            '.now-playing',
            '.current-song',
            '.track-info',
            '.song-title',
            '.artist-name',
            '[data-track]',
            '[data-artist]',
            '[data-title]',
        ]
        
        print(f"=== Looking for HTML elements ===")
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                print(f"Selector {selector}:")
                for elem in elements[:3]:
                    print(f"  {elem.get_text(strip=True)[:100]}")
                    print(f"  Attributes: {elem.attrs}")
                print()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_rtl_direct_page()
