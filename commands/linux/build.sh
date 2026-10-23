#!/usr/bin/env bash
# Build the Linux app, then pack it for a GitHub Release.
#
#   bash commands/linux/build.sh
#
# Result:
#   dist/UEFA-Simulator/UEFA-Simulator     the app
#   dist/UEFA-Simulator-linux.tar.gz       the archive to upload
set -e
cd "$(dirname "$0")/../.."

PY=python3
[ -x .venv/bin/python ] && PY=.venv/bin/python

"$PY" -m pip install "pyinstaller>=6"
"$PY" -m PyInstaller --noconfirm UEFA-Simulator.spec
tar -czf dist/UEFA-Simulator-linux.tar.gz -C dist UEFA-Simulator

echo
echo "Done: dist/UEFA-Simulator-linux.tar.gz"
