# 📈 Roadmap — Project Brain

## v0.1 — Foundation (Module Project Brain)
**Objectif : avoir un outil utilisable pour planifier un build**

- [ ] Structure HTML/CSS du dashboard
- [ ] Navigation entre les pages (SPA ou multi-pages)
- [ ] Module Project Brain :
  - [ ] Création d'un projet (nom, description, type)
  - [ ] Ajout manuel de blocs nécessaires
  - [ ] Calcul des ressources à partir d'une liste
  - [ ] Suivi : ressources possédées vs nécessaires
- [ ] Base de données `blocks.json` (blocs Minecraft courants)
- [ ] Base de données `recipes.json` (recettes de craft)
- [ ] LocalStorage pour sauvegarder les projets

## v0.2 — Farm Planner
- [ ] Formulaire de paramètres (type farm, TPS, sim distance)
- [ ] Base de données `farms.json` (rendements connus)
- [ ] Calcul rendement brut et réaliste
- [ ] Calcul du temps pour atteindre un objectif
- [ ] Export des résultats (JSON / texte)

## v0.3 — Calculateur Objectif → Ressources
- [ ] Entrée libre : "je veux X de ressource Y"
- [ ] Décomposition récursive en ressources brutes
- [ ] Affichage du plan complet (crafter, farmer, temps)
- [ ] Intégration avec Farm Planner

## v0.4 — Import Litematica (backend Python)
- [ ] Parser .litematic (format NBT)
- [ ] Extraction automatique de la liste de blocs
- [ ] Décomposition en ressources brutes
- [ ] Upload via interface web

## v0.5 — Builder Assistant
- [ ] Générateur de palettes de blocs par thème
- [ ] Générateur de formes (cercles, sphères, arches)
- [ ] Prévisualisation simple 2D/3D
- [ ] Suggestions de styles architecturaux

## v0.6 — Dashboard Monde
- [ ] Vue globale des ressources disponibles
- [ ] Stats de production par farm
- [ ] Timeline de progression des projets
- [ ] Estimation du "temps restant" global

## v1.0 — Collaboration
- [ ] Système de comptes utilisateurs
- [ ] Création et gestion d'équipes
- [ ] Assignation de tâches
- [ ] Partage de projets
- [ ] Synchronisation en temps réel (WebSocket)

## Futur / Idées
- Connexion directe au serveur Minecraft (mod/plugin)
- Récupération automatique des inventaires
- IA pour suggestions de build
- Marketplace de projets et schémas
- Application mobile
