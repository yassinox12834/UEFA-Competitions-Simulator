<sub>[← README](../README.md) · [Installation](installation.md) · [Terminal](terminal.md) · [Troubleshooting](troubleshooting.md) · **Building** · [Structure](project-structure.md) · [🇫🇷 Français](building.fr.md)</sub>

# Building the app yourself

The Windows app is made with [PyInstaller](https://pyinstaller.org). The recipe is in [`UEFA-Simulator.spec`](../UEFA-Simulator.spec).

## The commands

Run them from the project folder, after [installing the packages](installation.md).

| System | Build command | Result |
|---|---|---|
| Windows | `.\commands\windows\build.ps1` | `dist\UEFA-Simulator-windows.zip` |
| Windows (`py`) | `& ".\commands\python manager\build.ps1"` | `dist\UEFA-Simulator-windows.zip` |
| macOS | `bash commands/MacOs/build.sh` | `dist/UEFA-Simulator-macos.zip` |
| Linux | `bash commands/linux/build.sh` | `dist/UEFA-Simulator-linux.tar.gz` |

On Windows, the scripts use the `.venv` if there is one. On macOS and Linux they need it: run `req.sh` once before (see [installation](installation.md)), because recent systems refuse to install PyInstaller into the system Python. The app itself is in `dist\UEFA-Simulator\`; the `build\` folder only holds PyInstaller's working files.

On Windows, the zip is made last. If OneDrive or Windows Defender is still reading a new file, the script waits and tries again up to five times, then uses Windows' own `tar.exe`. It also checks that the zip holds every file of the app. The macOS and Linux scripts start from an empty archive and make the same check.

## One system at a time

Build on the system you want the app for: a Windows `.exe` cannot be made on Linux or macOS. The macOS and Linux scripts have not been tested yet.

## If it fails

> [!TIP]
> If the `.exe` closes at once without a message, set `console=True` in `UEFA-Simulator.spec` and build again: a black window will show the error. Set it back to `False` before you publish.

Other build errors (`Failed to load Python DLL`, `Access is denied`, `Unable to find`, `being used by another process`) are in [troubleshooting](troubleshooting.md#building-the-app).
