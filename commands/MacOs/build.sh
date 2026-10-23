#!/usr/bin/env bash
# Build the macOS app, then zip it for a GitHub Release.
#
#   bash commands/MacOs/build.sh
#
# Result:
#   dist/UEFA-Simulator/UEFA-Simulator     the app
#   dist/UEFA-Simulator-macos.zip          the zip to upload
#
# Not tested on a Mac yet.
set -e
cd "$(dirname "$0")/../.."

PY=python3
[ -x .venv/bin/python ] && PY=.venv/bin/python

"$PY" -m pip install "pyinstaller>=6"
"$PY" -m PyInstaller --noconfirm UEFA-Simulator.spec
(cd dist && zip -qr UEFA-Simulator-macos.zip UEFA-Simulator)

echo
echo "Done: dist/UEFA-Simulator-macos.zip"
