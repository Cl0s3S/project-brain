# 🧠 Project Brain — Minecraft Planning Platform

> Le "Notion + Excel + Litematica" de Minecraft — pour joueurs techniques et builders avancés.

![Version](https://img.shields.io/badge/version-0.1.0-green)
![Status](https://img.shields.io/badge/status-en%20développement-orange)
![License](https://img.shields.io/badge/license-MIT-blue)

---

## 🎯 C'est quoi ?

**Project Brain** est une plateforme web tout-en-un pour les joueurs Minecraft avancés.  
Elle permet de :

- 📐 **Planifier** des builds complexes (import Litematica / .schem)
- 🌾 **Optimiser** la production de ses farms (rendement, TPS, simulation distance)
- 📊 **Suivre** sa progression et ses ressources
- 🤝 **Collaborer** avec son équipe sur un serveur SMP

---

## 🧩 Modules

| Module | Description | Statut |
|--------|-------------|--------|
| 🧠 Project Brain | Gestion de projet, import schémas, analyse blocs | 🚧 En cours |
| 🌾 Farm Planner | Calcul rendement, paramètres serveur | 📋 Planifié |
| 🔁 Objectif → Ressources | Calculateur automatique | 📋 Planifié |
| 🏗️ Builder Assistant | Palettes, styles, générateur formes | 📋 Planifié |
| 📊 Dashboard Monde | Vue globale, stats, progression | 📋 Planifié |
| 🤝 Collaboration | Équipes, tâches, temps réel | 📋 Planifié |

---

## 🗂️ Structure du projet

```
project-brain/
├── index.html              # Page principale
├── assets/
│   ├── css/
│   │   ├── main.css        # Styles globaux
│   │   └── components.css  # Composants réutilisables
│   ├── js/
│   │   ├── app.js          # Point d'entrée
│   │   ├── router.js       # Navigation SPA
│   │   ├── store.js        # État global
│   │   └── modules/
│   │       ├── project.js      # Module Project Brain
│   │       ├── farm.js         # Module Farm Planner
│   │       ├── calculator.js   # Module Ressources
│   │       ├── builder.js      # Module Builder
│   │       └── dashboard.js    # Module Dashboard
│   └── img/
├── data/
│   ├── blocks.json         # Base de données blocs Minecraft
│   ├── recipes.json        # Recettes de craft
│   └── farms.json          # Données fermes connues
├── pages/
│   ├── dashboard.html
│   ├── project.html
│   ├── farms.html
│   ├── resources.html
│   └── team.html
├── backend/                # (optionnel, Python/Flask)
│   ├── app.py
│   ├── parser/
│   │   └── litematica.py   # Parser fichiers .litematic
│   └── calculator/
│       └── resources.py    # Moteur de calcul
├── docs/
│   ├── CONTRIBUTING.md
│   ├── ROADMAP.md
│   └── API.md
└── README.md
```

---

## 🚀 Installation

### Prérequis
- Un navigateur moderne
- Python 3.10+ (pour le backend, optionnel)

### Lancer en local (frontend uniquement)
```bash
git clone https://github.com/ton-username/project-brain.git
cd project-brain
# Ouvrir index.html dans un navigateur
# OU utiliser un serveur local :
python -m http.server 8080
```

### Lancer avec le backend Python
```bash
cd backend
pip install -r requirements.txt
python app.py
# Backend disponible sur http://localhost:5000
```

---

## 🛠️ Stack technique

**Frontend**
- HTML5 / CSS3 / JavaScript (Vanilla JS — pas de framework pour rester simple)
- Éventuellement Alpine.js ou Petite-Vue si besoin de réactivité légère

**Backend (optionnel)**
- Python 3 + Flask
- Parser Litematica (format NBT)
- Moteur de calcul craft/farm

**Données**
- JSON statique pour les blocs/recettes Minecraft
- LocalStorage pour la progression utilisateur
- (futur) Base de données partagée pour la collaboration

---

## 🤝 Contribuer

Les contributions sont les bienvenues !  
Voir [CONTRIBUTING.md](docs/CONTRIBUTING.md) pour les guidelines.

### Idées de contribution
- 📦 Enrichir la base de données `blocks.json`
- 🌾 Ajouter des données de farms dans `farms.json`
- 🐛 Reporter des bugs via les Issues
- 💡 Proposer des features via les Discussions

---

## 📈 Roadmap

Voir [ROADMAP.md](docs/ROADMAP.md) pour le plan détaillé.

**v0.1** — Dashboard + Project Brain (base)  
**v0.2** — Farm Planner  
**v0.3** — Calculateur Objectif → Ressources  
**v1.0** — Version complète collaborative  

---

## 📄 Licence

MIT — libre d'utilisation et de modification.

---

> *"Built by Minecraft players, for Minecraft players."* 🪨⛏️
