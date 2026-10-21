"""Root entry point: launches the CustomTkinter app.

    python main.py

Everything lives in interface/main.py; this file only exists so the
project starts from its own folder without remembering a subfolder.
"""

import runpy
from pathlib import Path

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parent / "interface" / "main.py"),
                   run_name="__main__")
