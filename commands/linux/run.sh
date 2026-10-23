#!/usr/bin/env bash
# Launch the app.
#
#   bash commands/linux/run.sh
#
# Uses the .venv folder made by req.sh. Without it, uses python3.
cd "$(dirname "$0")/../.."

PY=python3
[ -x .venv/bin/python ] && PY=.venv/bin/python

# Check what the window needs first: a clear message is better than a long error.
if ! "$PY" -c "import tkinter" 2>/dev/null; then
    echo "Tkinter is missing. On Debian or Ubuntu: sudo apt install python3-tk"
    exit 1
fi
if ! "$PY" -c "import customtkinter, PIL" 2>/dev/null; then
    echo "The packages are missing. Run this first:  bash commands/linux/req.sh"
    exit 1
fi

exec "$PY" main.py
