<sub>[← README](../README.fr.md) · [Installation](installation.fr.md) · **Terminal** · [Problèmes](troubleshooting.fr.md) · [Créer l'application](building.fr.md) · [Organisation](project-structure.fr.md) · [🇬🇧 English](terminal.md)</sub>

# Commandes du terminal

La simulation tourne aussi sans la fenêtre. Toutes les commandes se lancent depuis le dossier du projet, celui qui contient `main.py`.

## Avant de commencer

Les paquets doivent d'abord être installés (voir [installation](installation.fr.md)). Ensuite, activez le `.venv` :

```bash
.venv\Scripts\Activate.ps1       # Windows
source .venv/bin/activate        # macOS ou Linux
```

ou remplacez `python` dans les commandes ci-dessous par `.venv\Scripts\python` sous Windows et `.venv/bin/python` sous macOS et Linux.

## Une saison complète

Chaque commande fait un tirage, joue une saison avec le compte rendu complet, la rejoue 100 fois, et affiche les dix clubs qui ont le plus de chances de gagner :

```bash
python -m model.simulation UCL     # Ligue des champions
python -m model.simulation UEL     # Ligue Europa
python -m model.simulation UECL    # Ligue Conférence
```

## Une partie à la fois

| Commande | Ce qu'elle fait |
|---|---|
| `python -m model.draw_ucl` | un tirage de Ligue des champions et un de Ligue Europa, affichés chapeau par chapeau |
| `python -m model.draw_uecl` | un tirage de Ligue Conférence |
| `python -m model.matchdays_ucl` | un tirage réparti en 8 journées |
| `python -m model.predictor` | les chances de victoire à domicile, de nul et de victoire à l'extérieur pour quelques écarts de notes |
| `python -m model.predictor --train` | réentraîne le modèle de match (nécessite `scikit-learn`) |
| `python -m model.elo_score_updating --write` | recalcule la note de chaque club à partir des vrais matchs (nécessite `pandas`) |
| `python -m model.scorelines` | reconstruit la table des vrais scores (nécessite `pandas`) |

Le fonctionnement de chaque partie est expliqué dans [`model/docs/`](../model/docs/README.md).
