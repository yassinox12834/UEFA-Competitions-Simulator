#!/usr/bin/env bash
# Install the packages. Run it once, then launch the app with run.sh.
#
#   bash commands/MacOs/req.sh
#
# The packages go into a virtual environment, the .venv folder in the project,
# so they never clash with the rest of your computer. The first run creates it.
set -e
cd "$(dirname "$0")/../.."

if [ ! -x .venv/bin/python ]; then
    if ! command -v python3 >/dev/null 2>&1; then
        echo "python3 was not found. Install Python 3.10 or newer from https://www.python.org/downloads/"
        exit 1
    fi
    echo "Creating the virtual environment (.venv)..."
    python3 -m venv .venv
fi

echo "Installing the packages..."
.venv/bin/python -m pip install -r requirements.txt

echo
echo "Done. Launch the app with:  bash commands/MacOs/run.sh"
