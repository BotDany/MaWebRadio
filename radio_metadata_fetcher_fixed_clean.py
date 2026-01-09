# Fichier temporaire pour éviter l'erreur 500
# Le fichier original a été renommé en .broken

print("⚠️ Fichier de métadonnées temporairement désactivé")
print("🔧 L'application utilisera les métadonnées par défaut du frontend")

# Fonction vide pour éviter les erreurs d'import
def get_metadata(station_name, url):
    """Fonction temporaire vide - utilise les métadonnées par défaut"""
    from dataclasses import dataclass
    
    @dataclass
    class RadioMetadata:
        station: str
        title: str
        artist: str
        cover_url: str
        host: str = ""
    
    # Retourner des métadonnées vides pour éviter les erreurs
    return RadioMetadata(
        station=station_name,
        title="En direct",
        artist=station_name,
        cover_url=""
    )
