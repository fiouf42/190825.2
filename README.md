# 🎬 TikTok AI Video Generator

Une application complète de génération automatique de vidéos TikTok alimentée par l'intelligence artificielle. Créez des vidéos captivantes avec des scripts intelligents, des visuels au style charbon dramatique et une narration vocale professionnelle.

## ✨ Fonctionnalités principales

### 🤖 Pipeline IA complet
- **Génération de script** : Création automatique de scripts engageants avec GPT-4.1
- **Génération d'images** : Visuels au style charbon dramatique avec OpenAI DALL-E
- **Narration vocale** : Synthèse vocale professionnelle avec ElevenLabs (19+ voix disponibles)
- **Montage automatique** : Assemblage vidéo avec FFmpeg, transitions et sous-titres TikTok

### 🎯 Interface utilisateur
- **Design moderne** : Interface sombre avec dégradés et effets de transparence
- **Contrôles intuitifs** : Saisie de prompt, sélection de durée (15-60s), choix de voix
- **Feedback en temps réel** : États de chargement étape par étape
- **Lecteur vidéo intégré** : Prévisualisation et téléchargement MP4

### 🎨 Caractéristiques techniques
- **Format optimisé** : Vidéos 1080x1920 (format TikTok)
- **Transitions professionnelles** : Fondus enchaînés automatiques
- **Sous-titres intégrés** : Style TikTok avec timing automatique
- **Base de données** : Stockage MongoDB avec historique des projets

## 🛠️ Technologies utilisées

### Backend
- **FastAPI** : API REST haute performance
- **MongoDB** : Base de données NoSQL pour le stockage des projets
- **OpenAI GPT-4.1** : Génération de scripts intelligents
- **OpenAI DALL-E** : Génération d'images au style charbon
- **ElevenLabs** : Synthèse vocale professionnelle
- **FFmpeg** : Traitement et assemblage vidéo

### Frontend
- **React 19** : Interface utilisateur moderne
- **Tailwind CSS** : Design système et styles
- **Axios** : Communication API
- **Vite/Craco** : Build et développement

## 📋 Prérequis

- **Node.js** 18+ et Yarn
- **Python** 3.8+ et pip
- **MongoDB** (local ou cloud)
- **FFmpeg** installé sur le système
- **Clés API** : OpenAI, ElevenLabs

## 🚀 Installation

### 1. Cloner le projet
```bash
git clone <repository-url>
cd tiktok-ai-generator
```

### 2. Configuration du Backend

```bash
cd backend

# Installer les dépendances Python
pip install -r requirements.txt

# Installer FFmpeg (Ubuntu/Debian)
sudo apt update
sudo apt install ffmpeg

# Installer FFmpeg (macOS)
brew install ffmpeg

# Installer FFmpeg (Windows)
# Télécharger depuis https://ffmpeg.org/download.html
```

### 3. Configuration des variables d'environnement

Créer le fichier `backend/.env` :
```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="tiktok_generator"
OPENAI_API_KEY="sk-proj-VOTRE_CLE_OPENAI"
ELEVENLABS_API_KEY="sk_VOTRE_CLE_ELEVENLABS"
USE_MOCK_DATA="false"
```

### 4. Configuration du Frontend

```bash
cd frontend

# Installer les dépendances
yarn install
```

Créer le fichier `frontend/.env` :
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

### 5. Démarrage des services

#### Backend (Terminal 1)
```bash
cd backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

#### Frontend (Terminal 2)
```bash
cd frontend
yarn start
```

L'application sera accessible sur `http://localhost:3000`

## 🔑 Obtention des clés API

### OpenAI API Key
1. Créer un compte sur [OpenAI Platform](https://platform.openai.com)
2. Aller dans "API Keys" 
3. Créer une nouvelle clé secrète
4. Ajouter des crédits à votre compte pour utiliser GPT-4.1 et DALL-E

### ElevenLabs API Key
1. Créer un compte sur [ElevenLabs](https://elevenlabs.io)
2. Aller dans "Profile" → "API Keys"
3. Générer une nouvelle clé API
4. Souscrire à un plan payant pour accéder à toutes les voix

## 📖 Utilisation

### 1. Génération de vidéo complète
1. Entrer votre idée de vidéo dans le champ de texte
2. Ajuster la durée avec le slider (15-60 secondes)
3. Sélectionner une voix pour la narration
4. Cliquer sur "🎬 Générer la vidéo complète"

### 2. Suivi du processus
L'application vous guidera à travers chaque étape :
- 🎬 Génération du script (GPT-4.1)
- 🎨 Création des visuels (Style charbon)
- 🎵 Génération de la voix (ElevenLabs)
- 🎞️ Assemblage de la vidéo (FFmpeg)

### 3. Résultats
Une fois terminé, vous pourrez :
- Visionner la vidéo dans le lecteur intégré
- Télécharger le fichier MP4
- Consulter le script et les scènes
- Voir la galerie d'images générées

## 🎯 Exemples de prompts

- "astuces productivité étudiants"
- "recette de cuisine rapide et healthy"
- "conseils fitness pour débutants"
- "voyage à Paris en 3 jours"
- "organisation parfaite de son bureau"

## 🏗️ Architecture du système

```
TikTok AI Generator/
├── backend/                 # API FastAPI
│   ├── server.py           # Serveur principal et routes
│   ├── requirements.txt    # Dépendances Python
│   └── .env               # Variables d'environnement
├── frontend/               # Interface React
│   ├── src/
│   │   ├── App.js         # Composant principal
│   │   └── App.css        # Styles
│   ├── package.json       # Dépendances Node.js
│   └── .env              # Configuration frontend
└── README.md             # Documentation
```

## 🔧 API Endpoints

- `POST /api/create-complete-video` - Pipeline complet de génération
- `POST /api/generate-script` - Génération de script uniquement
- `POST /api/generate-images` - Génération d'images uniquement
- `POST /api/generate-voice` - Génération de voix uniquement
- `GET /api/voices/available` - Liste des voix disponibles
- `GET /api/project/{id}` - Récupération d'un projet

## 🐛 Dépannage

### Problèmes courants

**Erreur "FFmpeg not found"**
```bash
# Vérifier l'installation
ffmpeg -version

# Réinstaller si nécessaire
sudo apt install ffmpeg  # Linux
brew install ffmpeg      # macOS
```

**Erreur MongoDB**
```bash
# Démarrer MongoDB local
sudo systemctl start mongod  # Linux
brew services start mongodb  # macOS
```

**Quota OpenAI dépassé**
- Vérifier vos crédits sur platform.openai.com
- Ajouter des crédits ou utiliser une autre clé API

**ElevenLabs free tier**
- Souscrire à un plan payant pour accéder à toutes les fonctionnalités

## 📊 Performances

- **Génération de script** : 5-10 secondes
- **Génération d'images** : 30-60 secondes (4-6 images)
- **Synthèse vocale** : 10-20 secondes
- **Assemblage vidéo** : 15-30 secondes
- **Total** : ~60-120 secondes pour une vidéo complète

## 🔒 Sécurité

- Les clés API sont stockées dans des variables d'environnement
- Validation des entrées utilisateur
- Gestion d'erreurs complète
- Nettoyage automatique des fichiers temporaires

## 🚀 Déploiement en production

Pour déployer en production, configurez :
- MongoDB Atlas pour la base de données
- Variables d'environnement sécurisées
- HTTPS/SSL
- Load balancer si nécessaire
- Monitoring et logs

## 📄 Licence

MIT License - Voir le fichier LICENSE pour plus de détails.

## 🤝 Contribution

Les contributions sont les bienvenues ! Créez une issue ou une pull request.

## 📞 Support

Pour toute question ou problème, créez une issue sur GitHub.

---

**🎬 Créez des vidéos TikTok époustouflantes en quelques clics !**
