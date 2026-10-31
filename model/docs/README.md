# How the model works: the guide

> These pages explain, in plain words, how the simulator turns real football results into a simulated Champions League, Europa League or Conference League season. Each page is in English, then in French.

*Version française : [plus bas](#comment-marche-le-modèle--le-guide).*

## Two kinds of pages

| Kind | Where | For whom | What you get |
|---|---|---|---|
| **Idea pages** | this folder | anyone curious, no programming needed | what the part does, why, a full example with real numbers, a small Python program to try, the modules used, known limits |
| **Code pages** | [`code/`](code/) | people reading or changing the code | the real code, a few lines at a time, with what each line does and why |

Start with the idea page of a part, then open its code page if you want the details.

---

## The parts, in the order a season runs

| # | Idea page | What it answers | Code page | Main file |
|---|---|---|---|---|
| 1 | [`elo.md`](elo.md) | How strong is each club? One number per club, learnt from 5 300 real matches | [`code/elo_code.md`](code/elo_code.md) | `elo_score_updating.py` |
| 2 | [`logistic_regression.md`](logistic_regression.md) | Given two ratings, what are the chances of a home win, a draw and an away win? | [`code/predictor_code.md`](code/predictor_code.md) | `predictor.py` |
| 3 | [`draw.md`](draw.md) | Who plays whom in the league phase? | [`code/draw_code.md`](code/draw_code.md) | `draw_ucl.py`, `draw_uecl.py` |
| 4 | [`matchdays.md`](matchdays.md) | Which match is played on which day? | [`code/matchdays_code.md`](code/matchdays_code.md) | `matchdays_ucl.py`, `matchdays_uecl.py` |
| 5 | [`names.md`](names.md) | How do we know "Bayern Munich" and "Bayern München" are the same club? | [`code/names_code.md`](code/names_code.md) | `names.py` |
| 6 | [`match_engine.md`](match_engine.md) | How is one match played? | [`code/match_engine_code.md`](code/match_engine_code.md) | `match_engine.py` |
| 7 | [`scorelines.md`](scorelines.md) | Once the result is known, what is the score? | [`code/scorelines_code.md`](code/scorelines_code.md) | `scorelines.py` |
| 8 | [`league_phase.md`](league_phase.md) | How is the table ranked, and who goes through? | [`code/league_phase_code.md`](code/league_phase_code.md) | `league_phase.py` |
| 9 | [`knockout.md`](knockout.md) | How do the play-offs, the bracket and the final work? | [`code/knockout_code.md`](code/knockout_code.md) | `knockout.py` |
| 10 | [`extra_time.md`](extra_time.md) | What happens in the 30 minutes of extra time? | (inside `scorelines_code.md` and `knockout_code.md`) | `scorelines.py`, `knockout.py` |
| 11 | [`penalties.md`](penalties.md) | How is a penalty shoot-out played? | [`code/penalties_code.md`](code/penalties_code.md) | `penalties.py` |
| 12 | [`monte_carlo.md`](monte_carlo.md) | How does one season become "PSG win 21 % of the time"? | [`code/simulation_code.md`](code/simulation_code.md) | `simulation.py` |

All files are in the `model/` folder.

## The whole journey in one picture

```
 5 300 real matches ──> Elo ratings (1) ──> match model (2)
                                                  │
 pots ──> draw (3) ──> matchdays (4)              │
            │                                     │
            └── names matched to ratings (5) ─────┤
                                                  ▼
            one season: every match (6) gets a result and a score (7)
                        ├── league table (8)
                        └── knockout (9), extra time (10), penalties (11)
                                                  │
                                                  ▼
            repeat the season many times and count (12)
```

---

## Python modules used by the model

| Module | Comes with Python? | Used for | In which parts |
|---|---|---|---|
| `random` | yes | every random choice, always through a private generator started from a seed | draw, matchdays, match engine, scores, penalties, simulation |
| `math` | yes | `exp` for the match model | match model, match engine |
| `json` | yes | reading and writing settings, ratings and tables | almost everywhere |
| `csv` | yes | reading countries and competition weights | draw, Elo |
| `pathlib` | yes | file paths that work on every computer | almost everywhere |
| `collections` | yes | `defaultdict` and `Counter` for counting | draw, matchdays |
| `functools` | yes | `lru_cache`: read a file once and remember it | draw, match engine |
| `itertools` | yes | `chain` and `accumulate` | draw, scores |
| `bisect` | yes | fast search in a sorted list | scores |
| `difflib`, `re`, `unicodedata` | yes | comparing and cleaning club names | names |
| `concurrent.futures`, `os` | yes | running seasons on several processor cores | simulation |
| `pandas`, `numpy` | no, install with `pip` | reading the real matches; only when ratings and tables are **rebuilt** | Elo, match model (training), scores (building the table) |
| `scikit-learn` | no, install with `pip` | **training** the match model, once | match model |

The app itself, when it simulates, only needs Python's own modules, plus pandas because of one import (a known bug, see [`match_engine.md`](match_engine.md)).

---

## If a word stops you

Each idea is explained the first time it is needed. This table says where.

| Idea | In one line | Explained in |
|---|---|---|
| rating, expected score | one number per club; the share of a match a club should win | [`elo.md`](elo.md), sections 2 and 3 |
| softmax | turns three scores into three chances that add up to 100 % | [`logistic_regression.md`](logistic_regression.md), section 6 |
| a random number between 0 and 1 | how the computer rolls a die with any number of faces | [`match_engine.md`](match_engine.md), section 2 |
| backtracking | try a choice, go on, undo it if it leads to a dead end | [`draw.md`](draw.md), section 3 |
| seed | the starting number of the random generator: same seed, same result | [`draw.md`](draw.md), section 5 |
| standard error | how much luck is left in a simulated percentage | [`monte_carlo.md`](monte_carlo.md), section 3 |

---

## Known bugs, all in one place

All ten were fixed in version 1.1.0. Each page's "Known bugs" section says how, and lists what is still open.

| Page | Bug (before 1.1.0) | Fix |
|---|---|---|
| [`elo.md`](elo.md) | The real ratings used old competition weights from `coef_table.csv` | `coef_table.csv` rebuilt from `coefs.json`; ratings recomputed, match model retrained |
| [`elo.md`](elo.md) | Friendlies were in the training data (625 played) | Competitions with `comp_mult` 0 are skipped |
| [`match_engine.md`](match_engine.md) | "The app needs pandas" | Not reproduced: pandas is only imported inside `run()` |
| [`extra_time.md`](extra_time.md) | Extra-time goals counted in the ratings but not in the simulation | Both use the 90-minute score, then 0.8 / 0.2 after extra time and 0.7 / 0.3 after penalties |
| [`penalties.md`](penalties.md) | The description said the first kicker wins 50 % | Text updated: 51.3 % |
| [`scorelines.md`](scorelines.md) | Capping at 6 happened before deciding the result | Result read first: 8-7 becomes 6-5 |
| [`league_phase.md`](league_phase.md) | The log said "alphabetical order" | It says "kept in pot order" |
| [`matchdays.md`](matchdays.md) | The step limit was far too high | 5 000 instead of 200 000: slowest schedule 0.37 s instead of 8.8 s |
| [`names.md`](names.md) | A misspelt alias failed silently | The alias is searched first and flagged; the simulation warns |
| [`monte_carlo.md`](monte_carlo.md) | Custom ratings were ignored with several processes | The processes receive the same ratings: identical counts with 1 and 2 |

---

## Notes and anecdotes

<!-- Space for the author's own notes. -->

---
---

# Comment marche le modèle : le guide

> Ces pages expliquent, avec des mots simples, comment le simulateur transforme de vrais résultats de football en une saison simulée de Ligue des champions, de Ligue Europa ou de Ligue Conférence. Chaque page est en anglais, puis en français.

## Deux sortes de pages

| Sorte | Où | Pour qui | Ce qu'on y trouve |
|---|---|---|---|
| **Pages d'idées** | ce dossier | toute personne curieuse, sans savoir programmer | ce que fait la partie, pourquoi, un exemple complet avec de vrais nombres, un petit programme Python à essayer, les modules utilisés, les limites connues |
| **Pages de code** | [`code/`](code/) | ceux qui lisent ou modifient le code | le vrai code, quelques lignes à la fois, avec ce que fait chaque ligne et pourquoi |

Commencez par la page d'idées d'une partie, puis ouvrez sa page de code si vous voulez les détails.

---

## Les parties, dans l'ordre où se déroule une saison

| # | Page d'idées | La question | Page de code | Fichier principal |
|---|---|---|---|---|
| 1 | [`elo.md`](elo.md) | Quelle est la force de chaque club ? Un nombre par club, appris sur 5 300 vrais matchs | [`code/elo_code.md`](code/elo_code.md) | `elo_score_updating.py` |
| 2 | [`logistic_regression.md`](logistic_regression.md) | Avec deux notes, quelles sont les chances de victoire à domicile, de nul et de victoire à l'extérieur ? | [`code/predictor_code.md`](code/predictor_code.md) | `predictor.py` |
| 3 | [`draw.md`](draw.md) | Qui joue contre qui en phase de ligue ? | [`code/draw_code.md`](code/draw_code.md) | `draw_ucl.py`, `draw_uecl.py` |
| 4 | [`matchdays.md`](matchdays.md) | Quel match se joue quel jour ? | [`code/matchdays_code.md`](code/matchdays_code.md) | `matchdays_ucl.py`, `matchdays_uecl.py` |
| 5 | [`names.md`](names.md) | Comment sait-on que « Bayern Munich » et « Bayern München » sont le même club ? | [`code/names_code.md`](code/names_code.md) | `names.py` |
| 6 | [`match_engine.md`](match_engine.md) | Comment se joue un match ? | [`code/match_engine_code.md`](code/match_engine_code.md) | `match_engine.py` |
| 7 | [`scorelines.md`](scorelines.md) | Une fois le résultat connu, quel est le score ? | [`code/scorelines_code.md`](code/scorelines_code.md) | `scorelines.py` |
| 8 | [`league_phase.md`](league_phase.md) | Comment le classement est-il fait, et qui se qualifie ? | [`code/league_phase_code.md`](code/league_phase_code.md) | `league_phase.py` |
| 9 | [`knockout.md`](knockout.md) | Comment marchent les barrages, le tableau et la finale ? | [`code/knockout_code.md`](code/knockout_code.md) | `knockout.py` |
| 10 | [`extra_time.md`](extra_time.md) | Que se passe-t-il pendant les 30 minutes de prolongation ? | (dans `scorelines_code.md` et `knockout_code.md`) | `scorelines.py`, `knockout.py` |
| 11 | [`penalties.md`](penalties.md) | Comment se joue une séance de tirs au but ? | [`code/penalties_code.md`](code/penalties_code.md) | `penalties.py` |
| 12 | [`monte_carlo.md`](monte_carlo.md) | Comment une saison devient-elle « le PSG gagne 21 % du temps » ? | [`code/simulation_code.md`](code/simulation_code.md) | `simulation.py` |

Tous les fichiers sont dans le dossier `model/`.

## Tout le parcours en une image

```
 5 300 vrais matchs ──> notes Elo (1) ──> modèle de match (2)
                                                  │
 chapeaux ──> tirage (3) ──> journées (4)         │
                │                                 │
                └── noms reliés aux notes (5) ────┤
                                                  ▼
            une saison : chaque match (6) reçoit un résultat et un score (7)
                        ├── classement de la phase de ligue (8)
                        └── élimination directe (9), prolongation (10), tirs au but (11)
                                                  │
                                                  ▼
            répéter la saison de nombreuses fois et compter (12)
```

---

## Les modules Python utilisés par le modèle

| Module | Fourni avec Python ? | Sert à | Dans quelles parties |
|---|---|---|---|
| `random` | oui | chaque choix au hasard, toujours par un générateur privé démarré à partir d'une graine | tirage, journées, moteur de match, scores, tirs au but, simulation |
| `math` | oui | `exp` pour le modèle de match | modèle de match, moteur de match |
| `json` | oui | lire et écrire réglages, notes et tables | presque partout |
| `csv` | oui | lire les pays et les poids des compétitions | tirage, Elo |
| `pathlib` | oui | des chemins de fichiers qui marchent sur tout ordinateur | presque partout |
| `collections` | oui | `defaultdict` et `Counter` pour compter | tirage, journées |
| `functools` | oui | `lru_cache` : lire un fichier une fois et s'en souvenir | tirage, moteur de match |
| `itertools` | oui | `chain` et `accumulate` | tirage, scores |
| `bisect` | oui | recherche rapide dans une liste triée | scores |
| `difflib`, `re`, `unicodedata` | oui | comparer et nettoyer les noms de clubs | noms |
| `concurrent.futures`, `os` | oui | faire tourner les saisons sur plusieurs cœurs | simulation |
| `pandas`, `numpy` | non, à installer avec `pip` | lire les vrais matchs ; seulement quand les notes et les tables sont **reconstruites** | Elo, modèle de match (entraînement), scores (construction de la table) |
| `scikit-learn` | non, à installer avec `pip` | **entraîner** le modèle de match, une fois | modèle de match |

L'appli elle-même, quand elle simule, n'a besoin que des modules de Python, plus pandas à cause d'un import (un bug connu, voir [`match_engine.md`](match_engine.md)).

---

## Si un mot vous bloque

Chaque idée est expliquée la première fois qu'on en a besoin. Ce tableau dit où.

| Idée | En une ligne | Expliquée dans |
|---|---|---|
| note, score attendu | un nombre par club ; la part d'un match qu'un club devrait gagner | [`elo.md`](elo.md), sections 2 et 3 |
| softmax | transforme trois scores en trois chances qui font 100 % au total | [`logistic_regression.md`](logistic_regression.md), section 6 |
| un nombre au hasard entre 0 et 1 | comment l'ordinateur lance un dé avec n'importe quel nombre de faces | [`match_engine.md`](match_engine.md), section 2 |
| retour sur trace | essayer un choix, continuer, le défaire s'il mène à une impasse | [`draw.md`](draw.md), section 3 |
| graine | le nombre de départ du générateur de hasard : même graine, même résultat | [`draw.md`](draw.md), section 5 |
| erreur type | combien de hasard reste dans un pourcentage simulé | [`monte_carlo.md`](monte_carlo.md), section 3 |

---

## Les bugs connus, au même endroit

Les dix ont été corrigés dans la version 1.1.0. La partie « Bugs connus » de chaque page explique comment, et liste ce qui reste ouvert.

| Page | Bug (avant la 1.1.0) | Correction |
|---|---|---|
| [`elo.md`](elo.md) | Les vraies notes utilisaient d'anciens poids de compétition venant de `coef_table.csv` | `coef_table.csv` reconstruit à partir de `coefs.json` ; notes recalculées, modèle de match réentraîné |
| [`elo.md`](elo.md) | Les amicaux étaient dans les données d'entraînement (625 joués) | Les compétitions avec un `comp_mult` de 0 sont écartées |
| [`match_engine.md`](match_engine.md) | « L'appli a besoin de pandas » | Non reproduit : pandas n'est importé qu'à l'intérieur de `run()` |
| [`extra_time.md`](extra_time.md) | Les buts de prolongation comptaient dans les notes mais pas dans la simulation | Les deux utilisent le score après 90 minutes, puis 0.8 / 0.2 après prolongation et 0.7 / 0.3 après tirs au but |
| [`penalties.md`](penalties.md) | La description disait que le premier tireur gagne 50 % | Texte mis à jour : 51.3 % |
| [`scorelines.md`](scorelines.md) | Le plafond à 6 buts était appliqué avant de décider du résultat | Résultat lu d'abord : 8-7 devient 6-5 |
| [`league_phase.md`](league_phase.md) | Le journal disait « ordre alphabétique » | Il dit « kept in pot order » (ordre des chapeaux) |
| [`matchdays.md`](matchdays.md) | La limite de pas était bien trop haute | 5 000 au lieu de 200 000 : calendrier le plus lent en 0,37 s au lieu de 8,8 s |
| [`names.md`](names.md) | Un alias mal écrit échouait en silence | L'alias est cherché en premier et signalé ; la simulation prévient |
| [`monte_carlo.md`](monte_carlo.md) | Les notes personnalisées étaient ignorées avec plusieurs processus | Les processus reçoivent les mêmes notes : comptes identiques avec 1 et 2 |

---
