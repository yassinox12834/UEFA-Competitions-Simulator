<sub>[← README](../README.md) · [Installation](installation.md) · [Terminal](terminal.md) · [Troubleshooting](troubleshooting.md) · [Building](building.md) · **Structure** · [🇫🇷 Français](project-structure.fr.md)</sub>

# Project structure

```
UEFA-Competitions-Simulator/
├── main.py                 starts the app
├── UEFA-Simulator.spec     the recipe for the Windows app
├── requirements.txt        the packages to install
├── docs/                   these guides: installation, terminal, troubleshooting, building
├── commands/               ready-made scripts: install, launch, build
├── model/                  the draw, the ratings, the match model and the simulation
│   └── docs/               how each part works, in English and French
├── interface/              the window and its screens
├── uefa/                   where every file is (paths) and the project settings
├── datahandler/            downloads and cleans the data from API-Football
├── data/
│   ├── raw/                data as downloaded
│   ├── processed/          cleaned data: matches, ratings, match reports
│   └── reference/          settings: coefficients, starting ratings, model numbers
├── templates/              sets of pots the app can load and save
├── assets/images/          club badges, competition logos, flags, README pictures
├── scripts/                small one-off tools
└── GIFs/                   the animations shown in the README
```

## Where to go next

| Folder | Its own guide |
|---|---|
| `model/` | [`model/docs/`](../model/docs/README.md) |
| `interface/` | [`interface/README.md`](../interface/README.md) |
| `datahandler/` | [`datahandler/README.md`](../datahandler/README.md) |
| `templates/` | [`templates/README.md`](../templates/README.md) |
