# 🎵 Lecteur Radio avec Reprise Instantanée en Direct

Déployé sur Railway avec Flask et Audio HTML5

## 🚀 Fonctionnalités

- ⚡ **Reprise instantanée en direct** : Pause → Play = Direct immédiat
- 🔊 **Audio HTML5 natif** - Pas d'installation requise
- 📱 **Interface responsive** - Mobile, tablette, desktop
- 🎵 **17 radios françaises** - Chante France, RTL, Nostalgie, etc.
- 📋 **Historique automatique** des musiques passées
- 🎨 **Interface moderne** avec design gradient

## 🌐 Déploiement Railway

Ce projet est configuré pour Railway :

- **Procfile** : `web: python radio_player_web.py`
- **Port** : Dynamique via `PORT` environment variable
- **Requirements** : Flask + Requests + BeautifulSoup4

## 📋 Radios disponibles

- Chante France-80s
- RTL
- 100% Radio 80
- Nostalgie-Les 80 Plus Grand Tubes
- Flash 80 Radio
- Radio Comercial
- Bide Et Musique
- Mega Hits
- Superloustic
- Radio Gérard
- Supernana
- Génération Dorothée
- Made In 80
- Top 80 Radio
- Générikds
- Chansons Oubliées Où Presque
- Nostalgie-Les Tubes 80 N1

## ⚡ Comment ça marche

1. **Sélectionnez une radio** dans la liste déroulante
2. **Cliquez sur Play** ▶️ pour démarrer
3. **Mettez en pause** ⏸️ quand vous voulez
4. **Cliquez sur Play** ▶️ pour reprendre **instantanément en direct**

## 🔧 API Endpoints

- `GET /` - Interface principale
- `GET /api/metadata` - Métadonnées en temps réel
- `GET /api/history` - Historique des musiques
- `GET /api/play` - Démarrer la lecture
- `GET /api/pause` - Mettre en pause
- `GET /api/resume` - Reprendre en direct
- `GET /api/stop` - Arrêter

## 🎵 Caractéristique principale

**Reprise instantanée en direct** : Quand vous mettez une radio en pause et que vous appuyez sur play, ça reprend immédiatement en direct, pas là où vous vous êtes arrêté. Exactement comme une vraie radio !

## 📱 Technologies

- **Backend** : Flask (Python)
- **Frontend** : HTML5 + CSS3 + JavaScript
- **Audio** : HTML5 Audio API
- **Design** : Gradient moderne avec glassmorphism
- **Déploiement** : Railway

---

🚀 **Déployé sur Railway - Disponible 24/7**
