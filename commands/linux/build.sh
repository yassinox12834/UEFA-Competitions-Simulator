#!/usr/bin/env bash
# Build the Linux app, then pack it for a GitHub Release.
#
#   bash commands/linux/build.sh
#
# Run bash commands/linux/req.sh once before, to make the .venv.
#
# Result:
#   dist/UEFA-Simulator/UEFA-Simulator     the app
#   dist/UEFA-Simulator-linux.tar.gz       the archive to upload
#
# Not tested on Linux yet.
set -e
cd "$(dirname "$0")/../.."

# PyInstaller must run in the Python that has the app's packages: the .venv
# made by req.sh. The system python3 is not enough, and on recent Debian,
# Ubuntu and Homebrew Python, pip refuses to install into it anyway
# ("externally-managed-environment").
if [ ! -x .venv/bin/python ]; then
    echo "No .venv folder. Run this first:  bash commands/linux/req.sh"
    exit 1
fi
PY=.venv/bin/python

# A copy of the app that is still running can leave a half-deleted folder.
pkill -x UEFA-Simulator 2>/dev/null || true

"$PY" -m pip install "pyinstaller>=6"
"$PY" -m PyInstaller --noconfirm UEFA-Simulator.spec

# Count the files of the app, to check the archive holds all of them.
on_disk=$(find dist/UEFA-Simulator -type f | wc -l | tr -d ' ')

ARCHIVE=dist/UEFA-Simulator-linux.tar.gz
rm -f "$ARCHIVE"
tar -czf "$ARCHIVE" -C dist UEFA-Simulator

in_archive=$(tar -tzf "$ARCHIVE" | grep -cv '/$' || true)
if [ "$in_archive" != "$on_disk" ]; then
    echo "The app is built in dist/UEFA-Simulator/, but the archive is incomplete ($in_archive of $on_disk files)."
    echo "Close any program using that folder, then run:"
    echo "  tar -czf $ARCHIVE -C dist UEFA-Simulator"
    rm -f "$ARCHIVE"
    exit 1
fi

echo
echo "Done: $ARCHIVE"
