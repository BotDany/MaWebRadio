import requests
import re
import json

def get_superloustic_metadata():
    url = "https://www.superloustic.com"
    
    try:
        # 1. Récupérer la page principale
        print(f"Récupération de {url}...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # 2. Essayer de trouver l'URL de l'API du lecteur
        print("Recherche de l'API du lecteur...")
        
        # Essayer de trouver des scripts qui pourraient contenir l'URL de l'API
        script_pattern = re.compile(r'https?://[^"\']+?/wp-json/radio-player/[^"\']+')
        api_urls = script_pattern.findall(response.text)
        
        if not api_urls:
            # Essayer un autre motif commun pour les API de lecteur
            script_pattern = re.compile(r'https?://[^"\']+?/api/[^"\']+')
            api_urls = script_pattern.findall(response.text)
        
        if api_urls:
            print(f"URLs d'API potentielles trouvées : {api_urls}")
            
            # Essayer chaque URL d'API trouvée
            for api_url in api_urls[:3]:  # Essayer les 3 premières URLs
                try:
                    print(f"\nEssai avec l'API : {api_url}")
                    api_response = requests.get(api_url, timeout=5)
                    
                    if api_response.status_code == 200:
                        try:
                            data = api_response.json()
                            print("Réponse de l'API (format JSON) :")
                            print(json.dumps(data, indent=2, ensure_ascii=False))
                        except:
                            print("Réponse de l'API (texte brut) :")
                            print(api_response.text[:500])  # Afficher les 500 premiers caractères
                except Exception as e:
                    print(f"Erreur avec l'API {api_url} : {e}")
        else:
            print("Aucune URL d'API trouvée dans le code source.")
        
        # 3. Essayer de trouver des métadonnées directement dans la page
        print("\nRecherche de métadonnées dans le code source...")
        
        # Chercher des modèles courants de métadonnées
        patterns = {
            'titre': r'(?i)(?:titre|title)[\"\']\s*:\s*[\'"]([^\'"]+)[\'"]',
            'artiste': r'(?i)(?:artiste|artist)[\"\']\s*:\s*[\'"]([^\'"]+)[\'"]',
            'cover': r'(?i)(?:cover|image|pochette)[\"\']\s*:\s*[\'"]([^\'"]+)[\'"]',
            'now_playing': r'(?i)now_?playing[\'\"]?\s*:\s*[\'"]([^\'"]+)[\'"]'
        }
        
        for name, pattern in patterns.items():
            matches = re.findall(pattern, response.text)
            if matches:
                print(f"\n{name.capitalize()} trouvé(s) :")
                for i, match in enumerate(matches[:3], 1):  # Afficher les 3 premières correspondances
                    print(f"  {i}. {match}")
        
        # 4. Chercher des balises meta avec des métadonnées
        print("\nRecherche de balises meta...")
        meta_pattern = r'<meta\s+(?:[^>]*?\s+)?(?:name|property)=[\'"]([^\'"]+)[\'"][^>]*?\s+content=[\'"]([^\'"]+)[\'"][^>]*?>'
        meta_matches = re.findall(meta_pattern, response.text)
        
        if meta_matches:
            print("Balises meta trouvées :")
            for name, content in meta_matches[:10]:  # Afficher les 10 premières
                if any(keyword in name.lower() for keyword in ['title', 'description', 'og:', 'music:', 'song:']):
                    print(f"  {name}: {content[:100]}{'...' if len(content) > 100 else ''}")
        
        # 5. Essayer de trouver des données JSON dans les scripts
        print("\nRecherche de données JSON dans les scripts...")
        script_pattern = r'<script[^>]*>\s*(var\s+\w+\s*=\s*\{.*?\})\s*</script>'
        script_matches = re.findall(script_pattern, response.text, re.DOTALL)
        
        if script_matches:
            print(f"Données JSON potentielles trouvées dans {len(script_matches)} scripts.")
            for i, script in enumerate(script_matches[:2], 1):  # Afficher les 2 premiers scripts
                print(f"\nScript {i} (début) : {script[:200]}...")
        
    except Exception as e:
        print(f"Erreur : {e}")

if __name__ == "__main__":
    get_superloustic_metadata()
