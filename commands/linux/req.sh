#!/usr/bin/env bash
# Install the packages. Run it once, then launch the app with run.sh.
#
#   bash commands/linux/req.sh
#
# The packages go into a virtual environment, the .venv folder in the project,
# so they never clash with the rest of your computer. The first run creates it.
set -e
cd "$(dirname "$0")/../.."

if [ ! -x .venv/bin/python ]; then
    if ! command -v python3 >/dev/null 2>&1; then
        echo "python3 was not found. Install Python 3.10 or newer, then try again."
        exit 1
    fi
    echo "Creating the virtual environment (.venv)..."
    if ! python3 -m venv .venv; then
        echo "Could not create .venv. On Debian or Ubuntu: sudo apt install python3-venv python3-tk"
        echo "Then delete the half-made .venv folder and run this script again."
        exit 1
    fi
fi

echo "Installing the packages..."
.venv/bin/python -m pip install -r requirements.txt

echo
echo "Done. Launch the app with:  bash commands/linux/run.sh"
