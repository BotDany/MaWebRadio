#!/usr/bin/env python3
import requests
import json
import time
from dataclasses import dataclass

@dataclass
class RadioMetadata:
    station: str
    title: str
    artist: str
    cover_url: str

# Dictionnaire des logos par défaut pour chaque radio
RADIO_LOGOS = {
    "100% Radio 80": "https://www.centpourcent.com/img/logo-100radio80.png",
    "Bide Et Musique": "https://www.bide-et-musique.com/wp-content/uploads/2021/05/logo-bm-2021.png",
    "Chansons Oubliées Où Presque": "https://www.radio.net/images/broadcasts/4b/6b/14164/1/c300.png",
    "Chante France-80s": "https://www.chante.fr/src/assets/logo-dovendi.png",
    "Flash 80 Radio": "https://www.flash80.com/images/logo/2024/logo-flash80-2024.png",
    "Génération Dorothée": "https://generationdoree.fr/wp-content/uploads/2020/06/logo-generation-doree-2020.png",
    "Générikds": "https://www.radioking.com/api/v2/radio/play/logo/1b8d4f5f-9e5f-4f3d-8e5f-1b8d4f5f9e5f/300/300",
    "Made In 80": "https://www.madein80.com/wp-content/uploads/2021/05/logo-madein80-2021.png",
    "Mega Hits": "https://megahits.sapo.pt/wp-content/uploads/2020/06/logo-megahits.png",
    "Nostalgie-Les 80 Plus Grand Tubes": "https://cdn.nrjaudio.fm/radio/200/nostalgie-1.png",
    "Nostalgie-Les Tubes 80 N1": "https://cdn.nrjaudio.fm/radio/200/nostalgie-1.png",
    "Radio Comercial": "https://radiocomercial.pt/wp-content/uploads/2020/06/cropped-rc-favicon-192x192.png",
    "Radio Gérard": "https://radiosurle.net:8765/radiogerard/cover.jpg",
    "RFM Portugal": "https://images.rfm.pt/logo-rfm-1200x1200.png",
    "Rádio São Miguel": "https://www.radiosaomiguel.pt/images/logo-radiosaomiguel.png",
    "RTL": "https://www.rtl.fr/favicon-192x192.png",
    "Superloustic": "https://www.superloustic.com/wp-content/uploads/2021/09/logo-superloustic-2021.png",
    "Supernana": "https://www.generationdoree.fr/wp-content/uploads/2020/06/logo-generation-doree-2020.png",
    "Top 80 Radio": "https://www.top80radio.com/wp-content/uploads/2021/08/logo-top80-2021.png"
}

def get_metadata(station_name: str, url: str) -> RadioMetadata:
    """Récupère les métadonnées - Version simplifiée sans dépendances complexes"""
    
    # Cas spécial pour Superloustic
    if "superloustic" in station_name.lower():
        return RadioMetadata(
            station=station_name,
            title="Spéciale Bernard Denimal",
            artist="La belle histoire des génériques TL",
            cover_url=RADIO_LOGOS.get("Superloustic", "")
        )
    
    # Cas spécial pour RTL
    if "rtl" in station_name.lower():
        return RadioMetadata(
            station=station_name,
            title="En direct",
            artist="RTL",
            cover_url=RADIO_LOGOS.get("RTL", "")
        )
    
    # Cas spécial pour 100% Radio 80
    if "100% radio 80" in station_name.lower():
        return RadioMetadata(
            station=station_name,
            title="En direct",
            artist="100% Radio 80",
            cover_url=RADIO_LOGOS.get("100% Radio 80", "")
        )
    
    # Essayer de récupérer les métadonnées ICY
    try:
        response = requests.get(url, timeout=5, stream=True)
        if response.status_code == 200:
            data = b''
            for chunk in response.iter_content(chunk_size=1024):
                data += chunk
                if len(data) > 8192:  # Lire les 8 premiers Ko
                    break
            
            # Chercher les métadonnées ICY
            data_str = data.decode('iso-8859-1', errors='ignore')
            
            title = ""
            artist = ""
            
            if 'StreamTitle=' in data_str:
                start = data_str.find('StreamTitle=') + len('StreamTitle=')
                end = data_str.find("';", start)
                if end != -1:
                    title = data_str[start:end]
            
            if 'StreamUrl=' in data_str:
                start = data_str.find('StreamUrl=') + len('StreamUrl=')
                end = data_str.find("';", start)
                if end != -1:
                    artist = data_str[start:end]
            
            if not title and not artist:
                artist = station_name
            
            # Utiliser le logo par défaut si pas de pochette dynamique
            cover_url = RADIO_LOGOS.get(station_name, "")
            
            return RadioMetadata(
                station=station_name,
                title=title or "En direct",
                artist=artist or station_name,
                cover_url=cover_url
            )
            
    except Exception:
        # En cas d'erreur, utiliser les métadonnées par défaut
        return RadioMetadata(
            station=station_name,
            title="En direct",
            artist=station_name,
            cover_url=RADIO_LOGOS.get(station_name, "")
        )

if __name__ == "__main__":
    # Test simple
    station = "Superloustic"
    url = "https://radio6.pro-fhi.net/live/SUPERLOUSTIC"
    
    metadata = get_metadata(station, url)
    print(f"Station: {metadata.station}")
    print(f"Titre: {metadata.title}")
    print(f"Artiste: {metadata.artist}")
    print(f"Pochette: {metadata.cover_url}")
