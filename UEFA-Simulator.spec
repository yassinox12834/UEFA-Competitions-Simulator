# -*- mode: python ; coding: utf-8 -*-
#
# Build the app with:   pyinstaller --noconfirm UEFA-Simulator.spec
# (or run the build script in commands/, which does exactly that)
#
# Every path below is relative to this file, so the same spec works on
# Windows, macOS and Linux. Run PyInstaller on the system you build for:
# a Windows .exe cannot be built from Linux.

import os

# PyInstaller already provides these names when it runs this file. Importing
# them anyway changes nothing for the build, and tells the code editor where
# they come from, so it stops underlining them as errors.
from PyInstaller.building.api import COLLECT, EXE, PYZ
from PyInstaller.building.build_main import Analysis
from PyInstaller.utils.hooks import collect_data_files

# The folder of this file. PyInstaller provides it as SPECPATH; reading it
# through globals() keeps the editor quiet too.
SPEC_DIR = globals().get("SPECPATH", os.getcwd())

APP_NAME = "UEFA-Simulator"

# CustomTkinter keeps its themes and its Roboto font as data files.
datas = collect_data_files("customtkinter")

# What the app reads while it runs. Same layout as the project, because
# the code finds these files with paths built from the project root.
# NEVER add .env here: it holds your API key.
datas += [
    ("assets/images/clubs",   "assets/images/clubs"),
    ("assets/images/compets", "assets/images/compets"),
    ("assets/images/flags",   "assets/images/flags"),
    ("templates/2025_2026",   "templates/2025_2026"),
    ("templates/2026_2027",   "templates/2026_2027"),
    ("data/reference",        "data/reference"),
    ("data/processed/countries_filled_25.csv", "data/processed"),
    ("data/processed/eeelo_final.json",        "data/processed"),
]

# Optional: put an app.ico in assets/images/ and it becomes the icon of the .exe.
icon = os.path.join(SPEC_DIR, "assets", "images", "app.ico")

a = Analysis(
    # Not the root main.py: it starts the app with runpy, and PyInstaller
    # cannot follow that to find the modules the app imports.
    ["interface/main.py"],
    # interface/ is not a package (its files import each other by plain
    # name), and the project root makes uefa and model importable.
    pathex=[os.path.join(SPEC_DIR, "interface"), SPEC_DIR],
    datas=datas,
    # The app never needs these, but some modules import them inside a
    # function, which PyInstaller would follow and bundle (about 150 MB).
    excludes=["pandas", "numpy", "sklearn", "scipy", "matplotlib",
              "dotenv", "requests"],
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    console=False,                       # no black console window
    icon=icon if os.path.exists(icon) else None,
)

# One folder (not one file): starts faster, fewer antivirus false alarms.
coll = COLLECT(exe, a.binaries, a.datas, name=APP_NAME)
