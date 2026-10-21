"""
sim_engine.py - the bridge between the simulation screen and model/simulation.py.

Same role as draw_engine.py for the draw, same rules:

  1. The path. The project root is added to sys.path here, once, so that
     "model.simulation" can be found from interface/.
  2. The thread. A single simulation takes a few ms, but a Monte Carlo of
     10 000 tournaments takes several seconds, even on every core: run on
     Tk's thread, the window would freeze. SimJob runs on the side, the
     view checks in with poll(), and reads the progress with progress().
  3. No widget is touched from the worker thread. Ever.

Contents:
    METHODS        the three ways of playing a two-legged tie
    STAGES         the stages counted by the Monte Carlo, in order
    RUN_CHOICES    the numbers of tournaments offered for the Monte Carlo
    resources()    loads the model, the score table and the Elo ratings, once
    SimJob         one simulation (+ Monte Carlo) in the background
    save_log       writes the report and the trace to data/processed/
"""

import sys
import threading
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from model import simulation as sim                          # noqa: E402
from model.knockout import DEFAULT_METHOD, METHODS           # noqa: E402,F401 - re-exported
from model.simulation import STAGES                          # noqa: E402,F401 - re-exported
from model.predictor import PredictorError                   # noqa: E402

from config import MC_RUNS as RUN_CHOICES                     # noqa: E402,F401 - re-exported
DEFAULT_RUNS = 200

_RESOURCES = None


def resources(reload=False):
    """The model, the score table and the Elo ratings: read once, kept.

    Three JSON files, one of them 26 KB: re-reading them on every click on
    "Run" would not be noticeable, but the MatchModel object is also what
    the settings screen displays (training date, log loss), and it must be
    the same one that simulates.
    """
    global _RESOURCES
    if _RESOURCES is None or reload:
        _RESOURCES = sim.Resources()
    return _RESOURCES


class SimJob:
    """
    A complete season, then (optionally) the Monte Carlo, on a separate thread.

    poll() returns None while it is running, ('ok', result, mc) at the end,
    ('error', exc) if something breaks. progress() returns (done, total)
    for the Monte Carlo, (0, 0) before it and during the single season.
    """

    def __init__(self, comp, teams, matchdays, method=DEFAULT_METHOD,
                 expert=True, runs=0, seed=None):
        self.comp = comp
        self.teams = teams
        self.matchdays = matchdays
        self.config = sim.SimConfig(method=method, expert=expert, seed=seed)
        self.runs = int(runs)
        self._result = None
        self._mc = None
        self._error = None
        self._done = False
        self._progress = (0, 0)
        self._cancel = False

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()
        return self

    def cancel(self):
        """The Monte Carlo stops at the end of the tournament in progress."""
        self._cancel = True

    def _run(self):
        try:
            res = resources()
            self._result = sim.simulate(self.comp, self.teams, self.matchdays,
                                        self.config, res)
            if self.runs > 0 and not self._cancel:
                self._mc = sim.monte_carlo(
                    self.comp, self.teams, self.matchdays, self.config,
                    runs=self.runs, resources=res, progress=self._on_progress)
        except BaseException as exc:            # noqa: BLE001 - passed up as it is
            self._error = exc
        finally:
            self._done = True

    def _on_progress(self, done, total):
        self._progress = (done, total)
        if self._cancel:
            # monte_carlo has no stop button: we cut it short with our own
            # exception, caught above.
            raise sim.Cancelled()

    def poll(self):
        if not self._done:
            return None
        if self._error is not None and not isinstance(self._error, sim.Cancelled):
            return ("error", self._error)
        return ("ok", self._result, self._mc)

    def progress(self):
        return self._progress


def save_log(result):
    """Writes sim_<COMP>_<timestamp>.txt and returns its path."""
    return sim.write_log(result)


def error_text(exc):
    """The message to show when the simulation fails."""
    if isinstance(exc, PredictorError):
        return str(exc)
    return f"{type(exc).__name__}: {exc}"
