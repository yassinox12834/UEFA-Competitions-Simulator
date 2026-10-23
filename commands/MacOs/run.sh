#!/usr/bin/env bash
# Launch the app.
#
#   bash commands/MacOs/run.sh
#
# Uses the .venv folder made by req.sh. Without it, uses python3.
cd "$(dirname "$0")/../.."

PY=python3
[ -x .venv/bin/python ] && PY=.venv/bin/python

# Check what the window needs first: a clear message is better than a long error.
if ! "$PY" -c "import tkinter" 2>/dev/null; then
    echo "Tkinter is missing. Install Python from https://www.python.org/downloads/ (it includes Tkinter),"
    echo "or with Homebrew: brew install python-tk"
    exit 1
fi
if ! "$PY" -c "import customtkinter, PIL" 2>/dev/null; then
    echo "The packages are missing. Run this first:  bash commands/MacOs/req.sh"
    exit 1
fi

exec "$PY" main.py
