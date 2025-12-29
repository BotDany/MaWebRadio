import requests
import urllib3
import ssl
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_megahits_metadata():
    """Récupère les métadonnées du flux Mega Hits une seule fois"""
    url = "https://playerservices.streamtheworld.com/api/livestream-redirect/MEGA_HITSAAC.aac"
    
    try:
        session = requests.Session()
        
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.options |= 0x4
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        adapter = HTTPAdapter(max_retries=Retry(
            total=2,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"]
        ))
        
        session.mount('https://', adapter)
        session.mount('http://', adapter)
        session.verify = False
        
        headers = {
            'User-Agent': 'VLC/3.0.18 LibVLC/3.0.18',
            'Icy-MetaData': '1',
            'Accept': '*/*'
        }
        
        print(f"🔍 Connexion au flux Mega Hits...")
        print(f"URL: {url}\n")
        
        response = session.get(url, headers=headers, stream=True, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Erreur HTTP: {response.status_code}")
            return
            
        if 'icy-metaint' not in response.headers:
            print("❌ Le flux ne supporte pas les métadonnées ICY")
            print("En-têtes reçus:")
            for k, v in response.headers.items():
                print(f"  {k}: {v}")
            return
            
        meta_interval = int(response.headers['icy-metaint'])
        print("✅ Connexion réussie")
        print(f"📊 Intervalle des métadonnées: {meta_interval} octets")
        print(f"📻 Station: {response.headers.get('icy-name', 'Mega Hits')}")
        print(f"🎵 Genre: {response.headers.get('icy-genre', 'Misc')}")
        print("⏳ Récupération des métadonnées...\n")
        
        audio_data = response.raw.read(meta_interval)
        if not audio_data:
            print("❌ Aucune donnée audio reçue")
            return
            
        meta_length_byte = response.raw.read(1)
        if not meta_length_byte:
            print("❌ Impossible de lire la longueur des métadonnées")
            return
            
        meta_length = ord(meta_length_byte) * 16
        
        if meta_length > 0:
            metadata = response.raw.read(meta_length).rstrip(b'\x00').decode('utf-8', errors='ignore')
            
            print("🔍 Métadonnées brutes:")
            print(f"{metadata}\n")
            
            if 'StreamTitle=' in metadata:
                stream_title = metadata.split('StreamTitle=')[1].split(';')[0].strip("'\"")
                
                if not stream_title or "Mega Hits" in stream_title:
                    print("📻 En direct sur Mega Hits")
                else:
                    if ' - ' in stream_title:
                        artist, title = stream_title.split(' - ', 1)
                        print(f"👤 Artiste: {artist.strip()}")
                        print(f"🎶 Titre: {title.strip()}")
                    else:
                        print(f"📝 Info: {stream_title.strip()}")
            else:
                print("ℹ️ Aucune information de titre trouvée")
                
            if 'adw_ad=' in metadata and 'true' in metadata:
                print("\n📢 Publicité en cours")
        else:
            print("ℹ️ Aucune métadonnée disponible")
            
    except Exception as e:
        print(f"\n❌ Erreur: {str(e)}")
    finally:
        if 'response' in locals():
            response.close()
        print("\n✅ Analyse terminée")

if __name__ == "__main__":
    print("=" * 60)
    print(" Détection unique des métadonnées Mega Hits")
    print("=" * 60)
    get_megahits_metadata()