# UEFA Competitions Simulator

*Version française : [plus bas](#fr-version-française).*

*The [changelog](GHANGELOG.md) lists every notable change to the project.*

## What does it do?

This project simulates any of the three UEFA club competitions: the Champions League, the Europa League and the Conference League. It also carries out the draw for the new format (since 2024/25), which is far from trivial to implement.

## A small demonstration

![The menu](GIFs/GIF_1.gif)
The menu

![The draw](GIFs/GIF_2.gif)
The draw

![The simulation](GIFs/GIF_3.gif)
The simulation

## Features

- Simulates the three UEFA club competitions: Champions League, Europa League and Conference League, from the draw to the final.
- Runs the league phase draw with the real constraints: 8 opponents per club (6 in the Conference League), at most 2 opponents from the same association, and none from your own.
- Plays the draw out as an animated ceremony, pot by pot, instead of showing only the result.
- Lets you ban a specific home fixture (for example, Genk must not host Brann); the draw respects it.
- Lets you replace any club (name, association, badge), load pots from a JSON template, and save your own.
- Ships with the real 2025/26 pots for all three competitions.
- Builds the league phase table with UEFA's tiebreakers, then plays the play-offs, the two-legged knockout rounds and a single-match final at a neutral venue.
- Offers three methods for two-legged ties: `legs`, `aggregate` and `oneshot`.
- Plays penalty shoot-outs kick by kick, so every shoot-out has a real score.
- Updates Elo ratings after every simulated match, so a club on a winning run gets stronger during the season.
- Runs a Monte Carlo of up to 10,000 seasons on up to 8 processor cores, and shows each club's probability of reaching each stage as a heat map.
- Keeps an expert log of every match, in the app and as a text file.
- Works in English and French, with a light and a dark theme.

## How it works, in 30 seconds

```
 5 300 real matches ──> one Elo rating per club ──> a model that turns two ratings
 (2024 to 2025)                                      into P(home win), P(draw), P(away win)
                                                              │
 the pots ──> the draw ──> the matchdays                      │
                                 │                            │
                                 ▼                            ▼
          one season: every match gets a result and a score, ratings move after each match
                      ├── league phase table (top 8 / play-offs / out)
                      └── play-offs, round of 16, quarter-finals, semi-finals, final
                                 │
                                 ▼
          repeat the season up to 10,000 times and count how far each club gets
```

Each step is explained in plain words, with examples and small Python programs, in [`model/docs/`](model/docs/README.md).

---

## How to launch it

Everything below runs from the `UEFA/` folder (the one that contains `main.py`).

### Shortcut: the `commands/` folder

Three tiny scripts per system: `get_to_file` (go to the project folder), `req` (install the requirements) and `run` (launch the app).

>First, you’ll need to configure the Bash or PowerShell scripts in that folder. You don’t need to edit all of them, just the ones that are compatible with your operating system. Basically, those you intend to run.

| System | Folder | Install | Launch |
|---|---|---|---|
| Windows (PowerShell) | `commands/windows/` | `.\commands\windows\req.ps1` | `.\commands\windows\run.ps1` |
| macOS | `commands/MacOs/` | `bash commands/MacOs/req.sh` | `bash commands/MacOs/run.sh` |
| Linux | `commands/linux/` | `bash commands/linux/req.sh` | `bash commands/linux/run.sh` |

If PowerShell refuses to run a `.ps1` file, type `Set-ExecutionPolicy -Scope Process RemoteSigned` once in that window.

**Windows with the Python Manager (the `py` command), to choose your Python version:**

```
1. Type `py --list` to see the versions installed on your computer.
2. Open `commands/python manager/req.ps1` and `commands/python manager/run.ps1`, and **replace `3.12` by your version** (3.10 or newer) in each one.
3. Run them: `.\"commands\python manager\req.ps1"` then `.\"commands\python manager\run.ps1"`.

Without the scripts, the same thing by hand (replace `3.12` by your version):

```powershell
py -3.12 -m pip install -r requirements.txt
py -3.12 main.py

### 1. What you need

- **Python 3.10 or newer.** Check with `python --version`.
- **Tkinter**, the toolkit the window is built on. It comes with the Windows and macOS installers from python.org. On Debian or Ubuntu, add it with `sudo apt install python3-tk`. It cannot be installed with `pip`.
- **No API key is needed to run the app.** The pots, the ratings, the coefficients and the club badges ship with the project. A key is only needed to download fresh data (see [`datahandler/`](datahandler/README.md)).

### 2. Create a virtual environment (recommended)

A virtual environment keeps this project's packages separate from the rest of your computer.

```bash
# Windows (PowerShell)
py -m venv .venv
.venv\Scripts\Activate.ps1

# macOS or Linux
python3 -m venv .venv
source .venv/bin/activate
```

If PowerShell refuses to run the script, run `Set-ExecutionPolicy -Scope Process RemoteSigned` once in that window, then activate again. When it works, `(.venv)` appears at the start of your prompt.

### 3. Install the required packages

```bash
pip install -r requirements.txt
```

| Package | What it is used for |
|---|---|
| `customtkinter` | the window and every screen of the app |
| `Pillow` | loading and resizing the club badges and flags |
| `pandas`, `numpy` | reading and cleaning the real match data; rebuilding the ratings |
| `scikit-learn` | training the match model (once; the app then only reads its 8 numbers) |
| `requests` | downloading data and badges from API-Football |
| `python-dotenv` | reading the API key from the `.env` file |

### 4. Launch the app

```bash
python main.py
```

The menu opens. Pick a language, a competition (Champions League, Europa League or Conference League) and a mode: draw only, or the full simulation. Then follow the screens: pots, draw ceremony, and simulation.

### 5. Run the three competitions without the window (optional)

The model can also run in the terminal. Each command draws the competition with seed 1, plays one full season with the expert log, then a Monte Carlo of 100 seasons, and prints the ten clubs most likely to win:

```bash
python -m model.simulation UCL     # Champions League
python -m model.simulation UEL     # Europa League
python -m model.simulation UECL    # Conference League
```

Other parts can be run on their own too:

| Command | What it does |
|---|---|
| `python -m model.draw_ucl` | one Champions League and one Europa League draw, printed pot by pot |
| `python -m model.draw_uecl` | one Conference League draw |
| `python -m model.matchdays_ucl` | a draw split into 8 matchdays |
| `python -m model.predictor` | the chances of home win, draw and away win for a few rating gaps |
| `python -m model.predictor --train` | trains the match model again (needs `scikit-learn`) |
| `python -m model.elo_score_updating_copy --write` | recomputes every club's rating from the real matches (needs `pandas`) |
| `python -m model.scorelines` | rebuilds the table of real scores (needs `pandas`) |

### 6. If something goes wrong

| Message or symptom | Cause and fix |
|---|---|
| `ModuleNotFoundError: No module named 'customtkinter'` | The virtual environment is not active, or step 3 was skipped. Activate it, then run `pip install -r requirements.txt` again. |
| `ModuleNotFoundError: No module named 'model'` or `'uefa'` | You are not in the `UEFA/` folder. Use `cd` to go there first. |
| `No module named '_tkinter'` | Tkinter is missing. See step 1. |
| `predictor_weights.json not found` | The match model has not been trained. Run `python -m model.predictor --train`. |
| A warning "not found in the Elo file, starting at 1500" | A club's name could not be matched to a rating (usually a club you added yourself). See [`model/docs/names.md`](model/docs/names.md). |
| "no valid draw found in 50 attempts" | The banned home fixtures make the draw impossible. Remove some of them. |

---

## Project structure

```
UEFA/
├── .env.example                     template for your own .env file (API key)
├── .gitignore                       what Git must not track
├── GHANGELOG.md                     the changelog
├── image_downloader_logos.py        the script used to download the club badges
├── main.py                          starts the app
├── README.md                        this file
├── requirements.txt                 the packages to install
├── assets/
│   └── images/
│       ├── clubs/                   club badges, one folder per competition
│       │   ├── UCL/                 36 badges, one PNG per club
│       │   ├── UECL/                36 badges, one PNG per club
│       │   └── UEL/                 36 badges, one PNG per club
│       ├── compets/                 competition logos
│       │   ├── UCL_logo.png
│       │   ├── UECL_logo.png
│       │   └── UEL_logo.png
│       ├── flags/                   flags
│       │   ├── Flag_of_France.png
│       │   └── UK_US_flag.png
│       ├── github/                  README pictures (banner, stars)
│       │   ├── banner.png
│       │   ├── banner.svg
│       │   ├── star_en.png
│       │   └── star_fr.png
│       └── optional/                17 optional images
├── commands/                        ready-made install and launch scripts
│   ├── linux/                       Linux
│   │   ├── get_to_file.sh
│   │   ├── req.sh
│   │   └── run.sh
│   ├── MacOs/                       macOS
│   │   ├── get_to_file.sh
│   │   ├── req.sh
│   │   └── run.sh
│   ├── python manager/              Python Manager
│   │   ├── get_to_file.ps1
│   │   ├── req.ps1
│   │   └── run.ps1
│   └── windows/                     Windows
│       ├── get_to_file.ps1
│       ├── req.ps1
│       └── run.ps1
├── data/
│   ├── processed/                   cleaned data: matches, ratings, simulation logs
│   │   ├── all_competitions_25.csv
│   │   ├── cleaned_clubs_25.csv
│   │   ├── countries_filled_25.csv
│   │   ├── eeelo_final.json
│   │   ├── fixtures_25.csv
│   │   ├── match_features.csv
│   │   ├── predictions.csv
│   │   ├── sim_UECL_20260916-192903.txt
│   │   ├── uefa_coefficients_2021_2022.csv
│   │   ├── uefa_coefficients_2022_23.csv
│   │   └── uefa_countries_25.csv
│   ├── raw/                         data as downloaded
│   │   ├── fixtures_UCL/            36 JSON files, one per club
│   │   ├── fixtures_UECL/           36 JSON files, one per club
│   │   └── fixtures_UEL/            36 JSON files, one per club
│   └── reference/                   settings: coefficients, starting ratings, model weights, score table
│       ├── coef_table.csv
│       ├── coefs.json
│       ├── confr.json
│       ├── country_seeds.json
│       ├── predictor_weights.json
│       ├── scorelines.json
│       ├── team_seed.json
│       ├── UCL.json
│       ├── UCL_updated.json
│       ├── UECL.json
│       ├── UECL_updated.json
│       ├── UEL.json
│       └── UEL_updated.json
├── datahandler/                     scripts that download and clean the data from API-Football
│   ├── __init__.py
│   ├── add_neutral_venue.py
│   ├── build_fixtures_csv.py
│   ├── build_team_seeds.py
│   ├── drop_duplicate_fixtures.py
│   ├── fetch_club_logos.py
│   ├── fetch_competition_logos.py
│   ├── fetch_fixtures.py
│   ├── fetch_leagues.py
│   ├── fetch_team_ids.py
│   ├── README.md                    where the data comes from
│   └── img/                         4 diagrams (English and French versions)
├── GIFs/                            the demonstration above
│   ├── GIF_1.gif
│   ├── GIF_2.gif
│   └── GIF_3.gif
├── interface/                       the window and its screens (CustomTkinter)
│   ├── app.py                       the window and the router
│   ├── base_view.py                 the contract shared by every screen
│   ├── canvas_views.py              the three large tables of the results screen
│   ├── chrome.py                    the two bars that never move
│   ├── config.py
│   ├── draw_engine.py               bridge between the interface and model/
│   ├── draw_widgets.py              building blocks of the draw screen
│   ├── fonts.py                     the typography
│   ├── images.py                    makes every image of the app
│   ├── main.py                      entry point of the interface
│   ├── platform_utils.py
│   ├── README.md                    how the interface was written
│   ├── sim_engine.py                bridge to model/simulation.py
│   ├── sim_view.py                  the simulation screen
│   ├── theme.py                     default look of the widgets
│   ├── transition.py                animation engine
│   ├── views.py                     the menu screens
│   └── widgets.py                   reusable building blocks
├── model/                           the draw, the ratings, the match model and the simulation
│   ├── __init__.py
│   ├── categorising.py              builds the (league, round) category table
│   ├── coefs.py
│   ├── draw_ucl.py                  draw engine, 8-match league phase (UCL, UEL)
│   ├── draw_uecl.py                 draw engine, 6-match league phase (UECL)
│   ├── elo_score_updating_copy.py   runs the Elo ratings through a season
│   ├── knockout.py                  play-offs and knockout rounds
│   ├── league_phase.py              plays the league phase and ranks the 36 clubs
│   ├── match_engine.py              plays one match
│   ├── matchdays_ucl.py             splits a draw into matchdays (UCL, UEL)
│   ├── matchdays_uecl.py            splits a draw into matchdays (UECL)
│   ├── names.py                     matches club names written differently
│   ├── penalties.py                 penalty shoot-outs, kick by kick
│   ├── predict_matches_uefa.py
│   ├── predictor.py                 match outcome model (logistic regression)
│   ├── prepredictator.py            fits the result classifier
│   ├── scorelines.py                turns an outcome into a scoreline
│   ├── seeding.py
│   ├── simulation.py                simulates a whole competition
│   ├── testing.py
│   ├── tests.py
│   └── docs/                        how every part works, in English and French
│       ├── draw.md
│       ├── elo.md
│       ├── extra_time.md
│       ├── knockout.md
│       ├── league_phase.md
│       ├── logistic_regression.md
│       ├── match_engine.md
│       ├── matchdays.md
│       ├── monte_carlo.md
│       ├── names.md
│       ├── penalties.md
│       ├── README.md                the guide to the model
│       ├── scorelines.md
│       ├── code/                    11 pages, the code of each part explained
│       └── img/                     24 pictures (English and French versions)
├── scripts/                         small one-off tools (badge downloads, image clean-up)
│   ├── fetch_template_badges.py
│   └── remove_black_background.py
├── templates/                       pot files the app can load and save
│   ├── README.md                    their format
│   ├── 2025_2026/
│   │   ├── UCL_2025_2026.json
│   │   ├── UECL_2025_2026.json
│   │   └── UEL_2025_2026.json
│   └── 2026_2027/
│       └── UCL.json
└── uefa/                            shared settings
    ├── __init__.py
    └── config.py                    every path and constant of the project
```

Files ignored by Git (see `.gitignore`) are left out, and folders full of similar files are summed up on one line.

## Documentation

| Where | What you will find |
|---|---|
| [`model/docs/README.md`](model/docs/README.md) | The guide to the model: 12 pages, one per part (ratings, match model, draw, matchdays, name matching, one match, scores, league table, knockout, extra time, penalties, Monte Carlo). Each has a full example with real numbers, a small Python program to try, the modules used and the known bugs. |
| [`model/docs/code/`](model/docs/code/) | The code of each part, explained a few lines at a time. |
| [`datahandler/README.md`](datahandler/README.md) | Where the data comes from (API-Football, free plan), how to download it again, and its known problems. |
| [`templates/README.md`](templates/README.md) | The pot files the app can load and save, and their format. |
| [`interface/README.md`](interface/README.md) | How the interface was written, and the plan to rebuild it. |
| [Changelog](GHANGELOG.md) | Every notable change to the project, version by version. |

## Where the data comes from

All match data comes from [API-Football](https://www.api-football.com), on its free plan: one season of club football, 2024/25, about 5 300 matches (domestic leagues and cups, European competitions, friendlies). The free plan limits the project to recent seasons and 100 requests a day; [`datahandler/README.md`](datahandler/README.md) explains the details.

## Known limitations

- The ratings come from about 1.5 seasons of data, so many clubs stay close to their starting value.
- A match result depends only on the two clubs' ratings: no injuries, form, or players.
- The score of a match does not depend on how much stronger the winner is.
- The Monte Carlo treats the ratings as exact, so its probabilities are a little too confident.

The full list, with every known bug and how to fix it, is in [`model/docs/README.md`](model/docs/README.md#known-bugs-all-in-one-place).

---

## Future improvements in sight

- A better interface that is easier to customise.
- Other methods for simulating the competitions.
- Data from other seasons (the current data covers the 2024/25 season).
- The real rule for which club hosts the second leg in the quarter-finals and semi-finals (a coin toss for now).
- A tension bar: a bar you can set to show how tense a match is.

## Further improvements

- Include the players.
- Live simulation.

## Personal facts and opinions

- It took me about 3 months (started in July I think) to finish this project, because of school (lots of homework) and because of learning: I cannot learn all these concepts in one day. Of course, I forget some of them over time, because I only needed them once or twice.

## Feedback and advice

Feel free to share your remarks about any part of the project that needs fleshing out, adding or removing.

## Enjoyed it? Give it a star

![Star the project](assets/images/github/star_en.png)

If the project made you smile or taught you something, feel free to give it a star on GitHub (the little star at the top right of the page). It takes one second, it makes my day, and it helps other people find the project. No pressure, of course. Thank you for reading, and enjoy the football. ⚽⚽⚽

---
---

# [FR] Version française

# Simulateur des compétitions UEFA

*Le [journal des modifications](GHANGELOG.md) liste tous les changements notables du projet.*

## Que fait-il ?

Ce projet simule chacune des trois compétitions de clubs de l'UEFA : la Ligue des champions, la Ligue Europa et la Ligue Conférence. Il réalise aussi le tirage au sort du nouveau format (depuis 2024/25), qui est loin d'être simple à implémenter.

## Une petite démonstration

![Le menu](GIFs/GIF_1.gif)
Le menu

![Le tirage](GIFs/GIF_2.gif)
Le tirage

![La simulation](GIFs/GIF_3.gif)
La simulation

## Fonctionnalités

- Simule les trois compétitions de clubs de l'UEFA : Ligue des champions, Ligue Europa et Ligue Conférence, du tirage à la finale.
- Réalise le tirage de la phase de ligue avec les vraies contraintes : 8 adversaires par club (6 en Ligue Conférence), au plus 2 adversaires de la même association, et aucun de la sienne.
- Déroule le tirage comme une cérémonie animée, chapeau par chapeau, au lieu d'afficher seulement le résultat.
- Permet d'interdire un match à domicile précis (par exemple, Genk ne doit pas recevoir Brann) ; le tirage le respecte.
- Permet de remplacer n'importe quel club (nom, association, écusson), de charger des chapeaux depuis un modèle JSON et d'enregistrer les siens.
- Fournit les vrais chapeaux 2025/26 pour les trois compétitions.
- Construit le classement de la phase de ligue avec les critères de départage de l'UEFA, puis joue les barrages, les tours à élimination directe en aller-retour et une finale en un seul match sur terrain neutre.
- Propose trois méthodes pour les confrontations aller-retour : `legs`, `aggregate` et `oneshot`.
- Joue les séances de tirs au but tir par tir, donc chaque séance a un vrai score.
- Met à jour les notes Elo après chaque match simulé, si bien qu'un club en série de victoires devient plus fort au fil de la saison.
- Lancez une simulation de Monte-Carlo jusqu'à 10 000 saisons sur jusqu'à 8 cœurs du processeur, et affiche sous forme de carte de chaleur la probabilité de chaque club d'atteindre chaque tour.
- Garde un journal expert de chaque match, dans l'application et dans un fichier texte.
- Fonctionne en anglais et en français, avec un thème clair et un thème sombre.

## Comment ça marche, en 30 secondes

```
 5 300 vrais matchs ──> une note Elo par club ──> un modèle qui transforme deux notes
 (2024 à 2025)                                     en P(victoire dom.), P(nul), P(victoire ext.)
                                                              │
 les chapeaux ──> le tirage ──> les journées                  │
                                     │                        │
                                     ▼                        ▼
          une saison : chaque match reçoit un résultat et un score, les notes bougent après chaque match
                      ├── classement de la phase de ligue (top 8 / barrages / éliminés)
                      └── barrages, huitièmes, quarts, demies, finale
                                     │
                                     ▼
          répéter la saison jusqu'à 10 000 fois et compter jusqu'où va chaque club
```

Chaque étape est expliquée avec des mots simples, des exemples et de petits programmes Python, dans [`model/docs/`](model/docs/README.md).

---

## Comment le lancer ?

Toutes les commandes se lancent depuis le dossier `UEFA/` (celui qui contient `main.py`).

### Raccourci : le dossier `commands/`

Trois petits scripts par système : `get_to_file` (aller dans le dossier du projet), `req` (installer les paquets) et `run` (lancer l'application).

>Tout d’abord, vous devrez configurer les scripts présents dans ce dossier. Vous n’avez pas besoin de tous les modifier, seulement les fichiers `.sh` ou `.ps1` qui sont compatibles avec votre environnement et que vous comptez exécuter.

| Système | Dossier | Installer | Lancer |
|---|---|---|---|
| Windows (PowerShell) | `commands/windows/` | `.\commands\windows\req.ps1` | `.\commands\windows\run.ps1` |
| macOS | `commands/MacOs/` | `bash commands/MacOs/req.sh` | `bash commands/MacOs/run.sh` |
| Linux | `commands/linux/` | `bash commands/linux/req.sh` | `bash commands/linux/run.sh` |

Si PowerShell refuse d'exécuter un fichier `.ps1`, tapez une fois `Set-ExecutionPolicy -Scope Process RemoteSigned` dans cette fenêtre.

**Windows avec le Python Manager (la commande `py`), pour choisir votre version de Python :**

1. tapez `py --list` pour voir les versions installées sur votre ordinateur.
2. Ouvre `commands/python manager/req.ps1` et `commands/python manager/run.ps1`, et **remplace `3.12` par votre version** (3.10 ou plus récente) dans chacun.
3. Lancez-les : `.\"commands\python manager\req.ps1"` puis `.\"commands\python manager\run.ps1"`.

Sans les scripts, la même chose à la main (remplace `3.12` par votre version) :

```powershell
py -3.12 -m pip install -r requirements.txt
py -3.12 main.py
```

### 1. Ce qu'il faut

- **Python 3.10 ou plus récent.** Vérifiez avec `python --version`.
- **Tkinter**, la bibliothèque sur laquelle la fenêtre est construite. Il est inclus dans les installateurs Windows et macOS de python.org. Sur Debian ou Ubuntu, Ajoutez-le avec `sudo apt install python3-tk`. Il ne s'installe pas avec `pip`.
- **Aucune clé d'API n'est nécessaire pour lancer l'application.** Les chapeaux, les notes, les coefficients et les écussons sont fournis avec le projet. Une clé n'est utile que pour télécharger de nouvelles données (voir [`datahandler/`](datahandler/README.md)).

### 2. Créer un environnement virtuel (recommandé)

Un environnement virtuel garde les paquets de ce projet séparés du reste de l'ordinateur.

```bash
# Windows (PowerShell)
py -m venv .venv
.venv\Scripts\Activate.ps1

# macOS ou Linux
python3 -m venv .venv
source .venv/bin/activate
```

Si PowerShell refuse d'exécuter le script, tapez une fois `Set-ExecutionPolicy -Scope Process RemoteSigned` dans cette fenêtre, puis réactive. Quand ça marche, `(.venv)` s'affiche au début de la ligne de commande.

### 3. Installer les paquets nécessaires

```bash
pip install -r requirements.txt
```

| Paquet | À quoi il sert |
|---|---|
| `customtkinter` | la fenêtre et tous les écrans de l'application |
| `Pillow` | charger et redimensionner les écussons et les drapeaux |
| `pandas`, `numpy` | lire et nettoyer les vraies données de matchs ; recalculer les notes |
| `scikit-learn` | entraîner le modèle de match (une fois ; l'application lit ensuite seulement ses 8 nombres) |
| `requests` | télécharger les données et les écussons depuis API-Football |
| `python-dotenv` | lire la clé d'API dans le fichier `.env` |

### 4. Lancer l'application

```bash
python main.py
```

Le menu s'ouvre. Choisissez une langue, une compétition (Ligue des champions, Ligue Europa ou Ligue Conférence) et un mode : tirage seul ou simulation complète. Suivez ensuite les écrans : chapeaux, cérémonie du tirage, puis simulation.

### 5. Lancer les trois compétitions sans la fenêtre (facultatif)

Le modèle peut aussi tourner dans le terminal. Chaque commande fait le tirage de la compétition avec la graine 1, joue une saison complète avec le journal expert, puis un Monte-Carlo de 100 saisons, et affiche les dix clubs qui ont le plus de chances de gagner :

```bash
python -m model.simulation UCL     # Ligue des champions
python -m model.simulation UEL     # Ligue Europa
python -m model.simulation UECL    # Ligue Conférence
```

D'autres parties peuvent aussi être lancées seules :

| Commande | Ce qu'elle fait |
|---|---|
| `python -m model.draw_ucl` | un tirage de Ligue des champions et un de Ligue Europa, affichés chapeau par chapeau |
| `python -m model.draw_uecl` | un tirage de Ligue Conférence |
| `python -m model.matchdays_ucl` | un tirage réparti en 8 journées |
| `python -m model.predictor` | les chances de victoire à domicile, de nul et de victoire à l'extérieur pour quelques écarts de notes |
| `python -m model.predictor --train` | réentraîne le modèle de match (demande `scikit-learn`) |
| `python -m model.elo_score_updating_copy --write` | recalcule la note de chaque club à partir des vrais matchs (demande `pandas`) |
| `python -m model.scorelines` | reconstruit la table des vrais scores (demande `pandas`) |

### 6. En cas de problème

| Message ou symptôme | Cause et solution |
|---|---|
| `ModuleNotFoundError: No module named 'customtkinter'` | L'environnement virtuel n'est pas activé, ou l'étape 3 a été sautée. Activez-le, puis relancez `pip install -r requirements.txt`. |
| `ModuleNotFoundError: No module named 'model'` ou `'uefa'` | vous n'es pas dans le dossier `UEFA/`. Placez-vous dedans avec `cd`. |
| `No module named '_tkinter'` | Tkinter est absent. Voir l'étape 1. |
| `predictor_weights.json not found` | Le modèle de match n'a pas été entraîné. Lancez `python -m model.predictor --train`. |
| Un avertissement « not found in the Elo file, starting at 1500 » | Le nom d'un club n'a pas pu être relié à une note (en général un club que vous as ajouté toi-même). Voir [`model/docs/names.md`](model/docs/names.md). |
| « no valid draw found in 50 attempts » | Les matchs à domicile interdits rendent le tirage impossible. Retirez-en quelques-uns. |

---

## Organisation du projet

```
UEFA/
├── .env.example                     modèle pour votre propre fichier .env (clé d'API)
├── .gitignore                       ce que Git ne doit pas suivre
├── GHANGELOG.md                     le journal des modifications
├── image_downloader_logos.py        le script utilisé pour télécharger les écussons
├── main.py                          lance l'application
├── README.md                        ce fichier
├── requirements.txt                 les paquets à installer
├── assets/
│   └── images/
│       ├── clubs/                   écussons des clubs, un dossier par compétition
│       │   ├── UCL/                 36 écussons, un PNG par club
│       │   ├── UECL/                36 écussons, un PNG par club
│       │   └── UEL/                 36 écussons, un PNG par club
│       ├── compets/                 logos des compétitions
│       │   ├── UCL_logo.png
│       │   ├── UECL_logo.png
│       │   └── UEL_logo.png
│       ├── flags/                   drapeaux
│       │   ├── Flag_of_France.png
│       │   └── UK_US_flag.png
│       ├── github/                  images du README (bannière, étoiles)
│       │   ├── banner.png
│       │   ├── banner.svg
│       │   ├── star_en.png
│       │   └── star_fr.png
│       └── optional/                17 images facultatives
├── commands/                        scripts d'installation et de lancement prêts à l'emploi
│   ├── linux/                       Linux
│   │   ├── get_to_file.sh
│   │   ├── req.sh
│   │   └── run.sh
│   ├── MacOs/                       macOS
│   │   ├── get_to_file.sh
│   │   ├── req.sh
│   │   └── run.sh
│   ├── python manager/              Python Manager
│   │   ├── get_to_file.ps1
│   │   ├── req.ps1
│   │   └── run.ps1
│   └── windows/                     Windows
│       ├── get_to_file.ps1
│       ├── req.ps1
│       └── run.ps1
├── data/
│   ├── processed/                   données nettoyées : matchs, notes, journaux de simulation
│   │   ├── all_competitions_25.csv
│   │   ├── cleaned_clubs_25.csv
│   │   ├── countries_filled_25.csv
│   │   ├── eeelo_final.json
│   │   ├── fixtures_25.csv
│   │   ├── match_features.csv
│   │   ├── predictions.csv
│   │   ├── sim_UECL_20260916-192903.txt
│   │   ├── uefa_coefficients_2021_2022.csv
│   │   ├── uefa_coefficients_2022_23.csv
│   │   └── uefa_countries_25.csv
│   ├── raw/                         données telles que téléchargées
│   │   ├── fixtures_UCL/            36 fichiers JSON, un par club
│   │   ├── fixtures_UECL/           36 fichiers JSON, un par club
│   │   └── fixtures_UEL/            36 fichiers JSON, un par club
│   └── reference/                   réglages : coefficients, notes de départ, poids du modèle, table des scores
│       ├── coef_table.csv
│       ├── coefs.json
│       ├── confr.json
│       ├── country_seeds.json
│       ├── predictor_weights.json
│       ├── scorelines.json
│       ├── team_seed.json
│       ├── UCL.json
│       ├── UCL_updated.json
│       ├── UECL.json
│       ├── UECL_updated.json
│       ├── UEL.json
│       └── UEL_updated.json
├── datahandler/                     scripts qui téléchargent et nettoient les données d'API-Football
│   ├── __init__.py
│   ├── add_neutral_venue.py
│   ├── build_fixtures_csv.py
│   ├── build_team_seeds.py
│   ├── drop_duplicate_fixtures.py
│   ├── fetch_club_logos.py
│   ├── fetch_competition_logos.py
│   ├── fetch_fixtures.py
│   ├── fetch_leagues.py
│   ├── fetch_team_ids.py
│   ├── README.md                    d'où viennent les données
│   └── img/                         4 schémas (versions anglaise et française)
├── GIFs/                            la démonstration ci-dessus
│   ├── GIF_1.gif
│   ├── GIF_2.gif
│   └── GIF_3.gif
├── interface/                       la fenêtre et ses écrans (CustomTkinter)
│   ├── app.py                       la fenêtre et le routeur
│   ├── base_view.py                 le contrat commun à tous les écrans
│   ├── canvas_views.py              les trois grands tableaux de l'écran des résultats
│   ├── chrome.py                    les deux barres qui ne bougent jamais
│   ├── config.py
│   ├── draw_engine.py               pont entre l'interface et model/
│   ├── draw_widgets.py              éléments de l'écran du tirage
│   ├── fonts.py                     la typographie
│   ├── images.py                    fabrique toutes les images de l'application
│   ├── main.py                      point d'entrée de l'interface
│   ├── platform_utils.py
│   ├── README.md                    comment l'interface a été écrite
│   ├── sim_engine.py                pont vers model/simulation.py
│   ├── sim_view.py                  l'écran de simulation
│   ├── theme.py                     apparence par défaut des widgets
│   ├── transition.py                moteur d'animation
│   ├── views.py                     les écrans du menu
│   └── widgets.py                   éléments réutilisables
├── model/                           le tirage, les notes, le modèle de match et la simulation
│   ├── __init__.py
│   ├── categorising.py              construit la table de catégories (championnat, tour)
│   ├── coefs.py
│   ├── draw_ucl.py                  moteur de tirage, phase de ligue à 8 matchs (LDC, LE)
│   ├── draw_uecl.py                 moteur de tirage, phase de ligue à 6 matchs (LC)
│   ├── elo_score_updating_copy.py   déroule les notes Elo sur une saison
│   ├── knockout.py                  barrages et phases à élimination directe
│   ├── league_phase.py              joue la phase de ligue et classe les 36 clubs
│   ├── match_engine.py              joue un match
│   ├── matchdays_ucl.py             découpe un tirage en journées (LDC, LE)
│   ├── matchdays_uecl.py            découpe un tirage en journées (LC)
│   ├── names.py                     relie les noms de clubs écrits différemment
│   ├── penalties.py                 tirs au but, un tir à la fois
│   ├── predict_matches_uefa.py
│   ├── predictor.py                 modèle de résultat de match (régression logistique)
│   ├── prepredictator.py            entraîne le classifieur de résultats
│   ├── scorelines.py                transforme un résultat en score
│   ├── seeding.py
│   ├── simulation.py                simule toute une compétition
│   ├── testing.py
│   ├── tests.py
│   └── docs/                        comment fonctionne chaque partie, en anglais et en français
│       ├── draw.md
│       ├── elo.md
│       ├── extra_time.md
│       ├── knockout.md
│       ├── league_phase.md
│       ├── logistic_regression.md
│       ├── match_engine.md
│       ├── matchdays.md
│       ├── monte_carlo.md
│       ├── names.md
│       ├── penalties.md
│       ├── README.md                le guide du modèle
│       ├── scorelines.md
│       ├── code/                    11 pages, le code de chaque partie expliqué
│       └── img/                     24 images (versions anglaise et française)
├── scripts/                         petits outils ponctuels (écussons, nettoyage d'images)
│   ├── fetch_template_badges.py
│   └── remove_black_background.py
├── templates/                       fichiers de chapeaux que l'application peut charger et enregistrer
│   ├── README.md                    leur format
│   ├── 2025_2026/
│   │   ├── UCL_2025_2026.json
│   │   ├── UECL_2025_2026.json
│   │   └── UEL_2025_2026.json
│   └── 2026_2027/
│       └── UCL.json
└── uefa/                            réglages communs
    ├── __init__.py
    └── config.py                    tous les chemins et constantes du projet
```

Les fichiers ignorés par Git (voir `.gitignore`) ne sont pas montrés, et les dossiers remplis de fichiers semblables sont résumés sur une seule ligne.

## Documentation

| Où | Ce que vous y trouveras |
|---|---|
| [`model/docs/README.md`](model/docs/README.md) | Le guide du modèle : 12 pages, une par partie (notes, modèle de match, tirage, journées, correspondance des noms, un match, scores, classement, élimination directe, prolongation, tirs au but, Monte-Carlo). Chacune contient un exemple complet avec de vrais nombres, un petit programme Python à essayer, les modules utilisés et les bugs connus. |
| [`model/docs/code/`](model/docs/code/) | Le code de chaque partie, expliqué quelques lignes à la fois. |
| [`datahandler/README.md`](datahandler/README.md) | D'où viennent les données (API-Football, plan gratuit), comment les télécharger à nouveau, et leurs problèmes connus. |
| [`templates/README.md`](templates/README.md) | Les fichiers de chapeaux que l'application peut charger et enregistrer, et leur format. |
| [`interface/README.md`](interface/README.md) | Comment l'interface a été écrite, et le projet de la reconstruire. |
| [Journal des modifications](GHANGELOG.md) | Chaque changement notable du projet, version par version. |

## D'où viennent les données

Toutes les données de matchs viennent d'[API-Football](https://www.api-football.com), avec son plan gratuit : une saison de football de clubs, 2024/25, environ 5 300 matchs (championnats et coupes nationaux, compétitions européennes, amicaux). Le plan gratuit limite le projet aux saisons récentes et à 100 requêtes par jour ; [`datahandler/README.md`](datahandler/README.md) explique les détails.

## Limites connues

- Les notes viennent d'environ 1.5 saison de données, donc beaucoup de clubs restent proches de leur valeur de départ.
- Le résultat d'un match ne dépend que des notes des deux clubs : pas de blessures, de forme, ni de joueurs.
- Le score d'un match ne dépend pas de l'écart de force entre les deux clubs.
- Le Monte-Carlo traite les notes comme exactes, donc ses probabilités sont un peu trop sûres d'elles.

La liste complète, avec chaque bug connu et sa correction, est dans [`model/docs/README.md`](model/docs/README.md#les-bugs-connus-au-même-endroit).

---

## Améliorations en vue

- Une meilleure interface, plus facile à personnaliser.
- D'autres méthodes pour simuler les compétitions.
- Des données d'autres saisons (les données actuelles couvrent la saison 2024/25).
- La vraie règle qui décide quel club reçoit au match retour en quarts et en demies (tirée à pile ou face pour l'instant).
- Une barre de tension : une barre que l'on peut régler pour indiquer à quel point un match est tendu.

## Améliorations plus lointaines

- Inclure les joueurs.
- Une simulation en direct.

## Faits et avis personnels

- Il m'a fallu environ 3 mois (commencé en juillet je crois) pour finir ce projet, à cause de l'école (beaucoup de devoirs) et de l'apprentissage : je ne peux pas apprendre tous ces concepts en un jour. Bien sûr, j'en oublie certains avec le temps, car je n'en ai eu besoin qu'une ou deux fois.


## Pourquoi le project n'est pas considéré comme "temriné" pour mettre la version 1.0.0 ? 

> En réalité, j'ai encore envie de personnaliser les templates pour les aciennes et nouvelles saisons pour les trois compétitions. Je veux également mieux organiser la structure du projet.
## Remarques et conseils

N'hésitez pas à partager vos remarques sur une partie du projet qui mériterait d'être développée, ajoutée ou retirée.


## Il vous a plu ? Offre-lui une étoile

![Offrez une étoile](assets/images/github/star_fr.png)

Si le projet vous a fait sourire ou vous a appris quelque chose, N'hésitez pas à lui laisser une étoile sur GitHub (la petite étoile en haut à droite de la page). Ça prend une seconde, ça me fait très plaisir, et ça aide d'autres personnes à trouver le projet. Aucune obligation, bien sûr. Merci de m'avoir lu, et amusez-vous bien avec le football. ⚽⚽⚽
