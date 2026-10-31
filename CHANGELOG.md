# Changelog

All notable changes to this project are documented in this file.

## [1.1.0] 31-10-2026 🎃

A minor release, not a patch: it adds a feature (swapping two clubs between pots) and changes how the model rates matches decided after 90 minutes, so every chance the app shows moves. It also fixes the ten known bugs of 1.0.2 and rebuilds all of the model's data.

### Added

- Swapping two clubs between pots, in "Draw only" mode only, like the replacement. Ctrl + click a club (Cmd + click on macOS), then click a club in another pot, and they change places. A swap is refused when it would leave a pot with too many clubs from one association for any draw to exist (a counting check in `PotsModel.swap_problem`, explained in the code), or when both clubs are in the same pot. Esc cancels a pick. The status line shows the hint and counts the swaps next to the replacements. Files: `interface/draw_engine.py`, `draw_widgets.py`, `views.py`, `config.py`.
- Matches level after 90 minutes now count in the ratings according to how they ended: 0.8 / 0.2 for a win in extra time, 0.7 / 0.3 on penalties (`rating_scores` in `model/elo_score_updating.py`). The simulation uses the same scale when a tie is settled in extra time or on penalties (`_credit_decider` in `model/knockout.py`). A match won in 90 minutes keeps 1 / 0.
- Seven club aliases for the 2025/26 templates in `model/names.py`. Newcastle United, Basel, Mainz, Rijeka, KuPS Kuopio, Rakow and Lausanne-Sport used to start at the default rating of 1500; Newcastle's real rating is about 1740.
- A `timestamp` column in `match_features.csv`. `predictor.train()` sorts by it before it splits the matches into training and test.

### Fixed

- The real ratings used old competition weights: `coef_table.csv` had been built from an older `coefs.json`. `model/categorising.py` could not rebuild it (a tuple it did not unpack, and a category renamed "Domestic League" in one place only). Both are fixed and the CSV is rebuilt from `coefs.json`.
- Friendlies were in the match model's training data (625 played). Every competition whose `comp_mult` is 0 (five of them, 700 fixtures) is now left out of the training rows and of the score table.
- The Elo ratings used scores that included extra time. They now use the 90-minute score, with the scale above for extra time and penalties.
- `model/scorelines.py`: capping at 6 goals happened before the result was decided, so an 8-7 would have become a 6-6 draw. The result is now read first (`cap_scoreline`).
- `model/simulation.py`: with several processes, the Monte Carlo ignored custom ratings, so 1 and 2 processes gave different counts. The processes now receive the same ratings, model and score table. An error inside a season was hidden by a silent restart in one process; now only a process pool that cannot start falls back. The expert log printed "holdout None" with the new model weights. `SimConfig` used Python's shared random generator even when a seed was given.
- `model/names.py`: a misspelt alias failed silently. The alias itself is now searched first, the match is labelled, and the simulation warns.
- `model/league_phase.py`: the log said "alphabetical order" for a perfect tie. The real order is the pot order.
- `model/penalties.py`: the description said the club kicking first wins 50 %. It wins 51.3 %, and each club still wins half of its shoot-outs. `PRESSURE_DROP` now sits at the top of the file, the `MAX_ROUNDS` comment is corrected, and two variables are renamed.
- `model/elo_score_updating.py`: "report only" overwrote `match_features.csv`, and without a `neutral_venue` column the script crashed right after saying it would carry on. The text at the top of the file is up to date.
- `model/matchdays_ucl.py`: a junk line in a docstring and a typo in the error message.
- `datahandler/build_fixtures_csv.py` only looked in the top folder, found nothing, and wrote an empty `fixtures_25.csv` over the real one. It now reads the season sub-folders, keeps one row per match, marks the finals as neutral, refuses to write an empty table, and no longer runs when it is imported. Rebuilt from the raw files, the CSV is identical to the current one. `add_neutral_venue.py` and `drop_duplicate_fixtures.py` used file names nothing else used; they now work on `fixtures_25.csv` in place.
- The READMEs' odds table said "2025/26 pots" but had been computed with the 2024/25 pots (it listed Aston Villa).
- `interface/draw_widgets.py`: every click on a club ran its action twice, because the click was bound on a CustomTkinter label and again on the label inside it. The replace box opened twice, and a swap picked a club and dropped it straight away. The second call is now ignored.
- Removed from the list of bugs: "the app needs pandas". It could not be reproduced: `model.simulation` imports with pandas and scikit-learn blocked, and the Windows build excludes both.

### Changed

- Faster matchdays: the scheduler's step limit is 5,000 instead of 200,000. On 180 draws there was no failure, the slowest schedule went from 8.8 s to 0.37 s, and building the calendars is 3 to 10 times faster in total. The calendar changes for the few draws that needed more steps.
- Faster failure: when the draw search proves that no draw exists (it runs out of options, not of steps), it stops at once with a clear message instead of trying 49 more seeds, about 2.5 s instead of about 2 minutes.
- Rebuilt data: `eeelo_final.json`, `match_features.csv` (4,628 rows, 4,626 played), `scorelines.json` and `predictor_weights.json`. Exam on the newest 40 % of matches: log loss 0.967, against 1.051 for a model that always predicts the average.
- A new odds table in both READMEs, with the real 2025/26 pots. Barcelona and Paris Saint-Germain lead at about 20 % each.
- English interface: the replace box says "Replace" instead of "Swap", so that "swap" now only means the new exchange.
- `model/docs/` and `datahandler/README.md`: every bug section says what was fixed and how. The file name `elo_score_updating_copy.py`, which does not exist, is corrected everywhere.
- The French guides now always address the reader as « vous ».

### Known issues

- The second leg of the quarter-finals and semi-finals is given by a coin toss; since 2025/26, UEFA gives it to the clubs ranked 1 to 4 (1 and 2 in the semi-finals).
- The quarter-final bracket (`QF_BRACKET`) has not been checked against Annex B of the UEFA regulations.
- The default "legs" method sends about 27 % of two-legged ties to penalties, against about 10 % in the real data.
- Hamrun Spartans (2025/26 Conference League template) is not in the match data and starts at 1500.

## [1.0.2] 29-10-2026

Small fix release: two bugs fixed in the model's code, a more reliable Windows build, an unused file removed, and the licence file renamed.

### Fixed

- `model/elo_score_updating.py`: an empty "neutral venue" value was read as "true", so every match was marked as played on neutral ground and the "home" column of the training data was always 0. An empty value now means "not neutral".
- `commands/windows/build.ps1` and `commands/python manager/build.ps1`: the zip step stopped with "being used by another process" when OneDrive or Windows Defender was still reading a file the build had just made. The scripts now wait and try again up to five times, check that the zip holds every file of the app, fall back to Windows' own `tar.exe`, and say what to do if it still fails.
- `commands/MacOs/build.sh` and `commands/linux/build.sh`: without a `.venv`, they installed PyInstaller into the system Python, which recent Debian, Ubuntu and Homebrew Python refuse. They now stop and say to run `req.sh` first. They also close a running copy of the app, start from an empty archive (on macOS, `zip -r` kept files that were no longer in the app), use `ditto` on macOS so the app keeps its permissions, and check that the archive holds every file.
- The `.sh` scripts in the project folder had Windows line endings, so bash stopped at the first line on macOS and Linux. They are back to Unix line endings.
- `model/predictor.py`: the match model's exam was upside down (457 matches to train, 4,794 to test). The matches are now split by date: the oldest 60 % train, the newest 40 % are the exam. The model is still refit on all matches before it is saved.

### Added

- `.gitattributes`: the `.sh` scripts always keep Unix line endings, even when the project is checked out on Windows.

### Changed

- `LICENSE` is renamed `LICENCE`, and the links to it in `README.md` and `README.fr.md` are updated.
- `docs/building.md` and `docs/troubleshooting.md` (and their French versions) explain the new zip step and two build errors: a missing `templates` folder, and a file "being used by another process".
- A "Known bugs in version 1.0.2" section in `README.md` and `README.fr.md`. The two bugs above are removed from the list in `model/docs/README.md`.

### Removed

- `model/coefs.py`, an old script that wrote the competition weights. Nothing imports it; the code reads `data/reference/coefs.json`.

### Known issues

- The two fixes above are in the code only. `data/processed/match_features.csv` and `data/reference/predictor_weights.json` have not been rebuilt, so the app and the odds table still use the old run. Run `model/elo_score_updating.py`, then `model/predictor.py`, to rebuild them.
- Ten older bugs are still open; the list is in the READMEs.

## [1.0.1] 27-10-2026

Small clean-up release: a results table in the READMEs, a tidier `docs/` folder and one unused model file removed.

### Added

- A results table in `README.md` and `README.fr.md`: the title odds of the ten likeliest clubs for the real 2025/26 Champions League pots (one draw, 10,000 replays), with a note on its limits.

### Changed

- The main `README.md` is reorganised, and the guides (installation, terminal commands, troubleshooting, building, project structure) now live in the `docs/` folder.

### Removed

- `model/prepredictator.py`, an older first version of the match model with two inputs. Nothing used it, and its "neutral ground" option did nothing. `model/predictor.py` is the model the app uses. Its mentions in `model/docs/logistic_regression.md` are removed too.
- `model/monte_carlo_more.cpp`, an unused draft (only comments, and nothing included it).

## [1.0.0] 23-10-2026

The first stable version.

### Added

- A Windows app: download it from the Releases page and run it without installing Python. It is built with PyInstaller from `UEFA-Simulator.spec`.
- A `build` script in each folder of `commands/`, to build the app in one command.
- `uefa/paths.py`: one place that knows where the app's files are, both from the source code and from the app.
- Pictures in the `README.md`: a header, "how it works", "how a season works" and a download button, in English and French.

### Changed

- In the app, saved pots and match reports go to `UEFA-Simulator/` in your user folder, because the app folder is not meant to be written to. From the source code, nothing changes.
- The app no longer needs pandas or numpy: they are only loaded when the ratings are rebuilt. This makes the app about 150 MB smaller.
- The `README.md` is rewritten in simpler words, with a download section and a "build the app yourself" section.
- `GHANGELOG.md` is renamed `CHANGELOG.md`.

## [0.9.8] 23-10-2026

### Added

- A new idea in the future improvements: a tension bar, a bar you can set to show how tense a match is.
- A link to this changelog at the top of the `README.md` and in its documentation table.

### Changed

- The project structure tree in the `README.md` is brought up to date, in English and French. It leaves out everything listed in `.gitignore`.

## [0.9.7] 22-10-2026

### Removed

- Removal of some stray C/C++ files. They had been left in the repository by mistake, as they belong to a separate project: I am learning these two languages to get to grips with low-level programming.

### Added

- Setting up a changelog: `CHANGELOG.md` (this document). It tracks all the notable changes made to this project.

## [0.9.6] 21-10-2026

- First official release.

---

# Journal des modifications (version française)

Tous les changements notables de ce projet sont documentés dans ce fichier.

## [1.1.0] 31-10-2026 🎃

Une version mineure, pas un correctif : elle ajoute une fonction (échanger deux clubs de chapeau) et change la façon dont le modèle note les matchs décidés après 90 minutes, donc toutes les chances affichées par l'application bougent. Elle corrige aussi les dix bugs connus de la 1.0.2 et reconstruit toutes les données du modèle.

### Ajouté

- L'échange de deux clubs entre chapeaux, seulement en mode « Tirage seul », comme le remplacement. Ctrl + clic sur un club (Cmd + clic sur macOS), puis clic sur un club d'un autre chapeau : ils échangent leur place. Un échange est refusé s'il laisse dans un chapeau trop de clubs d'une même fédération pour qu'un tirage existe (une vérification par comptage dans `PotsModel.swap_problem`, expliquée dans le code), ou si les deux clubs sont dans le même chapeau. Échap annule un choix. La ligne d'état affiche l'astuce et compte les échanges à côté des remplacements. Fichiers : `interface/draw_engine.py`, `draw_widgets.py`, `views.py`, `config.py`.
- Les matchs à égalité après 90 minutes comptent maintenant dans les notes selon leur fin : 0.8 / 0.2 pour une victoire en prolongation, 0.7 / 0.3 aux tirs au but (`rating_scores` dans `model/elo_score_updating.py`). La simulation utilise la même échelle quand une confrontation se termine en prolongation ou aux tirs au but (`_credit_decider` dans `model/knockout.py`). Un match gagné en 90 minutes garde 1 / 0.
- Sept alias de clubs pour les modèles 2025/26 dans `model/names.py`. Newcastle United, Bâle, Mayence, Rijeka, KuPS Kuopio, Raków et Lausanne-Sport partaient de la note par défaut, 1500 ; la vraie note de Newcastle est d'environ 1740.
- Une colonne `timestamp` dans `match_features.csv`. `predictor.train()` trie selon elle avant de séparer les matchs d'entraînement et d'examen.

### Corrigé

- Les vraies notes utilisaient d'anciens poids de compétition : `coef_table.csv` avait été construit à partir d'un ancien `coefs.json`. `model/categorising.py` ne pouvait pas le reconstruire (un tuple non décompressé, et une catégorie renommée « Domestic League » à un seul endroit). Les deux sont corrigés et le CSV est reconstruit à partir de `coefs.json`.
- Les amicaux étaient dans les données d'entraînement du modèle de match (625 joués). Toute compétition dont le `comp_mult` vaut 0 (cinq, 700 matchs) est maintenant écartée des lignes d'entraînement et de la table des scores.
- Les notes Elo utilisaient des scores qui comprenaient la prolongation. Elles utilisent maintenant le score après 90 minutes, avec l'échelle ci-dessus pour la prolongation et les tirs au but.
- `model/scorelines.py` : le plafond à 6 buts était appliqué avant de décider du résultat, donc un 8-7 serait devenu un nul 6-6. Le résultat est maintenant lu d'abord (`cap_scoreline`).
- `model/simulation.py` : avec plusieurs processus, le Monte Carlo ignorait les notes personnalisées, donc 1 et 2 processus donnaient des comptes différents. Les processus reçoivent maintenant les mêmes notes, le même modèle et la même table des scores. Une erreur dans une saison était cachée par un redémarrage silencieux dans un seul processus ; désormais, seul un groupe de processus qui ne peut pas démarrer bascule. Le journal expert affichait « holdout None » avec les nouveaux poids du modèle. `SimConfig` utilisait le générateur de hasard partagé de Python même quand une graine était donnée.
- `model/names.py` : un alias mal écrit échouait en silence. L'alias lui-même est maintenant cherché en premier, la correspondance est étiquetée et la simulation prévient.
- `model/league_phase.py` : le journal disait « ordre alphabétique » pour une égalité parfaite. Le vrai ordre est celui des chapeaux.
- `model/penalties.py` : la description disait que le club qui tire en premier gagne 50 %. Il gagne 51,3 %, et chaque club gagne toujours la moitié de ses séances. `PRESSURE_DROP` est maintenant en haut du fichier, le commentaire de `MAX_ROUNDS` est corrigé et deux variables sont renommées.
- `model/elo_score_updating.py` : « rapport seulement » écrasait `match_features.csv`, et sans colonne `neutral_venue` le script plantait juste après avoir annoncé qu'il continuait. Le texte en haut du fichier est à jour.
- `model/matchdays_ucl.py` : une ligne parasite dans une docstring et une faute dans le message d'erreur.
- `datahandler/build_fixtures_csv.py` ne regardait que le dossier du haut, ne trouvait rien et écrivait un `fixtures_25.csv` vide par-dessus le vrai. Il lit maintenant les sous-dossiers de saison, garde une ligne par match, marque les finales comme neutres, refuse d'écrire un tableau vide et ne s'exécute plus quand on l'importe. Reconstruit à partir des fichiers bruts, le CSV est identique à l'actuel. `add_neutral_venue.py` et `drop_duplicate_fixtures.py` utilisaient des noms de fichiers que rien d'autre n'utilisait ; ils travaillent maintenant sur place, sur `fixtures_25.csv`.
- Le tableau des chances des README disait « chapeaux 2025/26 » mais avait été calculé avec les chapeaux 2024/25 (il contenait Aston Villa).
- `interface/draw_widgets.py` : chaque clic sur un club lançait son action deux fois, parce que le clic était lié à une étiquette CustomTkinter et encore à l'étiquette qu'elle contient. La fenêtre de remplacement s'ouvrait deux fois, et un échange choisissait un club puis l'abandonnait aussitôt. Le second appel est maintenant ignoré.
- Retiré de la liste des bugs : « l'appli a besoin de pandas ». Il n'a pas pu être reproduit : `model.simulation` s'importe avec pandas et scikit-learn bloqués, et la version Windows les exclut tous les deux.

### Changé

- Des journées plus rapides : la limite de pas du planificateur vaut 5 000 au lieu de 200 000. Sur 180 tirages, aucun échec, le calendrier le plus lent est passé de 8,8 s à 0,37 s, et la construction des calendriers est de 3 à 10 fois plus rapide au total. Le calendrier change pour les quelques tirages qui avaient besoin de plus de pas.
- Un échec plus rapide : quand la recherche du tirage prouve qu'aucun tirage n'existe (elle manque d'options, pas de pas), elle s'arrête tout de suite avec un message clair au lieu d'essayer 49 autres graines, environ 2,5 s au lieu d'environ 2 minutes.
- Données reconstruites : `eeelo_final.json`, `match_features.csv` (4 628 lignes, 4 626 jouées), `scorelines.json` et `predictor_weights.json`. Examen sur les 40 % de matchs les plus récents : perte logarithmique de 0,967, contre 1,051 pour un modèle qui prédit toujours la moyenne.
- Un nouveau tableau des chances dans les deux README, avec les vrais chapeaux 2025/26. Barcelone et le Paris Saint-Germain sont en tête, à environ 20 % chacun.
- Interface en anglais : la fenêtre de remplacement dit « Replace » au lieu de « Swap », pour que « swap » ne désigne plus que le nouvel échange.
- `model/docs/` et `datahandler/README.md` : chaque partie sur les bugs dit ce qui a été corrigé et comment. Le nom de fichier `elo_score_updating_copy.py`, qui n'existe pas, est corrigé partout.
- Les guides en français vouvoient maintenant toujours le lecteur.

### Problèmes connus

- Le match retour des quarts et des demies est attribué à pile ou face ; depuis 2025/26, l'UEFA le donne aux clubs classés 1 à 4 (1 et 2 en demies).
- Le tableau des quarts (`QF_BRACKET`) n'a pas été vérifié avec l'annexe B du règlement de l'UEFA.
- La méthode par défaut « legs » envoie environ 27 % des confrontations aller-retour aux tirs au but, contre environ 10 % dans les vraies données.
- Hamrun Spartans (modèle 2025/26 de la Ligue Conférence) n'est pas dans les données de matchs et part de 1500.

## [1.0.2] 29-10-2026

Petite version de correction : deux bugs corrigés dans le code du modèle, une création de l'application Windows plus fiable, un fichier inutilisé retiré, et le fichier de licence renommé.

### Corrigé

- `model/elo_score_updating.py` : une valeur vide dans « terrain neutre » était lue comme « vrai », donc tous les matchs étaient marqués comme joués sur terrain neutre et la colonne « domicile » des données d'entraînement valait toujours 0. Une valeur vide veut maintenant dire « pas neutre ».
- `commands/windows/build.ps1` et `commands/python manager/build.ps1` : l'étape du zip s'arrêtait avec « being used by another process » quand OneDrive ou Windows Defender lisait encore un fichier que la création venait de faire. Les scripts attendent maintenant et réessaient jusqu'à cinq fois, vérifient que le zip contient tous les fichiers de l'application, se rabattent sur le `tar.exe` de Windows, et expliquent quoi faire si cela échoue encore.
- `commands/MacOs/build.sh` et `commands/linux/build.sh` : sans `.venv`, ils installaient PyInstaller dans le Python du système, ce que refusent les versions récentes de Debian, d'Ubuntu et le Python de Homebrew. Ils s'arrêtent maintenant en disant de lancer `req.sh` d'abord. Ils ferment aussi une copie de l'application encore ouverte, partent d'une archive vide (sous macOS, `zip -r` gardait des fichiers qui n'étaient plus dans l'application), utilisent `ditto` sous macOS pour que l'application garde ses permissions, et vérifient que l'archive contient tous les fichiers.
- Les scripts `.sh` du dossier du projet avaient des fins de ligne Windows, donc bash s'arrêtait dès la première ligne sous macOS et Linux. Ils ont retrouvé des fins de ligne Unix.
- `model/predictor.py` : l'examen du modèle de match était à l'envers (457 matchs pour s'entraîner, 4 794 pour l'examen). Les matchs sont maintenant découpés par date : les 60 % les plus anciens servent à s'entraîner, les 40 % les plus récents sont l'examen. Le modèle est toujours ré-entraîné sur tous les matchs avant d'être enregistré.

### Ajouté

- `.gitattributes` : les scripts `.sh` gardent toujours des fins de ligne Unix, même quand le projet est récupéré sous Windows.

### Modifié

- `LICENSE` devient `LICENCE`, et les liens vers ce fichier dans `README.md` et `README.fr.md` sont mis à jour.
- `docs/building.md` et `docs/troubleshooting.md` (et leurs versions françaises) expliquent la nouvelle étape du zip et deux erreurs de création : un dossier `templates` absent, et un fichier « being used by another process ».
- Une partie « Bugs connus de la version 1.0.2 » dans `README.md` et `README.fr.md`. Les deux bugs ci-dessus sont retirés de la liste de `model/docs/README.md`.

### Supprimé

- `model/coefs.py`, un ancien script qui écrivait les poids des compétitions. Rien ne l'importe ; le code lit `data/reference/coefs.json`.

### Problèmes connus

- Les deux corrections ci-dessus sont seulement dans le code. `data/processed/match_features.csv` et `data/reference/predictor_weights.json` n'ont pas été recalculés, donc l'application et le tableau des chances utilisent encore l'ancien calcul. Lancez `model/elo_score_updating.py`, puis `model/predictor.py`, pour les recalculer.
- Dix bugs plus anciens sont encore ouverts ; la liste est dans les README.

## [1.0.1] 27-10-2026

Petite version de nettoyage : un tableau de résultats dans les README, un dossier `docs/` mieux rangé et un fichier du modèle inutilisé retiré.

### Ajouté

- Un tableau de résultats dans `README.md` et `README.fr.md` : les chances de titre des dix clubs les plus probables avec les vrais chapeaux 2025/26 de la Ligue des champions (un tirage, 10 000 rejeux), avec une note sur ses limites.

### Modifié

- Le `README.md` principal est réorganisé, et les guides (installation, commandes du terminal, dépannage, création de l'application, structure du projet) sont maintenant dans le dossier `docs/`.

### Supprimé

- `model/prepredictator.py`, une ancienne première version du modèle de match à deux entrées. Rien ne l'utilisait, et son option « terrain neutre » ne faisait rien. `model/predictor.py` est le modèle utilisé par l'appli. Ses mentions dans `model/docs/logistic_regression.md` sont aussi retirées.
- `model/monte_carlo_more.cpp`, un brouillon inutilisé (seulement des commentaires, et rien ne l'incluait).


## [1.0.0] 23-10-2026

La première version stable.

### Ajouté

- Une application Windows : téléchargez-la depuis la page Releases et lancez-la sans installer Python. Elle est créée avec PyInstaller à partir de `UEFA-Simulator.spec`.
- Un script `build` dans chaque dossier de `commands/`, pour créer l'application en une commande.
- `uefa/paths.py` : un seul endroit qui sait où se trouvent les fichiers, depuis le code source comme depuis l'application.
- Des images dans le `README.md` : un en-tête, « comment ça marche », « comment se déroule une saison » et un bouton de téléchargement, en anglais et en français.

### Modifié

- Dans l'application, les chapeaux enregistrés et les comptes rendus de matchs vont dans `UEFA-Simulator/`, dans votre dossier utilisateur, car le dossier de l'application n'est pas fait pour qu'on y écrive. Depuis le code source, rien ne change.
- L'application n'a plus besoin de pandas ni de numpy : ils ne sont chargés que pour recalculer les notes. L'application est ainsi environ 150 Mo plus légère.
- Le `README.md` est réécrit avec des mots plus simples, avec une partie téléchargement et une partie « créer l'application vous-même ».
- `GHANGELOG.md` devient `CHANGELOG.md`.

## [0.9.8] 23-10-2026

### Ajouté

- Une nouvelle idée dans les améliorations en vue : une barre de tension, une barre que l'on peut régler pour indiquer à quel point un match est tendu.
- Un lien vers ce journal des modifications en haut du `README.md` et dans son tableau de documentation.

### Modifié

- L'arborescence du projet dans le `README.md` est mise à jour, en anglais et en français. Elle laisse de côté tout ce qui figure dans `.gitignore`.

## [0.9.7] 22-10-2026

### Supprimé

- Suppression de quelques fichiers C/C++ oubliés dans le dépôt par erreur : ils appartiennent à un autre projet, car j'apprends ces deux langages pour me familiariser avec la programmation bas niveau.

### Ajouté

- Mise en place d'un journal des modifications : `CHANGELOG.md` (ce document). Il suit tous les changements notables apportés à ce projet.

## [0.9.6] 21-10-2026

- Première version officielle.