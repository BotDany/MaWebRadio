import json
import os
import time
from flask import Flask, render_template, jsonify, request, flash, redirect, url_for
from radio_metadata_fetcher_fixed_clean import RadioFetcher
from database_config import load_radios, save_radios

class RadioState:
    def __init__(self):
        self.current_station = None
        self.current_url = None
        self.is_playing = False
        self.fetcher = RadioFetcher()

app = Flask(__name__)
app.secret_key = 'radio_admin_secret_key_2025'
radio_state = RadioState()

print("🚀 Démarrage de l'application webradio...")

@app.route('/')
def index():
    radios = load_radios()
    return render_template('index.html', stations=radios)

@app.route('/api/metadata')
def metadata():
    import requests
    print(f"🔍 API appelée - station: {radio_state.current_station}, playing: {radio_state.is_playing}")
    
    if radio_state.current_station and radio_state.current_url and radio_state.is_playing:
        try:
            station_lower = radio_state.current_station.lower()
            
            if "generikids" in station_lower or "générikds" in station_lower:
                try:
                    api_url = "https://api.radioking.io/widget/radio/generikids/track/current"
                    response = requests.get(api_url, timeout=3)
                    
                    if response.status_code == 200:
                        data = response.json()
                        metadata = type('RadioMetadata', (), {
                            'artist': data.get('artist', radio_state.current_station),
                            'title': data.get('title', 'En direct'),
                            'cover_url': data.get('cover', ''),
                            'station': radio_state.current_station,
                            'host': ''
                        })()
                        print(f"🎵 API directe: {metadata.artist} - {metadata.title}")
                    else:
                        metadata = None
                except Exception as e:
                    print(f"❌ Erreur API directe: {e}")
                    metadata = None
            else:
                metadata = radio_state.fetcher.get_metadata(radio_state.current_station, radio_state.current_url)
            
            if metadata and metadata.title and metadata.title.lower() != "en direct":
                result = {
                    'status': 'success',
                    'artist': metadata.artist or radio_state.current_station,
                    'title': metadata.title,
                    'cover_url': metadata.cover_url or '',
                    'station': radio_state.current_station,
                    'is_playing': True
                }
                return jsonify(result)
            else:
                result = {
                    'status': 'no_data',
                    'artist': radio_state.current_station,
                    'title': 'En direct',
                    'cover_url': '',
                    'station': radio_state.current_station,
                    'is_playing': True
                }
                return jsonify(result)
        except Exception as e:
            result = {
                'status': 'error',
                'artist': radio_state.current_station,
                'title': 'En direct',
                'cover_url': '',
                'station': radio_state.current_station,
                'is_playing': True
            }
            return jsonify(result)
    
    result = {
        'status': 'no_data',
        'is_playing': False,
        'station': radio_state.current_station
    }
    return jsonify(result)

@app.route('/api/play')
def play():
    station = request.args.get('station')
    url = request.args.get('url')
    
    if station and url:
        radio_state.current_station = station
        radio_state.current_url = url
        radio_state.is_playing = True
        print(f"▶️ Play: {station}")
        return jsonify({
            'status': 'playing',
            'station': station,
            'url': url
        })
    
    return jsonify({'status': 'error', 'message': 'Station manquante'})

@app.route('/api/stop')
def stop():
    station = radio_state.current_station
    radio_state.current_station = None
    radio_state.current_url = None
    radio_state.is_playing = False
    
    print(f"⏹️ Stop: {station}")
    return jsonify({'status': 'stopped'})

@app.route('/api/history/<int:count>')
def get_history(count=10):
    """Récupérer l'historique des musiques passées"""
    if radio_state.current_station and radio_state.current_url:
        try:
            # Utiliser le fetcher global
            history = radio_state.fetcher.get_history(radio_state.current_station, radio_state.current_url, count)
            
            if history:
                return jsonify({
                    'status': 'success',
                    'history': history
                })
            else:
                return jsonify({
                    'status': 'no_data',
                    'message': 'Aucun historique disponible'
                })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Erreur lors de la récupération de l\'historique: {str(e)}'
            })
    else:
        return jsonify({
            'status': 'no_station',
            'message': 'Aucune radio sélectionnée'
        })

@app.route('/admin/simple-test')
def simple_test():
    """Test simple pour vérifier si le backend fonctionne"""
    try:
        print("🔍 simple_test: Test simple du backend")
        return jsonify({
            'status': 'success',
            'message': 'Backend fonctionne',
            'timestamp': time.time()
        })
    except Exception as e:
        print(f"❌ ERREUR simple_test: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/reset-db', methods=['GET', 'POST'])
def reset_database():
    """Forcer la réinitialisation de la base de données"""
    try:
        print("🔄 API /admin/reset-db: Réinitialisation forcée de la base de données...")
        from database_config import init_database
        success = init_database()
        
        if success:
            print("✅ Base de données réinitialisée avec succès")
            return jsonify({'status': 'success', 'message': 'Base de données réinitialisée'})
        else:
            print("❌ Erreur lors de la réinitialisation")
            return jsonify({'status': 'error', 'message': 'Erreur lors de la réinitialisation'}), 500
    except Exception as e:
        print(f"❌ ERREUR API /admin/reset-db: {str(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

# Routes d'administration
@app.route('/admin')
def admin():
    """Page d'administration des radios"""
    try:
        print("🔍 API /admin: Début de la requête")
        radios = load_radios()
        print(f"📊 API /admin: {len(radios)} radios chargées")
        
        # Convertir les radios au format {station, url, logo}
        formatted_radios = []
        for radio in radios:
            print(f"🔍 Traitement radio: {radio}")
            if len(radio) >= 3:
                formatted_radios.append({
                    'station': radio[0],
                    'url': radio[1], 
                    'logo': radio[2]
                })
                print(f"✅ Radio avec logo: {radio[0]} -> {radio[2]}")
            elif len(radio) == 2:
                formatted_radios.append({
                    'station': radio[0],
                    'url': radio[1], 
                    'logo': ''
                })
                print(f"✅ Radio sans logo: {radio[0]}")
            else:
                formatted_radios.append({
                    'station': radio[0],
                    'url': radio[1], 
                    'logo': ''
                })
                print(f"⚠️ Radio format inattendu: {radio}")
        
        print(f"📋 API /admin: {len(formatted_radios)} radios formatées")
        return jsonify(formatted_radios)
    except Exception as e:
        print(f"❌ ERREUR API /admin: {str(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/add', methods=['POST'])
def add_radio():
    """Ajouter une nouvelle radio"""
    name = request.form.get('name')
    url = request.form.get('url')
    logo = request.form.get('logo')
    
    if name and url:
        radios = load_radios()
        if logo:
            radios.append([name, url, logo])
        else:
            radios.append([name, url])
        
        if save_radios(radios):
            flash(f'Radio "{name}" ajoutée avec succès!', 'success')
        else:
            flash(f'Erreur lors de l\'ajout de la radio "{name}"', 'error')
    else:
        flash('Veuillez remplir tous les champs obligatoires', 'error')
    
    return redirect(url_for('admin'))
@app.route('/admin/test-debug', methods=['POST'])
def test_debug():
    """Route de test pour vérifier la réception des données"""
    try:
        print("🔍 test_debug: Début test de réception des données")
        
        # Afficher toutes les données du formulaire
        print("📝 test_debug: Données reçues:")
        for key, value in request.form.items():
            print(f"   - {key}: '{value}'")
        
        # Afficher les fichiers
        print("📁 test_debug: Fichiers reçus:")
        for key, file in request.files.items():
            print(f"   - {key}: {file.filename}")
        
        return jsonify({
            'status': 'success',
            'message': 'Test réussi',
            'form_data': dict(request.form),
            'files': {key: file.filename for key, file in request.files.items()}
        })
    except Exception as e:
        print(f"❌ ERREUR test_debug: {str(e)}")
        import traceback
        print(f"❌ Traceback test_debug: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/edit/<radio_name>', methods=['POST'])
def edit_radio(radio_name):
    """Modifier une radio existante"""
    try:
        print(f"🔍 edit_radio: Début modification pour '{radio_name}'")
        
        # Décoder le nom de la radio (gère les deux cas: encodé et non encodé)
        import urllib.parse
        radio_name = urllib.parse.unquote(radio_name)
        print(f"🔍 edit_radio: Nom décodé: '{radio_name}'")
        
        # Charger les radios existantes
        radios = load_radios()
        print(f"📊 edit_radio: {len(radios)} radios chargées depuis la base")
        
        # Trouver la radio à modifier
        for i, radio_data in enumerate(radios):
            print(f"🔍 edit_radio: Vérification radio {i}: {radio_data}")
            if radio_data[0] == radio_name:
                print(f"✅ edit_radio: Radio trouvée à l'index {i}: {radio_data}")
                
                new_name = request.form.get('name')
                new_url = request.form.get('url')
                new_logo = request.form.get('logo')
                
                print(f"📝 edit_radio: Données reçues:")
                print(f"   - new_name: '{new_name}'")
                print(f"   - new_url: '{new_url}'")
                print(f"   - new_logo: '{new_logo}'")
                
                if new_name and new_url:
                    # Mettre à jour avec le logo si fourni
                    if new_logo:
                        print(f"📝 edit_radio: Mise à jour avec logo: {new_name}, {new_url}, {new_logo}")
                        radios[i] = [new_name, new_url, new_logo]
                    else:
                        print(f"📝 edit_radio: Mise à jour sans logo: {new_name}, {new_url}")
                        # Garder le logo existant si pas de nouveau logo
                        if len(radio_data) > 2:
                            radios[i] = [new_name, new_url, radio_data[2]]
                            print(f"📝 edit_radio: Logo existant conservé: {radio_data[2]}")
                        else:
                            radios[i] = [new_name, new_url, '']
                            print(f"📝 edit_radio: Aucun logo existant, création vide")
                    
                    print(f"💾 edit_radio: Tentative de sauvegarde de {len(radios)} radios...")
                    if save_radios(radios):
                        print(f"✅ edit_radio: Sauvegarde réussie pour '{radio_name}'")
                        return jsonify({
                            'status': 'success',
                            'message': f'Radio "{radio_name}" modifiée en "{new_name}" avec succès!'
                        })
                    else:
                        print(f"❌ edit_radio: Erreur lors de la sauvegarde pour '{radio_name}'")
                        return jsonify({
                            'status': 'error',
                            'message': f'Erreur lors de la modification de la radio "{radio_name}"'
                        }), 500
                else:
                    print(f"❌ edit_radio: Champs obligatoires manquants pour '{radio_name}'")
                    return jsonify({
                        'status': 'error',
                        'message': 'Le nom et l\'URL sont obligatoires'
                    }), 400
                break
        else:
            print(f"❌ edit_radio: Radio '{radio_name}' non trouvée dans {len(radios)} radios")
            for i, (name, url) in enumerate(radios):
                print(f"   - Radio {i}: '{name}'")
            return jsonify({
                'status': 'error',
                'message': f'Radio "{radio_name}" non trouvée'
            }), 404
            
    except Exception as e:
        print(f"❌ ERREUR edit_radio: {str(e)}")
        import traceback
        print(f"❌ Traceback edit_radio: {traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': f'Erreur lors de la modification: {str(e)}'
        }), 500

@app.route('/admin/delete/<radio_name>', methods=['POST'])
def delete_admin_radio(radio_name):
    """Supprimer une radio existante"""
    try:
        # Décoder le nom de la radio (gère les deux cas: encodé et non encodé)
        import urllib.parse
        radio_name = urllib.parse.unquote(radio_name)
        
        # Charger les radios existantes
        radios = load_radios()
        
        # Filtrer pour supprimer la radio
        updated_radios = [radio for radio in radios if radio[0] != radio_name]
        
        if len(updated_radios) < len(radios):
            if save_radios(updated_radios):
                flash(f'Radio "{radio_name}" supprimée avec succès!', 'success')
            else:
                flash(f'Erreur lors de la suppression de la radio "{radio_name}"', 'error')
        else:
            flash(f'Radio "{radio_name}" non trouvée', 'error')
            
    except Exception as e:
        flash(f'Erreur lors de la suppression: {str(e)}', 'error')
    
    return redirect(url_for('admin'))

@app.route('/admin/test/<radio_name>')
def test_radio(radio_name):
    """Tester une radio et récupérer les métadonnées"""
    try:
        # Décoder le nom de la radio (gère les deux cas: encodé et non encodé)
        import urllib.parse
        radio_name = urllib.parse.unquote(radio_name)
        
        # Charger les radios existantes
        radios = load_radios()
        
        # Trouver l'URL de la radio
        for name, url in radios:
            if name == radio_name:
                # Utiliser le fetcher global
                metadata = radio_state.fetcher.get_metadata(name, url)
                
                if metadata and metadata.title and metadata.artist:
                    return jsonify({
                        'status': 'success',
                        'artist': metadata.artist,
                        'title': metadata.title,
                        'cover_url': metadata.cover_url
                    })
                else:
                    return jsonify({
                        'status': 'no_data',
                        'message': 'Aucune métadonnée disponible'
                    })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Radio "{radio_name}" non trouvée'
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Erreur lors du test: {str(e)}'
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
