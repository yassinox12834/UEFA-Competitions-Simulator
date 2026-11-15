"""
base_view.py - the contract shared by every screen.

A screen does not inherit from CTkFrame directly: it inherits from
BaseView, which gives it a centred body (self.body) and a list of methods
that the router (App) knows how to call. Adding a screen later therefore
means writing a class that fills in these gaps, nothing more.
"""

import logging
import time
import tkinter
import types

import customtkinter as ctk

from config import SURFACE

log = logging.getLogger(__name__)


def is_sliced(built):
    """True if a builder returned a generator, i.e. asks to be built in slices."""
    return isinstance(built, types.GeneratorType)


class SliceBuild:
    """
    Runs a panel builder written as a generator, a few slices per turn of
    the event loop instead of all of it in one callback.

    A builder marks its cut points with a bare `yield`. Every CustomTkinter
    widget draws its own rounded corners on a canvas, so a results screen
    costs 150 to 200 ms to build; done in one callback, that is 200 ms
    during which the window ignores clicks and the spinner stops. Here the
    slices run back to back until about BUDGET_MS is spent, then Tk gets
    the hand back (repaints, the spinner, a click) before the next batch.
    On a fast machine several slices go in one batch; on a slow one each
    slice gets its own.

    on_done()      called once the generator is exhausted
    on_error(exc)  called instead if a slice raises
    finish_now()   builds whatever is left, synchronously (the panel is
                   needed right now)
    cancel()       stops for good; nothing more is called
    """

    BUDGET_MS = 12
    GAP_MS = 1

    def __init__(self, widget, gen, on_done, on_error=None):
        self.widget, self.gen = widget, gen
        self.on_done, self.on_error = on_done, on_error
        self._job = None
        self.finished = False

    def start(self):
        self._step()
        return self

    def _step(self):
        self._job = None
        t0 = time.perf_counter()
        try:
            while True:
                next(self.gen)
                if (time.perf_counter() - t0) * 1000 >= self.BUDGET_MS:
                    break
        except StopIteration:
            self._finish()
            return
        except Exception as exc:
            self._fail(exc)
            return
        try:
            self._job = self.widget.after(self.GAP_MS, self._step)
        except tkinter.TclError:
            self.finished = True          # the host was destroyed

    def finish_now(self):
        if self.finished:
            return
        self._cancel_job()
        try:
            for _ in self.gen:
                pass
        except Exception as exc:
            self._fail(exc)
            return
        self._finish()

    def cancel(self):
        self._cancel_job()
        self.finished = True
        try:
            self.gen.close()
        except Exception:
            pass

    def _cancel_job(self):
        if self._job is not None:
            try:
                self.widget.after_cancel(self._job)
            except (tkinter.TclError, ValueError):
                pass
            self._job = None

    def _finish(self):
        self.finished = True
        self.on_done()

    def _fail(self, exc):
        self.finished = True
        if self.on_error is not None:
            self.on_error(exc)
        else:
            log.error("sliced build failed", exc_info=exc)


class BaseView(ctk.CTkFrame):
    """
    build()        -> widgets, called once
    refresh_text() -> reapplies every translated text
    on_show()      -> on every display (calls refresh_text by default)
    on_hide()      -> just before leaving the screen
    on_theme_change() -> light/dark switched (rebuilds texts by default)
    blocks()       -> the large blocks, in order of appearance
    on_back()      -> Escape key
    on_enter()     -> Enter key
    """

    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color=SURFACE, corner_radius=0, **kwargs)
        self.app = app
        # All content lives in self.body, packed with expand=True: the
        # column stays vertically centred, even when the window is enlarged.
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(expand=True)
        self.build()

    def build(self):
        pass

    def refresh_text(self):
        pass

    def on_show(self):
        self.refresh_text()

    def on_hide(self):
        pass

    def on_theme_change(self):
        """Light/dark mode just changed.

        CustomTkinter widgets repaint themselves; only plain Tk widgets
        (colours resolved once) need help. The default is the old, safe
        behaviour: rebuild everything through refresh_text(). Screens that
        know better override it and redo only what is needed.
        """
        self.refresh_text()

    def blocks(self):
        return []

    def on_back(self):
        pass

    def on_enter(self):
        pass
