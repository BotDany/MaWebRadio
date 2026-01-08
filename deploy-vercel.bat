@echo off
echo 🚀 Déploiement sur Vercel...
echo.

echo 📦 Installation des dépendances Vercel...
pip install -r requirements-vercel.txt

echo 📦 Installation de Vercel CLI...
npm install -g vercel

echo 🚀 Déploiement en cours...
vercel --prod

echo ✅ Déploiement terminé!
echo 🌐 URL: https://ma-webradio.vercel.app
pause
