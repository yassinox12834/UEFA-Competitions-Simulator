#!/usr/bin/env bash
# Build the macOS app, then zip it for a GitHub Release.
#
#   bash commands/MacOs/build.sh
#
# Run bash commands/MacOs/req.sh once before, to make the .venv.
#
# Result:
#   dist/UEFA-Simulator/UEFA-Simulator     the app
#   dist/UEFA-Simulator-macos.zip          the zip to upload
#
# Not tested on a Mac yet.
set -e
cd "$(dirname "$0")/../.."

# PyInstaller must run in the Python that has the app's packages: the .venv
# made by req.sh. The system python3 is not enough, and on recent Debian,
# Ubuntu and Homebrew Python, pip refuses to install into it anyway
# ("externally-managed-environment").
if [ ! -x .venv/bin/python ]; then
    echo "No .venv folder. Run this first:  bash commands/MacOs/req.sh"
    exit 1
fi
PY=.venv/bin/python

# A copy of the app that is still running can leave a half-deleted folder.
pkill -x UEFA-Simulator 2>/dev/null || true

"$PY" -m pip install "pyinstaller>=6"
"$PY" -m PyInstaller --noconfirm UEFA-Simulator.spec

# Count the files of the app, to check the archive holds all of them.
on_disk=$(find dist/UEFA-Simulator -type f | wc -l | tr -d ' ')

# Start from an empty zip: "zip -r" would update an old one and keep files
# that are no longer in the app. ditto is the macOS tool for this; it keeps
# file permissions and links, so the app still opens once unzipped.
ARCHIVE=dist/UEFA-Simulator-macos.zip
rm -f "$ARCHIVE"
if command -v ditto >/dev/null 2>&1; then
    ditto -c -k --keepParent dist/UEFA-Simulator "$ARCHIVE"
else
    (cd dist && zip -qry UEFA-Simulator-macos.zip UEFA-Simulator)
fi

in_archive=$(zipinfo -1 "$ARCHIVE" | grep -cv '/$' || true)
if [ "$in_archive" != "$on_disk" ]; then
    echo "The app is built in dist/UEFA-Simulator/, but the zip is incomplete ($in_archive of $on_disk files)."
    echo "Close any program using that folder (Finder, iCloud or Dropbox syncing), then run:"
    echo "  rm -f $ARCHIVE && ditto -c -k --keepParent dist/UEFA-Simulator $ARCHIVE"
    rm -f "$ARCHIVE"
    exit 1
fi

echo
echo "Done: $ARCHIVE"
