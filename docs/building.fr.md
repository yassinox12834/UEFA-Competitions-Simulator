<sub>[← README](../README.fr.md) · [Installation](installation.fr.md) · [Terminal](terminal.fr.md) · [Problèmes](troubleshooting.fr.md) · **Créer l'application** · [Organisation](project-structure.fr.md) · [🇬🇧 English](building.md)</sub>

# Créer l'application vous-même

L'application Windows est créée avec [PyInstaller](https://pyinstaller.org). La recette se trouve dans [`UEFA-Simulator.spec`](../UEFA-Simulator.spec).

## Les commandes

Lancez-les depuis le dossier du projet, après avoir [installé les paquets](installation.fr.md).

| Système | Commande | Résultat |
|---|---|---|
| Windows | `.\commands\windows\build.ps1` | `dist\UEFA-Simulator-windows.zip` |
| Windows (`py`) | `& ".\commands\python manager\build.ps1"` | `dist\UEFA-Simulator-windows.zip` |
| macOS | `bash commands/MacOs/build.sh` | `dist/UEFA-Simulator-macos.zip` |
| Linux | `bash commands/linux/build.sh` | `dist/UEFA-Simulator-linux.tar.gz` |

Sous Windows, les scripts utilisent le `.venv` s'il existe. Sous macOS et Linux, ils en ont besoin : lancez `req.sh` une fois avant (voir [l'installation](installation.fr.md)), car les systèmes récents refusent d'installer PyInstaller dans le Python du système. L'application elle-même se trouve dans `dist\UEFA-Simulator\` ; le dossier `build\` ne contient que les fichiers de travail de PyInstaller.

Sous Windows, le zip est fait en dernier. Si OneDrive ou Windows Defender lit encore un nouveau fichier, le script attend et réessaie jusqu'à cinq fois, puis utilise le `tar.exe` de Windows. Il vérifie aussi que le zip contient tous les fichiers de l'application. Les scripts macOS et Linux partent d'une archive vide et font la même vérification.

## Un système à la fois

Créez l'application sur le système auquel elle est destinée : un `.exe` Windows ne peut pas être créé sous Linux ou macOS. Les scripts macOS et Linux n'ont pas encore été testés.

## En cas d'échec

> [!TIP]
> Si le `.exe` se ferme aussitôt sans message, mettez `console=True` dans `UEFA-Simulator.spec` et recréez l'application : une fenêtre noire affichera l'erreur. Remettez `False` avant de publier.

Les autres erreurs de création (`Failed to load Python DLL`, `Access is denied`, `Unable to find`, `being used by another process`) sont dans [en cas de problème](troubleshooting.fr.md#création-de-lapplication).
