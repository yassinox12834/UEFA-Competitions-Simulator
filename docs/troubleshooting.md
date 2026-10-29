<sub>[← README](../README.md) · [Installation](installation.md) · [Terminal](terminal.md) · **Troubleshooting** · [Building](building.md) · [Structure](project-structure.md) · [🇫🇷 Français](troubleshooting.fr.md)</sub>

# Troubleshooting

Find the message you see in the left column.

## Installing and launching

| Message | What to do |
|---|---|
| `running scripts is disabled on this system` | Type `Set-ExecutionPolicy -Scope Process RemoteSigned` in that PowerShell window, then try again. |
| `Python was not found` | Install Python from [python.org](https://www.python.org/downloads/) and tick **Add python.exe to PATH** in the installer. |
| `Python 3.12 is not installed on this computer` | You use the `python manager` scripts: put one of your versions in [`version.ps1`](../commands/python%20manager/version.ps1). |
| `The packages are missing` | Run the `req` script for your system first. |
| `No module named 'customtkinter'` | Same cause: the packages are not installed for the Python you are using. Run the `req` script, or activate the `.venv` before `python main.py`. |
| `externally-managed-environment` | Your Linux or Homebrew Python refuses `pip install` outside a virtual environment. Use `req.sh`, which makes one for you. |
| `Tkinter is missing` or `No module named '_tkinter'` | See [What you need](installation.md#what-you-need). |
| `No module named 'model'` or `'uefa'` | You are not in the project folder. Use `cd` to go there, or use the scripts. |

## While the app runs

| Message | What to do |
|---|---|
| `predictor_weights.json not found` | Run `python -m model.predictor --train`. |
| "not found in the Elo file, starting at 1500" | The app could not find a rating for a club, usually one you added yourself. See [`model/docs/names.md`](../model/docs/names.md). |
| "no valid draw found in 50 attempts" | The matches you banned make the draw impossible. Remove some of them. |

## Building the app

| Message | What to do |
|---|---|
| `Failed to load Python DLL` | You opened the `.exe` in `build\`. The real app is in `dist\UEFA-Simulator\`. |
| `PermissionError: [WinError 5] Access is denied` | A file in `dist\UEFA-Simulator\` is in use. Close the app and any Explorer window on that folder. If the project is in OneDrive, pause syncing, then build again. |
| `Unable to find '...\templates\2025_2026' when adding binary and data files` | A folder that `UEFA-Simulator.spec` puts inside the app is missing. Get it back with `git checkout -- templates`, then build again. |
| `The process cannot access the file '...\base_library.zip' because it is being used by another process` | The app is built; only the zip failed, because OneDrive or Windows Defender was still reading a new file. Since 1.0.2 the build scripts wait and try again. If it still fails, pause OneDrive syncing and run `tar.exe -a -c -f dist\UEFA-Simulator-windows.zip -C dist UEFA-Simulator`. |
| `$'\r': command not found` or `set: -: invalid option` (macOS, Linux) | The `.sh` scripts have Windows line endings, usually because the project was copied from a Windows computer. Run `perl -pi -e 's/\r$//' commands/*/*.sh`, then try again. A fresh `git clone` does not have this problem. |
| `No .venv folder` (macOS, Linux) | Run `bash commands/MacOs/req.sh` or `bash commands/linux/req.sh` first, then build again. |
| The `.exe` closes at once without a message | See the tip at the end of [building the app](building.md). |

Not in the list? [Open an issue](https://github.com/yassinox12834/UEFA-Competitions-Simulator/issues) with the full message.
