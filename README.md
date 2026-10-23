<p align="center">
  <img src="assets/images/github/readme/header_en.svg" alt="UEFA Competitions Simulator: run the draw, play the season, find out who wins" width="100%">
</p>

<p align="center">
  <a href="https://github.com/yassinox12834/UEFA-Competitions-Simulator/releases/latest"><img src="https://img.shields.io/github/v/release/yassinox12834/UEFA-Competitions-Simulator?style=flat-square&color=2FA96B&label=release" alt="Latest release"></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-3E7BFA?style=flat-square&logo=python&logoColor=white" alt="Python 3.10 or newer">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-E8833A?style=flat-square" alt="Windows, macOS and Linux">
  <img src="https://img.shields.io/badge/language-English%20%7C%20Fran%C3%A7ais-8B93A5?style=flat-square" alt="English and French">
  <a href="LICENSE"><img src="https://img.shields.io/badge/licence-MIT-E6BE5A?style=flat-square" alt="MIT licence"></a>
</p>

<p align="center">
  <a href="#fr-version-française"><b>🇫🇷 Version française</b></a> ·
  <a href="CHANGELOG.md">Changelog</a> ·
  <a href="https://github.com/yassinox12834/UEFA-Competitions-Simulator/issues">Report a bug</a>
</p>

<p align="center">
  <a href="https://github.com/yassinox12834/UEFA-Competitions-Simulator/releases/latest">
    <img src="assets/images/github/readme/download_en.svg" alt="Download for Windows" width="340">
  </a>
</p>

<p align="center">
  <a href="#see-it-in-action">See it</a> ·
  <a href="#what-you-can-do">Features</a> ·
  <a href="#how-it-works">How it works</a> ·
  <a href="#quick-start">Quick start</a> ·
  <a href="#if-something-goes-wrong">Problems?</a> ·
  <a href="#build-the-app-yourself">Build</a> ·
  <a href="#documentation">Docs</a>
</p>

## What is it?

A desktop app that plays the three European club competitions for you: the **Champions League**, the **Europa League** and the **Conference League**.

It runs the draw with the real UEFA rules, plays every match of the season, and can replay the whole season **thousands of times** to show each club's real chances of going far.

## See it in action

<p align="center">
  <img src="GIFs/GIF_1.gif" alt="The menu" width="820"><br>
  <sub><b>The menu.</b> Pick a language, a competition and a mode.</sub>
</p>

<p align="center">
  <img src="GIFs/GIF_2.gif" alt="The draw" width="820"><br>
  <sub><b>The draw.</b> Played out pot by pot, like the real ceremony.</sub>
</p>

<p align="center">
  <img src="GIFs/GIF_3.gif" alt="The simulation" width="820"><br>
  <sub><b>The simulation.</b> League table, knockout rounds, and each club's chances.</sub>
</p>

## What you can do

| | |
|---|---|
| 🎱 **Run the draw** | With the real rules: 8 opponents per club (6 in the Conference League), never a club from the same country, at most 2 from any other country. |
| 🎬 **Watch the ceremony** | Pot by pot, or skip straight to the result. |
| ✏️ **Change the clubs** | Replace any club, ban a match you do not want (for example, Genk must not play at home against Brann), load pots from a file, or save your own. |
| ⚽ **Play a full season** | League table, play-offs, knockout rounds and a final on neutral ground. Every match gets a real score; penalty shoot-outs are played kick by kick. |
| 📈 **Follow the form** | A club that keeps winning gets stronger during the season. |
| 🔁 **Replay it 10,000 times** | See, for each club, how often it reaches each round. |
| 📄 **Read every detail** | A full report of every match, in the app and as a text file. |
| 🌍 **Your way** | English or French, light or dark theme. |

The real 2025/26 pots of all three competitions are already included.

## How it works

<p align="center">
  <img src="assets/images/github/readme/how_it_works_en.svg" alt="How it works: real matches, club ratings, the draw, the season, repeat" width="100%">
</p>

1. **Real matches.** The app learns from about 5,300 real games of the 2024/25 season.
2. **Club ratings.** From those results, every club gets a strength score, called an Elo rating. Beating a strong club earns more than beating a weak one.
3. **The draw.** The pots are drawn with the same rules UEFA uses.
4. **The season.** For each match, the app turns the two clubs' ratings into chances (home win, draw, away win), then picks a result and a score.
5. **Repeat.** One season is a story; 10,000 seasons give real chances.

Each step is explained with examples and small Python programs in [`model/docs/`](model/docs/README.md).

### How a season works

Since 2024/25, the three competitions use a new format. If you have not followed it, here it is in one picture:

<p align="center">
  <img src="assets/images/github/readme/season_en.svg" alt="League phase of 36 clubs, then play-offs, round of 16, quarter-finals, semi-finals and final" width="100%">
</p>

---

## Quick start

### Option 1: the Windows app (no Python needed)

1. Open the [latest release](https://github.com/yassinox12834/UEFA-Competitions-Simulator/releases/latest) and download `UEFA-Simulator-windows.zip`.
2. Unzip it, open the folder, and double-click `UEFA-Simulator.exe`.

Windows may say the publisher is unknown, because the app is not signed: click **More info**, then **Run anyway**. The pots you save and the match reports go to `C:\Users\<you>\UEFA-Simulator\`.

### Option 2: from the source code

For macOS and Linux, or if you want to read and change the code.

<p align="center">
  <img src="assets/images/github/readme/quick_start_en.svg" alt="Three steps: get Python, install the packages, launch the app" width="100%">
</p>

**You need:**

- **Python 3.10 or newer.** Check with `python --version` (`python3 --version` on macOS and Linux).
- **Tkinter**, which draws the window. It comes with the installers from [python.org](https://www.python.org/downloads/) on Windows and macOS. On Debian or Ubuntu: `sudo apt install python3-tk python3-venv`. It cannot be installed with `pip`.
- **No API key.** Everything the app needs is already in the project. A key is only needed to download new data (see [`datahandler/`](datahandler/README.md)).

**Get the code:**

```bash
git clone https://github.com/yassinox12834/UEFA-Competitions-Simulator.git
cd UEFA-Competitions-Simulator
```

**Then pick your system.** Each script first moves to the project folder, so it works from anywhere. The `req` script puts the packages in a `.venv` folder inside the project, and `run` uses it automatically: nothing to activate.

<details open>
<summary><b>🪟 Windows (PowerShell)</b></summary>

```powershell
.\commands\windows\req.ps1      # once: install the packages
.\commands\windows\run.ps1      # every time: launch the app
```

If PowerShell says that running scripts is disabled, type this once in that window, then try again:

```powershell
Set-ExecutionPolicy -Scope Process RemoteSigned
```

</details>

<details>
<summary><b>🪟 Windows, choosing your Python version (<code>py</code>)</b></summary>

Use these if you have several versions of Python and want to pick one. They install the packages for that version directly, without a `.venv`.

1. Type `py --list` to see the versions installed on your computer.
2. Open [`commands/python manager/version.ps1`](commands/python%20manager/version.ps1) and replace `3.12` with one of them (3.10 or newer). It is the only line to change: the three scripts read it from there.
3. Run them. The path has a space, so it needs quotes and `&` in front:

```powershell
& ".\commands\python manager\req.ps1"      # once
& ".\commands\python manager\run.ps1"      # every time
```

If the version you wrote is not installed, the script says so and lists the ones you have.

</details>

<details>
<summary><b>🍎 macOS</b></summary>

```bash
bash commands/MacOs/req.sh      # once: install the packages
bash commands/MacOs/run.sh      # every time: launch the app
```

If you installed Python with Homebrew, Tkinter is separate: `brew install python-tk`.

</details>

<details>
<summary><b>🐧 Linux</b></summary>

```bash
sudo apt install python3-tk python3-venv   # Debian or Ubuntu, once
bash commands/linux/req.sh                 # once: install the packages
bash commands/linux/run.sh                 # every time: launch the app
```

</details>

<details>
<summary><b>⌨️ Without the scripts, by hand</b></summary>

```bash
# 1. Create a virtual environment and activate it
py -m venv .venv                 # Windows
.venv\Scripts\Activate.ps1       # Windows: "(.venv)" appears at the start of the line

python3 -m venv .venv            # macOS or Linux
source .venv/bin/activate        # macOS or Linux

# 2. Install the packages, then launch
python -m pip install -r requirements.txt
python main.py
```

Every command runs from the project folder, the one that contains `main.py`.

</details>

Then pick a language, a competition and a mode (draw only, or full simulation), and follow the screens.

<details>
<summary><b>What each package is for</b></summary>

| Package | What it is for |
|---|---|
| `customtkinter` | the window and every screen |
| `Pillow` | the club badges and flags |
| `pandas`, `numpy` | rebuilding the ratings from the real matches (the app itself does not need them) |
| `scikit-learn` | training the match model again (the app only reads its 8 saved numbers) |
| `requests`, `python-dotenv` | downloading new data from API-Football |

</details>

<details>
<summary><b>Without the window: the terminal commands</b></summary>

The simulation also runs in the terminal. Each command makes a draw, plays one season with the full match report, replays it 100 times, and prints the ten clubs most likely to win:

```bash
python -m model.simulation UCL     # Champions League
python -m model.simulation UEL     # Europa League
python -m model.simulation UECL    # Conference League
```

| Command | What it does |
|---|---|
| `python -m model.draw_ucl` | one Champions League and one Europa League draw, printed pot by pot |
| `python -m model.draw_uecl` | one Conference League draw |
| `python -m model.matchdays_ucl` | a draw split into 8 matchdays |
| `python -m model.predictor` | the chances of home win, draw and away win for a few rating gaps |
| `python -m model.predictor --train` | trains the match model again (needs `scikit-learn`) |
| `python -m model.elo_score_updating_copy --write` | rebuilds every club's rating from the real matches (needs `pandas`) |
| `python -m model.scorelines` | rebuilds the table of real scores (needs `pandas`) |

Activate the `.venv` first (see "by hand" above), or replace `python` with `.venv\Scripts\python` on Windows and `.venv/bin/python` on macOS and Linux.

</details>

## If something goes wrong

| Message | What to do |
|---|---|
| `running scripts is disabled on this system` | Type `Set-ExecutionPolicy -Scope Process RemoteSigned` in that PowerShell window, then try again. |
| `Python was not found` | Install Python from [python.org](https://www.python.org/downloads/) and tick **Add python.exe to PATH** in the installer. |
| `Python 3.12 is not installed on this computer` | You use the `python manager` scripts: put one of your versions in [`version.ps1`](commands/python%20manager/version.ps1). |
| `The packages are missing` | Run the `req` script for your system first. |
| `No module named 'customtkinter'` | Same cause: the packages are not installed for the Python you are using. Run the `req` script, or activate the `.venv` before `python main.py`. |
| `externally-managed-environment` | Your Linux or Homebrew Python refuses `pip install` outside a virtual environment. Use `req.sh`, which makes one for you. |
| `Tkinter is missing` or `No module named '_tkinter'` | See "You need" above. |
| `No module named 'model'` or `'uefa'` | You are not in the project folder. Use `cd` to go there, or use the scripts. |
| `predictor_weights.json not found` | Run `python -m model.predictor --train`. |
| "not found in the Elo file, starting at 1500" | The app could not find a rating for a club, usually one you added yourself. See [`model/docs/names.md`](model/docs/names.md). |
| "no valid draw found in 50 attempts" | The matches you banned make the draw impossible. Remove some of them. |
| `Failed to load Python DLL` | You opened the `.exe` in `build\`. The real app is in `dist\UEFA-Simulator\`. |
| `PermissionError: [WinError 5] Access is denied` while building | A file in `dist\UEFA-Simulator\` is in use. Close the app and any Explorer window on that folder. If the project is in OneDrive, pause syncing, then build again. |

## Build the app yourself

The Windows app is made with [PyInstaller](https://pyinstaller.org). The recipe is in [`UEFA-Simulator.spec`](UEFA-Simulator.spec).

| System | Build command | Result |
|---|---|---|
| Windows | `.\commands\windows\build.ps1` | `dist\UEFA-Simulator-windows.zip` |
| Windows (`py`) | `& ".\commands\python manager\build.ps1"` | `dist\UEFA-Simulator-windows.zip` |
| macOS | `bash commands/MacOs/build.sh` | `dist/UEFA-Simulator-macos.zip` |
| Linux | `bash commands/linux/build.sh` | `dist/UEFA-Simulator-linux.tar.gz` |

The scripts use the `.venv` if there is one. The app itself is in `dist\UEFA-Simulator\`; the `build\` folder only holds PyInstaller's working files.

Build on the system you want the app for: a Windows `.exe` cannot be made on Linux or macOS. The macOS and Linux scripts have not been tested yet.

> [!TIP]
> If the `.exe` closes at once without a message, set `console=True` in `UEFA-Simulator.spec` and build again: a black window will show the error. Set it back to `False` before you publish.

---

## Project structure

<details>
<summary><b>Show the folders</b></summary>

```
UEFA-Competitions-Simulator/
├── main.py                 starts the app
├── UEFA-Simulator.spec     the recipe for the Windows app
├── requirements.txt        the packages to install
├── commands/               ready-made scripts: install, launch, build
├── model/                  the draw, the ratings, the match model and the simulation
│   └── docs/               how each part works, in English and French
├── interface/              the window and its screens
├── uefa/                   where every file is (paths) and the project settings
├── datahandler/            downloads and cleans the data from API-Football
├── data/
│   ├── raw/                data as downloaded
│   ├── processed/          cleaned data: matches, ratings, match reports
│   └── reference/          settings: coefficients, starting ratings, model numbers
├── templates/              sets of pots the app can load and save
├── assets/images/          club badges, competition logos, flags, README pictures
├── scripts/                small one-off tools
└── GIFs/                   the demonstration above
```

</details>

## Documentation

| Where | What you will find |
|---|---|
| [`model/docs/`](model/docs/README.md) | The guide to the model, 12 short pages: ratings, match model, draw, matchdays, club names, one match, scores, league table, knockout, extra time, penalties, replaying the season. Each has a full example with real numbers and a small Python program to try. |
| [`model/docs/code/`](model/docs/code/) | The code of each part, explained a few lines at a time. |
| [`datahandler/`](datahandler/README.md) | Where the data comes from and how to download it again. |
| [`templates/`](templates/README.md) | The pot files the app can load and save. |
| [`interface/`](interface/README.md) | How the interface was written. |
| [Changelog](CHANGELOG.md) | Every notable change, version by version. |

## Where the data comes from

All match data comes from [API-Football](https://www.api-football.com), on its free plan: the 2024/25 club season, about 5,300 matches (leagues, cups, European games and friendlies). The free plan only gives recent seasons and 100 requests a day; [`datahandler/`](datahandler/README.md) explains more.

## Known limits

- The ratings come from about a season and a half of matches, so many clubs stay close to their starting value.
- A result depends only on the two clubs' ratings: no injuries, no players, no recent form before the season.
- The score of a match does not depend on how much stronger the winner is.
- The ratings are treated as exact, so the chances shown are a little too sure of themselves.

The full list, with every known bug, is in [`model/docs/`](model/docs/README.md#known-bugs-all-in-one-place).

## Ideas for later

- [ ] An interface that is easier to change.
- [ ] Data from other seasons.
- [ ] The real rule for who plays the second leg at home in the quarter-finals and semi-finals (a coin toss for now).
- [ ] A "tension" bar that shows how tight a match is.
- [ ] Players, and a live simulation.

## Feedback

Found a bug, or have an idea? [Open an issue](https://github.com/yassinox12834/UEFA-Competitions-Simulator/issues). If the project was useful to you, a ⭐ helps other people find it.

## Licence

MIT, see [LICENSE](LICENSE).

<br>

---
---

<br>

# [FR] Version française

<p align="center">
  <img src="assets/images/github/readme/header_fr.svg" alt="Simulateur des compétitions UEFA : faites le tirage, jouez la saison, découvrez le vainqueur" width="100%">
</p>

<p align="center">
  <a href="#what-is-it"><b>🇬🇧 English version</b></a> ·
  <a href="CHANGELOG.md">Journal des modifications</a> ·
  <a href="https://github.com/yassinox12834/UEFA-Competitions-Simulator/issues">Signaler un bug</a>
</p>

<p align="center">
  <a href="https://github.com/yassinox12834/UEFA-Competitions-Simulator/releases/latest">
    <img src="assets/images/github/readme/download_fr.svg" alt="Télécharger pour Windows" width="340">
  </a>
</p>

<p align="center">
  <a href="#en-images">En images</a> ·
  <a href="#ce-que-vous-pouvez-faire">Fonctions</a> ·
  <a href="#comment-ça-marche">Comment ça marche</a> ·
  <a href="#démarrage-rapide">Démarrage rapide</a> ·
  <a href="#en-cas-de-problème">Un problème ?</a> ·
  <a href="#créer-lapplication-vous-même">Créer l'application</a> ·
  <a href="#documentation-1">Docs</a>
</p>

## Qu'est-ce que c'est ?

Une application qui joue pour vous les trois compétitions européennes de clubs : la **Ligue des champions**, la **Ligue Europa** et la **Ligue Conférence**.

Elle fait le tirage avec les vraies règles de l'UEFA, joue chaque match de la saison, et peut rejouer toute la saison **des milliers de fois** pour montrer les vraies chances de chaque club d'aller loin.

## En images

<p align="center">
  <img src="GIFs/GIF_1.gif" alt="Le menu" width="820"><br>
  <sub><b>Le menu.</b> Choisissez une langue, une compétition et un mode.</sub>
</p>

<p align="center">
  <img src="GIFs/GIF_2.gif" alt="Le tirage" width="820"><br>
  <sub><b>Le tirage.</b> Chapeau par chapeau, comme la vraie cérémonie.</sub>
</p>

<p align="center">
  <img src="GIFs/GIF_3.gif" alt="La simulation" width="820"><br>
  <sub><b>La simulation.</b> Classement, phases finales, et les chances de chaque club.</sub>
</p>

## Ce que vous pouvez faire

| | |
|---|---|
| 🎱 **Faire le tirage** | Avec les vraies règles : 8 adversaires par club (6 en Ligue Conférence), jamais un club du même pays, au plus 2 d'un même autre pays. |
| 🎬 **Regarder la cérémonie** | Chapeau par chapeau, ou directement le résultat. |
| ✏️ **Changer les clubs** | Remplacer n'importe quel club, interdire un match (par exemple, Genk ne doit pas recevoir Brann), charger des chapeaux depuis un fichier, ou enregistrer les vôtres. |
| ⚽ **Jouer une saison complète** | Classement, barrages, phases finales et une finale sur terrain neutre. Chaque match a un vrai score ; les tirs au but sont joués tir par tir. |
| 📈 **Suivre la forme** | Un club qui gagne souvent devient plus fort pendant la saison. |
| 🔁 **La rejouer 10 000 fois** | Voir, pour chaque club, à quelle fréquence il atteint chaque tour. |
| 📄 **Lire chaque détail** | Un compte rendu complet de chaque match, dans l'application et dans un fichier texte. |
| 🌍 **À votre façon** | Anglais ou français, thème clair ou sombre. |

Les vrais chapeaux 2025/26 des trois compétitions sont déjà inclus.

## Comment ça marche

<p align="center">
  <img src="assets/images/github/readme/how_it_works_fr.svg" alt="Comment ça marche : vrais matchs, notes des clubs, tirage, saison, on recommence" width="100%">
</p>

1. **Vrais matchs.** L'application apprend à partir d'environ 5 300 vrais matchs de la saison 2024/25.
2. **Notes des clubs.** À partir de ces résultats, chaque club reçoit une note de force, appelée note Elo. Battre un club fort rapporte plus que battre un club faible.
3. **Le tirage.** Les chapeaux sont tirés avec les mêmes règles que l'UEFA.
4. **La saison.** Pour chaque match, l'application transforme les notes des deux clubs en chances (victoire à domicile, nul, victoire à l'extérieur), puis choisit un résultat et un score.
5. **On recommence.** Une saison, c'est une histoire ; 10 000 saisons donnent de vraies chances.

Chaque étape est expliquée avec des exemples et de petits programmes Python dans [`model/docs/`](model/docs/README.md).

### Comment se déroule une saison

Depuis 2024/25, les trois compétitions ont un nouveau format. Si vous ne l'avez pas suivi, le voici en une image :

<p align="center">
  <img src="assets/images/github/readme/season_fr.svg" alt="Phase de ligue de 36 clubs, puis barrages, huitièmes, quarts, demies et finale" width="100%">
</p>

---

## Démarrage rapide

### Option 1 : l'application Windows (sans Python)

1. Ouvrez la [dernière version](https://github.com/yassinox12834/UEFA-Competitions-Simulator/releases/latest) et téléchargez `UEFA-Simulator-windows.zip`.
2. Décompressez-le, ouvrez le dossier, et double-cliquez sur `UEFA-Simulator.exe`.

Windows peut dire que l'éditeur est inconnu, car l'application n'est pas signée : cliquez sur **Informations complémentaires**, puis sur **Exécuter quand même**. Les chapeaux que vous enregistrez et les comptes rendus vont dans `C:\Users\<vous>\UEFA-Simulator\`.

### Option 2 : depuis le code source

Pour macOS et Linux, ou si vous voulez lire et modifier le code.

<p align="center">
  <img src="assets/images/github/readme/quick_start_fr.svg" alt="Trois étapes : installer Python, installer les paquets, lancer l'application" width="100%">
</p>

**Il vous faut :**

- **Python 3.10 ou plus récent.** Vérifiez avec `python --version` (`python3 --version` sur macOS et Linux).
- **Tkinter**, qui dessine la fenêtre. Il est inclus dans les installateurs de [python.org](https://www.python.org/downloads/) sur Windows et macOS. Sur Debian ou Ubuntu : `sudo apt install python3-tk python3-venv`. Il ne s'installe pas avec `pip`.
- **Aucune clé d'API.** Tout ce dont l'application a besoin est déjà dans le projet. Une clé ne sert qu'à télécharger de nouvelles données (voir [`datahandler/`](datahandler/README.md)).

**Récupérez le code :**

```bash
git clone https://github.com/yassinox12834/UEFA-Competitions-Simulator.git
cd UEFA-Competitions-Simulator
```

**Puis choisissez votre système.** Chaque script se place d'abord dans le dossier du projet, il marche donc depuis n'importe où. Le script `req` installe les paquets dans un dossier `.venv` du projet, et `run` l'utilise tout seul : rien à activer.

<details open>
<summary><b>🪟 Windows (PowerShell)</b></summary>

```powershell
.\commands\windows\req.ps1      # une fois : installer les paquets
.\commands\windows\run.ps1      # à chaque fois : lancer l'application
```

Si PowerShell dit que l'exécution de scripts est désactivée, tapez une fois ceci dans cette fenêtre, puis réessayez :

```powershell
Set-ExecutionPolicy -Scope Process RemoteSigned
```

</details>

<details>
<summary><b>🪟 Windows, en choisissant votre version de Python (<code>py</code>)</b></summary>

Pour ceux qui ont plusieurs versions de Python et veulent en choisir une. Ces scripts installent les paquets directement pour cette version, sans `.venv`.

1. Tapez `py --list` pour voir les versions installées sur votre ordinateur.
2. Ouvrez [`commands/python manager/version.ps1`](commands/python%20manager/version.ps1) et remplacez `3.12` par l'une d'elles (3.10 ou plus récente). C'est la seule ligne à changer : les trois scripts la lisent là.
3. Lancez-les. Le chemin contient un espace, il faut donc des guillemets et un `&` devant :

```powershell
& ".\commands\python manager\req.ps1"      # une fois
& ".\commands\python manager\run.ps1"      # à chaque fois
```

Si la version écrite n'est pas installée, le script le dit et affiche celles que vous avez.

</details>

<details>
<summary><b>🍎 macOS</b></summary>

```bash
bash commands/MacOs/req.sh      # une fois : installer les paquets
bash commands/MacOs/run.sh      # à chaque fois : lancer l'application
```

Si vous avez installé Python avec Homebrew, Tkinter est à part : `brew install python-tk`.

</details>

<details>
<summary><b>🐧 Linux</b></summary>

```bash
sudo apt install python3-tk python3-venv   # Debian ou Ubuntu, une fois
bash commands/linux/req.sh                 # une fois : installer les paquets
bash commands/linux/run.sh                 # à chaque fois : lancer l'application
```

</details>

<details>
<summary><b>⌨️ Sans les scripts, à la main</b></summary>

```bash
# 1. Créer un environnement virtuel et l'activer
py -m venv .venv                 # Windows
.venv\Scripts\Activate.ps1       # Windows : "(.venv)" s'affiche au début de la ligne

python3 -m venv .venv            # macOS ou Linux
source .venv/bin/activate        # macOS ou Linux

# 2. Installer les paquets, puis lancer
python -m pip install -r requirements.txt
python main.py
```

Toutes les commandes se lancent depuis le dossier du projet, celui qui contient `main.py`.

</details>

Choisissez ensuite une langue, une compétition et un mode (tirage seul, ou simulation complète), puis suivez les écrans.

<details>
<summary><b>À quoi sert chaque paquet</b></summary>

| Paquet | À quoi il sert |
|---|---|
| `customtkinter` | la fenêtre et tous les écrans |
| `Pillow` | les écussons des clubs et les drapeaux |
| `pandas`, `numpy` | recalculer les notes à partir des vrais matchs (l'application elle-même n'en a pas besoin) |
| `scikit-learn` | réentraîner le modèle de match (l'application lit seulement ses 8 nombres enregistrés) |
| `requests`, `python-dotenv` | télécharger de nouvelles données depuis API-Football |

</details>

<details>
<summary><b>Sans la fenêtre : les commandes du terminal</b></summary>

La simulation tourne aussi dans le terminal. Chaque commande fait un tirage, joue une saison avec le compte rendu complet, la rejoue 100 fois, et affiche les dix clubs qui ont le plus de chances de gagner :

```bash
python -m model.simulation UCL     # Ligue des champions
python -m model.simulation UEL     # Ligue Europa
python -m model.simulation UECL    # Ligue Conférence
```

| Commande | Ce qu'elle fait |
|---|---|
| `python -m model.draw_ucl` | un tirage de Ligue des champions et un de Ligue Europa, affichés chapeau par chapeau |
| `python -m model.draw_uecl` | un tirage de Ligue Conférence |
| `python -m model.matchdays_ucl` | un tirage réparti en 8 journées |
| `python -m model.predictor` | les chances de victoire à domicile, de nul et de victoire à l'extérieur pour quelques écarts de notes |
| `python -m model.predictor --train` | réentraîne le modèle de match (demande `scikit-learn`) |
| `python -m model.elo_score_updating_copy --write` | recalcule la note de chaque club à partir des vrais matchs (demande `pandas`) |
| `python -m model.scorelines` | reconstruit la table des vrais scores (demande `pandas`) |

Activez d'abord le `.venv` (voir « à la main » ci-dessus), ou remplacez `python` par `.venv\Scripts\python` sous Windows et `.venv/bin/python` sous macOS et Linux.

</details>

## En cas de problème

| Message | Que faire |
|---|---|
| `running scripts is disabled on this system` | Tapez `Set-ExecutionPolicy -Scope Process RemoteSigned` dans cette fenêtre PowerShell, puis réessayez. |
| `Python was not found` | Installez Python depuis [python.org](https://www.python.org/downloads/) et cochez **Add python.exe to PATH** dans l'installateur. |
| `Python 3.12 is not installed on this computer` | Vous utilisez les scripts `python manager` : mettez l'une de vos versions dans [`version.ps1`](commands/python%20manager/version.ps1). |
| `The packages are missing` | Lancez d'abord le script `req` de votre système. |
| `No module named 'customtkinter'` | Même cause : les paquets ne sont pas installés pour le Python que vous utilisez. Lancez le script `req`, ou activez le `.venv` avant `python main.py`. |
| `externally-managed-environment` | Votre Python Linux ou Homebrew refuse `pip install` hors d'un environnement virtuel. Utilisez `req.sh`, qui en crée un pour vous. |
| `Tkinter is missing` ou `No module named '_tkinter'` | Voir « Il vous faut » ci-dessus. |
| `No module named 'model'` ou `'uefa'` | Vous n'êtes pas dans le dossier du projet. Placez-vous dedans avec `cd`, ou utilisez les scripts. |
| `predictor_weights.json not found` | Lancez `python -m model.predictor --train`. |
| « not found in the Elo file, starting at 1500 » | L'application n'a pas trouvé de note pour un club, en général un club que vous avez ajouté vous-même. Voir [`model/docs/names.md`](model/docs/names.md). |
| « no valid draw found in 50 attempts » | Les matchs que vous avez interdits rendent le tirage impossible. Retirez-en quelques-uns. |
| `Failed to load Python DLL` | Vous avez ouvert le `.exe` de `build\`. La vraie application est dans `dist\UEFA-Simulator\`. |
| `PermissionError: [WinError 5] Access is denied` pendant la création | Un fichier de `dist\UEFA-Simulator\` est utilisé. Fermez l'application et toute fenêtre de l'Explorateur ouverte sur ce dossier. Si le projet est dans OneDrive, suspendez la synchronisation, puis recommencez. |

## Créer l'application vous-même

L'application Windows est créée avec [PyInstaller](https://pyinstaller.org). La recette se trouve dans [`UEFA-Simulator.spec`](UEFA-Simulator.spec).

| Système | Commande | Résultat |
|---|---|---|
| Windows | `.\commands\windows\build.ps1` | `dist\UEFA-Simulator-windows.zip` |
| Windows (`py`) | `& ".\commands\python manager\build.ps1"` | `dist\UEFA-Simulator-windows.zip` |
| macOS | `bash commands/MacOs/build.sh` | `dist/UEFA-Simulator-macos.zip` |
| Linux | `bash commands/linux/build.sh` | `dist/UEFA-Simulator-linux.tar.gz` |

Les scripts utilisent le `.venv` s'il existe. L'application elle-même se trouve dans `dist\UEFA-Simulator\` ; le dossier `build\` ne contient que les fichiers de travail de PyInstaller.

Créez l'application sur le système auquel elle est destinée : un `.exe` Windows ne peut pas être créé sous Linux ou macOS. Les scripts macOS et Linux n'ont pas encore été testés.

> [!TIP]
> Si le `.exe` se ferme aussitôt sans message, mettez `console=True` dans `UEFA-Simulator.spec` et recréez l'application : une fenêtre noire affichera l'erreur. Remettez `False` avant de publier.

---

## Organisation du projet

<details>
<summary><b>Afficher les dossiers</b></summary>

```
UEFA-Competitions-Simulator/
├── main.py                 lance l'application
├── UEFA-Simulator.spec     la recette de l'application Windows
├── requirements.txt        les paquets à installer
├── commands/               scripts tout prêts : installer, lancer, créer l'application
├── model/                  le tirage, les notes, le modèle de match et la simulation
│   └── docs/               comment marche chaque partie, en anglais et en français
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
└── GIFs/                   la démonstration ci-dessus
```

</details>

## Documentation

| Où | Ce que vous y trouverez |
|---|---|
| [`model/docs/`](model/docs/README.md) | Le guide du modèle, 12 pages courtes : notes, modèle de match, tirage, journées, noms des clubs, un match, scores, classement, phases finales, prolongation, tirs au but, saisons rejouées. Chacune contient un exemple complet avec de vrais nombres et un petit programme Python à essayer. |
| [`model/docs/code/`](model/docs/code/) | Le code de chaque partie, expliqué quelques lignes à la fois. |
| [`datahandler/`](datahandler/README.md) | D'où viennent les données et comment les télécharger à nouveau. |
| [`templates/`](templates/README.md) | Les fichiers de chapeaux que l'application peut charger et enregistrer. |
| [`interface/`](interface/README.md) | Comment l'interface a été écrite. |
| [Journal des modifications](CHANGELOG.md) | Chaque changement notable, version par version. |

## D'où viennent les données

Toutes les données de matchs viennent d'[API-Football](https://www.api-football.com), avec son plan gratuit : la saison de clubs 2024/25, environ 5 300 matchs (championnats, coupes, matchs européens et amicaux). Le plan gratuit ne donne que les saisons récentes et 100 requêtes par jour ; [`datahandler/`](datahandler/README.md) en dit plus.

## Limites connues

- Les notes viennent d'environ une saison et demie de matchs, donc beaucoup de clubs restent proches de leur note de départ.
- Un résultat ne dépend que des notes des deux clubs : pas de blessures, pas de joueurs, pas de forme récente avant la saison.
- Le score d'un match ne dépend pas de l'écart de force entre les deux clubs.
- Les notes sont considérées comme exactes, donc les chances affichées sont un peu trop sûres d'elles.

La liste complète, avec chaque bug connu, se trouve dans [`model/docs/`](model/docs/README.md#les-bugs-connus-au-m%C3%AAme-endroit).

## Idées pour la suite

- [ ] Une interface plus facile à modifier.
- [ ] Des données d'autres saisons.
- [ ] La vraie règle qui décide qui reçoit au match retour en quarts et en demies (pile ou face pour l'instant).
- [ ] Une barre de « tension » qui montre à quel point un match est serré.
- [ ] Les joueurs, et une simulation en direct.

## Remarques

Vous avez trouvé un bug, ou vous avez une idée ? [Ouvrez une issue](https://github.com/yassinox12834/UEFA-Competitions-Simulator/issues). Si le projet vous a été utile, une ⭐ aide d'autres personnes à le trouver.

## Licence

MIT, voir [LICENSE](LICENSE).
