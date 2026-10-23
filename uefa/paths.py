"""Where the project's files live, from source or from the .exe."""

import sys
from pathlib import Path

FROZEN = getattr(sys, "frozen", False)

# Read-only files shipped with the app: data/, assets/, templates/.
# From source: the project root. From the .exe: sys._MEIPASS.
RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))

# Files the user creates: saved templates, simulation logs.
# From source: the project root, exactly as before.
# From the .exe: a user folder, because the app folder is not for writing.
USER_DIR = (Path.home() / "UEFA-Simulator") if FROZEN else RESOURCE_DIR