#!/usr/bin/env python3
"""
Script pour afficher toutes les radios avec leurs métadonnées en temps réel
"""

import time
from radio_metadata_fetcher_fixed_clean import RadioFetcher

def show_all_metadata():
    """Affiche les métadonnées de toutes les radios"""
    print("🎵 MÉTADONNÉES EN TEMPS RÉEL - TOUTES LES RADIOS")
    print("=" * 80)
    
    # Liste de toutes les radios
    fetcher = RadioFetcher()
    
    radios = [
        ("100% Radio 80", "http://100radio-80.ice.infomaniak.ch/100radio-80-128.mp3"),
        ("Bide Et Musique", "https://relay1.bide-et-musique.com:9300/bm.mp3"),
        ("Chansons Oubliées Où Presque", "https://manager7.streamradio.fr:2850/stream"),
        ("Chante France-80s", "https://chantefrance80s.ice.infomaniak.ch/chantefrance80s-128.mp3"),
        ("Top 80 Radio", "https://securestreams6.autopo.st:2321/stream.mp3"),
        ("Nostalgie Romania", "https://nl.digitalrm.pt:8140/stream"),
        ("Génération Dorothée", "https://stream.votreradiosurlenet.eu/generationdorothee.mp3"),
        ("Générikds", "https://listen.radioking.com/radio/497599/stream/554719"),
        ("Made In 80", "https://listen.radioking.com/radio/260719/stream/305509"),
        ("Mega Hits", "https://playerservices.streamtheworld.com/api/livestream-redirect/MEGA_HITSAAC_SC?csegid=2&dist=rmultimedia_apps&gdpr=1&bundle-id=pt.megahits.ios"),
        ("Nostalgie-Les 80 Plus Grand Tubes", "https://streaming.nrjaudio.fm/ouwg8usk6j4d"),
        ("Nostalgie-Les Tubes 80 N1", "https://streaming.nrjaudio.fm/ouo6im7nfibk"),
        ("Radio Comercial", "https://stream-icy.bauermedia.pt/comercial.mp3"),
        ("Radio Gérard", "https://radiosurle.net:8765/radiogerard"),
        ("RTL", "http://streaming.radio.rtl.fr/rtl-1-44-128"),
        ("Superloustic", "https://radio6.pro-fhi.net/live/SUPERLOUSTIC"),
        ("Supernana", "https://radiosurle.net:8765/showsupernana"),
    ]
    
    print(f"📻 Test de {len(radios)} radios...")
    print()
    
    for i, (name, url) in enumerate(radios, 1):
        print(f"🎵 {i:2d}. {name}")
        print(f"🔗 URL: {url}")
        
        try:
            # Récupérer les métadonnées
            metadata = fetcher.get_metadata(name, url)
            
            if metadata and metadata.title and metadata.artist:
                print(f"🎤 ARTISTE: {metadata.artist}")
                print(f"🎶 TITRE  : {metadata.title}")
                if metadata.cover_url:
                    print(f"🖼️ COVER  : {metadata.cover_url}")
                else:
                    print(f"🖼️ COVER  : Non disponible")
            else:
                print(f"🎙️ STATUT  : En direct (pas de métadonnées)")
                
        except Exception as e:
            print(f"❌ ERREUR  : {str(e)}")
        
        print("-" * 60)
        print()
    
    print("✅ Test terminé !")
    print("💡 Les métadonnées sont mises en cache pour 5 secondes")

if __name__ == "__main__":
    show_all_metadata()
