#!/usr/bin/env python3

from radio_metadata_fetcher_fixed_clean import RadioFetcher

def test_superloustic_metadata():
    print("🔍 Test de récupération des métadonnées pour Superloustic")
    
    # Créer une instance de RadioFetcher
    fetcher = RadioFetcher()
    
    # Appeler directement la méthode _get_superloustic_metadata
    print("\n1. Test de _get_superloustic_metadata:")
    metadata = fetcher._get_superloustic_metadata("Superloustic")
    
    if metadata:
        print("✅ Métadonnées récupérées avec succès!")
        print(f"   Artiste: {metadata.artist}")
        print(f"   Titre: {metadata.title}")
        print(f"   Pochette: {metadata.cover_url}")
    else:
        print("❌ Impossible de récupérer les métadonnées")
    
    # Tester avec get_metadata qui utilise le cache
    print("\n2. Test de get_metadata avec cache:")
    url = "https://radio6.pro-fhi.net/radio/9004/stream"
    metadata = fetcher.get_metadata("Superloustic", url)
    
    if metadata:
        print("✅ Métadonnées récupérées via get_metadata:")
        print(f"   Artiste: {metadata.artist}")
        print(f"   Titre: {metadata.title}")
        print(f"   Pochette: {metadata.cover_url}")
    else:
        print("❌ Impossible de récupérer les métadonnées via get_metadata")

if __name__ == "__main__":
    test_superloustic_metadata()
