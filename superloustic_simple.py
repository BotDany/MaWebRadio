#!/usr/bin/env python3

# Version simplifiée du fetcher Superloustic
import requests
import re
from typing import Optional, Tuple
import time
import json
import sys
import os
from dataclasses import dataclass

@dataclass
class RadioMetadata:
    station: str
    title: str
    artist: str
    cover_url: str = ""
    host: str = ""

def get_superloustic_metadata(station_name: str, url: str) -> Optional[RadioMetadata]:
    """Récupère les métadonnées pour Superloustic avec pochette du site"""
    try:
        # Essayer d'abord les métadonnées ICY standard
        headers = {
            "Icy-MetaData": "1",
            "Accept": "*/*",
            "Accept-Language": "fr-FR,fr;q=0.9",
            "Accept-Encoding": "identity",
            "Connection": "keep-alive"
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            meta_int = response.headers.get("icy-metaint", "")
            if meta_int:
                meta_data = response.headers.get("icy-metaint", "").split(";")
                for meta in meta_data:
                    if "StreamTitle=" in meta:
                        stream_title = meta.split("StreamTitle=")[1].split(";")[0].strip("'\"")
                        stream_title = stream_title.strip()
                        
                        if " - " in stream_title:
                            a, t = stream_title.split(" - ", 1)
                            artist = a.strip()
                            title = t.strip()
                        else:
                            title = stream_title
                            artist = station_name
                        
                        if title and title.lower() != "en direct":
                            # Essayer d'extraire la pochette depuis le site Superloustic
                            try:
                                site_response = requests.get("https://www.superloustic.com/", timeout=10)
                                if site_response.status_code == 200:
                                    content = site_response.text
                                    # Chercher spécifiquement dans le div qtmplayer__cover (pochette actuelle)
                                    cover_match = re.search(r'<div id="qtmplayer__cover"[^>]*>.*?<img[^>]+src="([^"]+)"', content)
                                    if cover_match:
                                        cover_url = cover_match.group(1)
                                        print(f"🖼️ Pochette Superloustic actuelle trouvée: {cover_url}")
                                        return RadioMetadata(
                                            station=station_name,
                                            title=title,
                                            artist=artist,
                                            cover_url=cover_url,
                                            host=""
                                        )
                                    else:
                                        print(f"❌ Pas de pochette actuelle trouvée sur le site")
                            except Exception as e:
                                print(f"❌ Erreur extraction pochette Superloustic: {e}")
                            
                            return RadioMetadata(
                                station=station_name,
                                title=title,
                                artist=artist,
                                cover_url=cover_url,
                                host=""
                            )
        
        # Fallback si aucune métadonnée
        return RadioMetadata(
            station=station_name,
            title="En direct",
            artist="Superloustic",
            cover_url="https://www.superloustic.com/wp-content/uploads/2021/09/logo-superloustic-2021.png",
            host=""
        )
        
    except Exception as e:
        print(f"❌ Erreur Superloustic: {e}")
        return RadioMetadata(
            station=station_name,
            title="En direct",
            artist="Superloustic",
            cover_url="https://www.superloustic.com/wp-content/uploads/2021/09/logo-superloustic-2021.png",
            host=""
        )

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        station = sys.argv[1]
        url = sys.argv[2]
        
        result = get_superloustic_metadata(station, url)
        print(json.dumps({
            "station": result.station,
            "title": result.title,
            "artist": result.artist,
            "cover_url": result.cover_url
        }, ensure_ascii=False, indent=2))
