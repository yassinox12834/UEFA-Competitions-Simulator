<sub>[← README](../README.fr.md) · [Installation](installation.fr.md) · [Terminal](terminal.fr.md) · [Problèmes](troubleshooting.fr.md) · [Créer l'application](building.fr.md) · **Organisation** · [🇬🇧 English](project-structure.md)</sub>

# Organisation du projet

```
UEFA-Competitions-Simulator/
├── main.py                 lance l'application
├── UEFA-Simulator.spec     la recette de l'application Windows
├── requirements.txt        les paquets à installer
├── docs/                   ces guides : installation, terminal, problèmes, création
├── commands/               scripts tout prêts : installer, lancer, créer l'application
├── model/                  le tirage, les notes, le modèle de match et la simulation
│   └── docs/               comment fonctionne chaque partie, en anglais et en français
├── interface/              la fenêtre et ses écrans
├── uefa/                   où se trouve chaque fichier (chemins) et les réglages du projet
├── datahandler/            télécharge et nettoie les données d'API-Football
├── data/
│   ├── raw/                les données telles que téléchargées
│   ├── processed/          les données nettoyées : matchs, notes, comptes rendus
│   └── reference/          les réglages : coefficients, notes de départ, nombres du modèle
├── templates/              les chapeaux que l'application peut charger et enregistrer
├── assets/images/          écussons, logos des compétitions, drapeaux, images du README
├── scripts/                petits outils ponctuels
└── GIFs/                   les animations du README
```

## Pour aller plus loin

| Dossier | Son propre guide |
|---|---|
| `model/` | [`model/docs/`](../model/docs/README.md) |
| `interface/` | [`interface/README.md`](../interface/README.md) |
| `datahandler/` | [`datahandler/README.md`](../datahandler/README.md) |
| `templates/` | [`templates/README.md`](../templates/README.md) |
