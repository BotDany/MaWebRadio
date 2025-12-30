from radio_metadata_fetcher_fixed_clean import RadioFetcher
import json
from datetime import datetime

# Liste complète des radios de final_app.py
RADIOS = [
    ("RTL", "http://streaming.radio.rtl.fr/rtl-1-44-128"),
    ("Chante France-80s", "https://chantefrance80s.ice.infomaniak.ch/chantefrance80s-128.mp3"),
    ("100% Radio 80", "http://100radio-80.ice.infomaniak.ch/100radio-80-128.mp3"),
    ("Nostalgie 80", "https://scdn.nrjaudio.fm/fr/30601/mp3_128.mp3"),
    ("RFM 80-90", "http://rfm-live-mp3-128.scdn.arkena.com/rfm.mp3"),
    ("RTL2 80s", "http://streaming.radio.rtl2.fr/rtl2-1-44-128"),
    ("NRJ 80s", "https://scdn.nrjaudio.fm/fr/30601/mp3_128.mp3"),
    ("Virgin Radio 80s", "https://ais-live.cloud-services.asso.fr/virginradio.mp3"),
    ("Bide Et Musique", "https://relay1.bide-et-musique.com:9300/bm.mp3"),
    ("Flash 80 Radio", "https://manager7.streamradio.fr:1985/stream"),
    ("Mega Hits", "https://playerservices.streamtheworld.com/api/livestream-redirect/MEGA_HITSAAC_SC"),
    ("Radio Comercial", "https://stream-icy.bauermedia.pt/comercial.mp3"),
    ("Superloustic", "https://radio6.pro-fhi.net/live/SUPERLOUSTIC"),
    ("Génération Dorothée", "https://stream.votreradiosurlenet.eu/generationdorothee.mp3"),
    ("Top 80 Radio", "https://securestreams6.autopo.st:2321/"),
    ("Chansons Oubliées Où Presque", "https://manager7.streamradio.fr:2850/stream"),
    # Ajout de Générikds avec l'URL directe
    ("Générikds", "https://listen.radioking.com/radio/497599/stream/554719"),
]

def test_all_radios():
    fetcher = RadioFetcher()
    
    print("🎵 RADIO PLAYER - TEST COMPLET DES MÉTADONNÉES")
    print("=" * 80)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Test de {len(RADIOS)} radios")
    print("=" * 80)
    
    results = []
    success_count = 0
    direct_count = 0
    error_count = 0
    
    for i, (station, url) in enumerate(RADIOS, 1):
        print(f"\n{i:2d}. 🎵 {station}")
        print(f"    URL: {url}")
        
        try:
            metadata = fetcher.get_metadata(station, url)
            
            if metadata and metadata.title and metadata.title.lower() != 'en direct':
                status = "✅ SUCCÈS"
                success_count += 1
                
                # Formatter l'affichage
                artist_display = metadata.artist[:40] + "..." if len(metadata.artist) > 40 else metadata.artist
                title_display = metadata.title[:40] + "..." if len(metadata.title) > 40 else metadata.title
                
                print(f"    {status} | {artist_display} - {title_display}")
                
                if metadata.cover_url and metadata.cover_url != "":
                    print(f"    📱 Pochette: Oui")
                else:
                    print(f"    📱 Pochette: Non")
                    
                if metadata.host and metadata.host != "":
                    print(f"    🎙️  Host: {metadata.host}")
                
                results.append({
                    'station': station,
                    'status': 'success',
                    'artist': metadata.artist,
                    'title': metadata.title,
                    'cover_url': metadata.cover_url,
                    'host': metadata.host
                })
                
            else:
                status = "⚠️  EN DIRECT"
                direct_count += 1
                print(f"    {status} | Pas de métadonnées spécifiques")
                
                results.append({
                    'station': station,
                    'status': 'direct',
                    'artist': station,
                    'title': 'En direct',
                    'cover_url': '',
                    'host': ''
                })
                
        except Exception as e:
            status = "❌ ERREUR"
            error_count += 1
            error_msg = str(e)[:50] + "..." if len(str(e)) > 50 else str(e)
            print(f"    {status} | {error_msg}")
            
            results.append({
                'station': station,
                'status': 'error',
                'artist': '',
                'title': f'Erreur: {str(e)}',
                'cover_url': '',
                'host': ''
            })
    
    # Résumé final
    print("\n" + "=" * 80)
    print("📊 RÉSUMÉ COMPLET")
    print("=" * 80)
    print(f"✅ Succès métadonnées: {success_count} radios")
    print(f"⚠️  En direct: {direct_count} radios")
    print(f"❌ Erreur: {error_count} radios")
    print(f"📈 Total: {len(RADIOS)} radios")
    print(f"🎯 Taux de réussite: {(success_count/len(RADIOS)*100):.1f}%")
    
    # Détail des succès
    if success_count > 0:
        print("\n🎵 RADIOS AVEC MÉTADONNÉES COMPLÈTES:")
        for result in results:
            if result['status'] == 'success':
                print(f"   • {result['station']}: {result['artist']} - {result['title']}")
    
    # Détail des radios en direct
    if direct_count > 0:
        print("\n📻 RADIOS EN DIRECT:")
        for result in results:
            if result['status'] == 'direct':
                print(f"   • {result['station']}")
    
    # Erreurs
    if error_count > 0:
        print("\n❌ ERREURS:")
        for result in results:
            if result['status'] == 'error':
                print(f"   • {result['station']}: {result['title']}")
    
    # Export JSON
    print(f"\n💾 Export JSON: {len(results)} radios sauvegardées")
    with open('radio_metadata_report.json', 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_radios': len(RADIOS),
            'success_count': success_count,
            'direct_count': direct_count,
            'error_count': error_count,
            'success_rate': success_count/len(RADIOS)*100,
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print("=" * 80)
    print("🎉 Test terminé !")

if __name__ == "__main__":
    test_all_radios()
