<sub>[← README](../README.fr.md) · [Installation](installation.fr.md) · [Terminal](terminal.fr.md) · **Problèmes** · [Créer l'application](building.fr.md) · [Organisation](project-structure.fr.md) · [🇬🇧 English](troubleshooting.md)</sub>

# En cas de problème

Cherchez le message affiché dans la colonne de gauche. Les messages restent en anglais, car c'est ainsi qu'ils apparaissent à l'écran.

## Installation et lancement

| Message | Que faire |
|---|---|
| `running scripts is disabled on this system` | Tapez `Set-ExecutionPolicy -Scope Process RemoteSigned` dans cette fenêtre PowerShell, puis réessayez. |
| `Python was not found` | Installez Python depuis [python.org](https://www.python.org/downloads/) et cochez **Add python.exe to PATH** dans l'installateur. |
| `Python 3.12 is not installed on this computer` | Vous utilisez les scripts `python manager` : mettez l'une de vos versions dans [`version.ps1`](../commands/python%20manager/version.ps1). |
| `The packages are missing` | Lancez d'abord le script `req` de votre système. |
| `No module named 'customtkinter'` | Même cause : les paquets ne sont pas installés pour le Python que vous utilisez. Lancez le script `req`, ou activez le `.venv` avant `python main.py`. |
| `externally-managed-environment` | Votre Python Linux ou Homebrew refuse `pip install` hors d'un environnement virtuel. Utilisez `req.sh`, qui en crée un pour vous. |
| `Tkinter is missing` ou `No module named '_tkinter'` | Voir [Ce qu'il vous faut](installation.fr.md#ce-quil-vous-faut). |
| `No module named 'model'` ou `'uefa'` | Vous n'êtes pas dans le dossier du projet. Placez-vous dedans avec `cd`, ou utilisez les scripts. |

## Pendant que l'application tourne

| Message | Que faire |
|---|---|
| `predictor_weights.json not found` | Lancez `python -m model.predictor --train`. |
| « not found in the Elo file, starting at 1500 » | L'application n'a pas trouvé de note pour un club, en général un club que vous avez ajouté vous-même. Voir [`model/docs/names.md`](../model/docs/names.md). |
| « no valid draw found in 50 attempts » | Les matchs que vous avez interdits rendent le tirage impossible. Retirez-en quelques-uns. |

## Création de l'application

| Message | Que faire |
|---|---|
| `Failed to load Python DLL` | Vous avez ouvert le `.exe` de `build\`. La vraie application se trouve dans `dist\UEFA-Simulator\`. |
| `PermissionError: [WinError 5] Access is denied` | Un fichier de `dist\UEFA-Simulator\` est utilisé. Fermez l'application et toute fenêtre de l'Explorateur ouverte sur ce dossier. Si le projet est dans OneDrive, suspendez la synchronisation, puis recommencez. |
| Le `.exe` se ferme aussitôt sans message | Voir le conseil à la fin de [créer l'application](building.fr.md). |

Votre problème n'est pas dans la liste ? [Ouvrez un ticket](https://github.com/yassinox12834/UEFA-Competitions-Simulator/issues) avec le message complet.
