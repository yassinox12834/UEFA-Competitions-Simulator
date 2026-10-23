# Changelog

All notable changes to this project are documented in this file.

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