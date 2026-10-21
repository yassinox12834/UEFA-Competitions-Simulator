"""
main.py - the single entry point. This is where the app is launched.

This file is the dispatcher: it draws nothing and computes nothing. It
just connects the pieces in the right order, and it is the only place
where the order matters:

    1. DPI          before any window, otherwise the rendering is blurry
    2. App          the window, the router, the fonts
    3. the views    registered from the catalogue in views.py
    4. mainloop     Tk takes over until the window is closed

File map:
    config.py         constants, colours, translated texts, paths
    platform_utils.py Windows specifics (DPI, usable screen area)
    images.py         every image: PNGs, drawn icons, cache
    fonts.py          the fonts, created after the window
    transition.py     the animation engine
    widgets.py        reusable building blocks (cards, buttons, headers)
    base_view.py      the contract shared by every screen
    chrome.py         top bar and step rail
    draw_engine.py    the bridge to model/: pots, draw, ceremony
    draw_widgets.py   the building blocks specific to the draw screen
    views.py          the three menu screens, then the draw
    sim_engine.py     the bridge to model/simulation.py, on another thread
    sim_view.py       the simulation screen: settings, season, results
    app.py            the window and the router
    main.py           this file: the assembly
"""

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

import platform_utils as platform_utils                          # noqa: E402

# Must happen BEFORE the first window, so before importing anything that
# would create a widget.
platform_utils._enable_dpi_awareness()

from app import App                                         # noqa: E402
from views import VIEW_REGISTRY                             # noqa: E402


def run_engine(lang, comp, mode):
    """
    Menu exit: the three choices arrive here.

    The draw no longer goes through this function. DrawView launches it
    itself, via interface/draw_engine.py, because it needs to talk to it
    (replace a club, replay the ceremony, draw again) and not just trigger
    it once.

    Neither does the simulation: DrawView stores the draw in
    app.draw_result and shows the "simulation" screen (sim_view.py), which
    runs model/simulation.py on a separate thread. This function is now
    only used to log the three menu choices.
    """
    print(f"lang={lang}  comp={comp}  mode={mode}")


def build_app():
    """Builds the complete app without launching it (handy for testing)."""
    app = App(on_complete=run_engine)
    for name, view_cls in VIEW_REGISTRY:
        app.register(name, view_cls)
    app.show(VIEW_REGISTRY[0][0])          # first screen of the journey
    return app


def main():
    build_app().mainloop()


if __name__ == "__main__":
    # Needed on Windows: the Monte Carlo of 10 000 seasons starts worker
    # processes, and each of them re-imports this file. Without the
    # __main__ guard every worker would open a window of its own.
    import multiprocessing
    multiprocessing.freeze_support()
    main()
