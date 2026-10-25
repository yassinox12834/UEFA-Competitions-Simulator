<sub>[← README](../README.md) · [Installation](installation.md) · **Terminal** · [Troubleshooting](troubleshooting.md) · [Building](building.md) · [Structure](project-structure.md) · [🇫🇷 Français](terminal.fr.md)</sub>

# Terminal commands

The simulation also runs without the window. Every command runs from the project folder, the one that contains `main.py`.

## Before you start

The packages must be installed first (see [installation](installation.md)). Then either activate the `.venv`:

```bash
.venv\Scripts\Activate.ps1       # Windows
source .venv/bin/activate        # macOS or Linux
```

or replace `python` in the commands below with `.venv\Scripts\python` on Windows and `.venv/bin/python` on macOS and Linux.

## A full season

Each command makes a draw, plays one season with the full match report, replays it 100 times, and prints the ten clubs most likely to win:

```bash
python -m model.simulation UCL     # Champions League
python -m model.simulation UEL     # Europa League
python -m model.simulation UECL    # Conference League
```

## One part at a time

| Command | What it does |
|---|---|
| `python -m model.draw_ucl` | one Champions League and one Europa League draw, printed pot by pot |
| `python -m model.draw_uecl` | one Conference League draw |
| `python -m model.matchdays_ucl` | a draw split into 8 matchdays |
| `python -m model.predictor` | the chances of home win, draw and away win for a few rating gaps |
| `python -m model.predictor --train` | trains the match model again (needs `scikit-learn`) |
| `python -m model.elo_score_updating --write` | rebuilds every club's rating from the real matches (needs `pandas`) |
| `python -m model.scorelines` | rebuilds the table of real scores (needs `pandas`) |

How each part works is explained in [`model/docs/`](../model/docs/README.md).
