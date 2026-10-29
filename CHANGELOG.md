# Changelog

All notable changes to this project are documented in this file.

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