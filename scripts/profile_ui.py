"""Drives the interface through a full journey and times every step.

Usage, from the project root:
    python scripts/profile_ui.py                 # full simulation journey
    python scripts/profile_ui.py . draw          # draw-only journey
    PROF_STEP="theme" python scripts/profile_ui.py   # cProfile one step
(On Linux without a screen: xvfb-run -a python scripts/profile_ui.py)

Columns:
    ready    ms until the step is usable (includes the 300 ms slide)
    anim     animation frames played during the step
    tickmed  median cost of one animation frame, ms (budget: 16 ms)
    maxcb    longest single Tk callback, ms: the longest time a click or
             a key press could be ignored. Above ~100 ms it feels laggy.
    maxgap   longest single event of the event loop, ms: a callback, or one
             batch of the redraws and layout Tk does when idle. What the eye
             sees as a stutter, and how long a click may wait.
    widgets  widgets alive in the window after the step
"""
import os, sys, time, statistics
from pathlib import Path

repo = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]).resolve()
sys.path.insert(0, str(repo))
sys.path.insert(0, str(repo / "interface"))

import platform_utils  # noqa
import transition as tr
from main import build_app

FRAMES = []
import tkinter
CB = {"max": 0.0}
_orig_cw = tkinter.CallWrapper.__call__


def _timed_cw(self, *args):
    t = time.perf_counter()
    try:
        return _orig_cw(self, *args)
    finally:
        ms = (time.perf_counter() - t) * 1000
        if ms > CB["max"]:
            CB["max"] = ms
            f = getattr(self.func, "__func__", self.func)
            CB["who"] = getattr(f, "__qualname__", repr(f))


tkinter.CallWrapper.__call__ = _timed_cw
_orig_tick = tr.Animation._tick


def timed_tick(self):
    t0 = time.perf_counter()
    _orig_tick(self)
    FRAMES.append((time.perf_counter() - t0) * 1000)


tr.Animation._tick = timed_tick


def count(w):
    return 1 + sum(count(c) for c in w.winfo_children())


def pump(app, until=None, timeout=20.0):
    t0 = time.perf_counter()
    while True:
        app.update()
        if until is None or until():
            # let pending idle work settle
            for _ in range(5):
                app.update()
            return time.perf_counter() - t0
        if time.perf_counter() - t0 > timeout:
            return float("nan")


def idle(app, seconds):
    end = time.perf_counter() + seconds
    while time.perf_counter() < end:
        app.update()
        time.sleep(0.002)


results = []


import cProfile, pstats
PROF = os.environ.get("PROF_STEP")


def step(app, label, action, until=None, settle=0.0):
    pr = cProfile.Profile() if PROF and PROF in label else None
    if pr: pr.enable()
    _step(app, label, action, until, settle)
    if pr:
        pr.disable()
        st = pstats.Stats(pr); st.sort_stats(os.environ.get("SORT","cumulative"))
        st.print_stats(os.environ.get("FILT","."), 30)
        if os.environ.get("CALLEES"): st.print_callees(os.environ["CALLEES"])


def _step(app, label, action, until=None, settle=0.0):
    FRAMES.clear()
    CB["max"] = 0.0
    CB["who"] = "(the action itself)"
    t0 = time.perf_counter()
    action()
    block = (time.perf_counter() - t0) * 1000
    gaps = [block]
    cond = lambda: not app._busy and (until is None or until())
    end_settle = None
    while True:
        # One Tcl event at a time, as mainloop() does: update() would run
        # every event that becomes due while it runs, so a build split in
        # slices would still look like one long block.
        while True:
            a = time.perf_counter()
            more = app.tk.dooneevent(tkinter._tkinter.DONT_WAIT)
            gaps.append((time.perf_counter() - a) * 1000)
            if not more:
                break
        if end_settle is None and cond():
            end_settle = time.perf_counter() + max(settle, 0.3)
            ready = (time.perf_counter() - t0) * 1000
        if end_settle is not None and time.perf_counter() > end_settle:
            break
        if time.perf_counter() - t0 > 30:
            ready = float("nan"); break
        time.sleep(0.001)
    dt = ready
    FRAMES[:] = [max(CB["max"], block)] + FRAMES  # first value = longest single callback
    fr = list(FRAMES)
    worst = fr[0]
    med = statistics.median(fr[1:]) if len(fr) > 1 else 0
    results.append((label, dt, len(fr), med, worst, count(app), max(gaps[1:] or [0])))
    if os.environ.get("WHO"):
        print(f"  {label}: slowest callback {CB['max']:.0f} ms in {CB['who']}, action {block:.0f} ms")


t0 = time.perf_counter()
app = build_app()
pump(app)
idle(app, 0.6)
results.append(("startup", (time.perf_counter() - t0) * 1000, 0, 0, 0, count(app), 0))
draw = app._views["draw"]
sim = app._views["simulation"]
mode = sys.argv[2] if len(sys.argv) > 2 else "simulate"

step(app, "language -> competition", lambda: app._views["language"].choose("en"), settle=0.4)
step(app, "competition -> mode", lambda: app._views["competition"].choose("UCL"), settle=0.4)
app._views["mode"].choose(mode)
idle(app, 0.8)                    # prewarm happens here
step(app, "mode -> draw (pots)", lambda: app._views["mode"].start(), settle=0.4)
step(app, "theme toggle", lambda: (app.appbar.theme_switch.toggle()), settle=0.3)
step(app, "pots -> choice", lambda: draw._go("choice"), settle=0.2)
step(app, "instant draw -> results", lambda: draw._launch("instant"),
     until=lambda: draw._phase == "results", settle=1.0)
if mode == "simulate":
    step(app, "results -> simulation", draw._to_simulation, settle=0.4)
    step(app, "run season + 200-run MC", sim._launch,
         until=lambda: sim._phase in ("results", "failed"), settle=1.0)
    print("sim phase:", sim._phase)

print(f"{'step':32s} {'ready':>8s} {'anim':>7s} {'tickmed':>7s} {'maxcb':>7s} {'maxgap':>7s} {'widgets':>8s}")
for label, dt, n, med, worst, w, gap in results:
    print(f"{label:32s} {dt:8.0f} {n:7d} {med:7.1f} {worst:7.1f} {gap:7.1f} {w:8d}")
app.destroy()
