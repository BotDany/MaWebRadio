# 🚀 Guide de Déploiement Railway

## 📋 Prérequis

- Un compte Railway (https://railway.app)
- Un compte GitHub
- Le projet dans un repository GitHub

## 🎯 Étapes de déploiement

### 1. Préparer le repository GitHub

```bash
git add .
git commit -m "🎵 Lecteur Radio avec Reprise Instantanée - Ready for Railway"
git push origin main
```

### 2. Créer le projet Railway

1. Connectez-vous sur https://railway.app
2. Cliquez sur **"New Project"**
3. Choisissez **"Deploy from GitHub repo"**
4. Sélectionnez votre repository

### 3. Configuration automatique

Railway détectera automatiquement :

- ✅ **Procfile** : `web: python radio_player_web.py`
- ✅ **requirements.txt** : Flask + dépendances
- ✅ **Port** : Variable d'environnement `PORT`
- ✅ **Démarrage** : Commande du Procfile

### 4. Variables d'environnement (optionnelles)

Dans Railway > Settings > Variables :

```
FLASK_ENV=production
PORT=5000  # Railway définira automatiquement le port
```

### 5. Déploiement

- Cliquez sur **"Deploy Now"**
- Railway va :
  - Installer les dépendances (`pip install -r requirements.txt`)
  - Démarrer le serveur Flask (`python radio_player_web.py`)
  - Exposer sur le port dynamique

### 6. Vérification

Une fois déployé :

1. **URL publique** : `https://votre-projet.railway.app`
2. **Logs** : Disponibles dans l'interface Railway
3. **Métriques** : Monitoring intégré

## 🔧 Fonctionnalités sur Railway

### ✅ Ce qui fonctionne parfaitement :

- 🎵 **Lecteur radio avec audio HTML5**
- ⚡ **Reprise instantanée en direct**
- 📱 **Interface responsive**
- 📋 **Historique des musiques**
- 🎨 **Design moderne**
- 🌐 **Accessible 24/7**

### 🌍 Performance :

- **CDN Railway** : Distribution mondiale
- **SSL/TLS** : HTTPS automatique
- **Scaling** : Auto-scaling inclus
- **Logs** : Monitoring en temps réel

## 📱 Utilisation

Une fois déployé :

1. Ouvrez `https://votre-projet.railway.app`
2. Sélectionnez une radio
3. Cliquez sur Play ▶️
4. Testez : Play → Pause → Play = **Direct instantané** !

## 🛠️ Dépannage

### Si le site ne démarre pas :

1. **Vérifiez les logs** dans Railway
2. **Variables d'environnement** : `FLASK_ENV=production`
3. **Port** : Assurez-vous que le code utilise `os.environ.get('PORT')`

### Si l'audio ne fonctionne pas :

- L'audio HTML5 fonctionne sur tous les navigateurs modernes
- Pas besoin de configuration supplémentaire
- Railway ne bloque pas les flux audio

## 🎯 Avantages Railway

- ✅ **Gratuit** pour les petits projets
- ✅ **HTTPS** automatique
- ✅ **Domaine personnalisé** possible
- ✅ **Git integration** parfaite
- ✅ **Logs et monitoring**
- ✅ **Scaling automatique**

---

🚀 **Votre lecteur radio sera disponible en quelques minutes sur Railway !**
