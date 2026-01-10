#!/usr/bin/env python3

# Script pour réparer le fetcher
try:
    with open('radio_metadata_fetcher_fixed_clean.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Trouver et corriger la ligne avec la parenthèse manquante
    lines = content.split('\n')
    
    # Corriger la ligne 1060 - ajouter la parenthèse manquante
    for i, line in enumerate(lines):
        if 'return RadioMetadata(station=station_name, title=title or "En direct", artist=artist or station_name, cover_url=cover_url, host=""' in line:
            lines[i] = '            return RadioMetadata(station=station_name, title=title or "En direct", artist=artist or station_name, cover_url=cover_url, host="")'
            break
    
    with open('radio_metadata_fetcher_fixed_clean.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print('Fetcheur réparé')
except Exception as e:
    print(f'Erreur: {e}')
