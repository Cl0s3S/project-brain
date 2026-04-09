# 🤝 Contribuer à Project Brain

Merci de vouloir contribuer ! Voici comment ça marche.

## Workflow Git

1. **Fork** le dépôt
2. Crée une branche : `git checkout -b feature/nom-de-ta-feature`
3. Fais tes changements
4. Commit : `git commit -m "feat: description courte"`
5. Push : `git push origin feature/nom-de-ta-feature`
6. Ouvre une **Pull Request**

## Convention de commits

```
feat:     nouvelle fonctionnalité
fix:      correction de bug
data:     ajout/modification de données JSON
docs:     documentation
style:    changements CSS/UI
refactor: refactoring sans nouvelle feature
```

## Contribuer aux données

Les fichiers JSON dans `/data/` sont la colonne vertébrale du projet.  
Tu peux contribuer en ajoutant :

### `blocks.json`
```json
{
  "id": "minecraft:stone_bricks",
  "name": "Stone Bricks",
  "name_fr": "Briques de pierre",
  "craftable": true,
  "recipe": {
    "ingredients": [{ "id": "minecraft:stone", "count": 4 }],
    "output": 4
  }
}
```

### `farms.json`
```json
{
  "id": "iron_farm_standard",
  "name": "Iron Farm (standard)",
  "output_item": "minecraft:iron_ingot",
  "rates": {
    "base_per_hour": 9000,
    "optimal_tps": 20,
    "simulation_distance": 4
  }
}
```

## Signaler un bug

Ouvre une **Issue** avec :
- Description du bug
- Étapes pour le reproduire
- Comportement attendu vs observé
- Navigateur / OS

## Proposer une feature

Ouvre une **Discussion** (onglet Discussions du repo) avec :
- Le problème que ça résout
- Ta proposition de solution
- Des maquettes si tu en as
