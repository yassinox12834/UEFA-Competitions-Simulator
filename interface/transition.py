"""
transition.py - reusable animation engine for UEFA Predictor.

Everything that moves in the interface goes through here: screen changes,
card hover, progress bar. The module only knows Tk and CustomTkinter,
never the app, so it could be moved elsewhere as it is.

Three building blocks:

    Animation      the loop, based on TIME and not on a fixed number of
                   frames: the duration stays the same whether the machine
                   runs at 30 or at 120 frames per second.
    animate_*      the shortcuts built on it (value, colour).
    Transition     the sequencing of two views in the same container.

The views are placed with .place(relwidth=1, relheight=1): they can
therefore be shifted in x / y without breaking their internal layout.
"""

from __future__ import annotations

import time
import tkinter

import customtkinter as ctk


# =====================================================================
#  EASING CURVES
# =====================================================================
# Each one takes t in [0, 1] (raw progress) and returns the perceived
# progress. Without them, everything looks mechanical.

def linear(t):
    return t


def ease_out_cubic(t):
    """Starts fast, slows down at the end. The default for an entrance."""
    return 1 - (1 - t) ** 3


def ease_out_quint(t):
    """Same idea, but the braking is much stronger."""
    return 1 - (1 - t) ** 5


def ease_in_out_cubic(t):
    """Gentle on both sides: for a round trip or a value."""
    return 4 * t ** 3 if t < 0.5 else 1 - ((-2 * t + 2) ** 3) / 2


def ease_out_back(t, overshoot=1.70158):
    """Slightly overshoots the target, then comes back: a bounce effect."""
    t -= 1
    return 1 + (overshoot + 1) * t ** 3 + overshoot * t ** 2


EASINGS = {
    "linear": linear,
    "ease_out_cubic": ease_out_cubic,
    "ease_out_quint": ease_out_quint,
    "ease_in_out_cubic": ease_in_out_cubic,
    "ease_out_back": ease_out_back,
}

DEFAULT_FPS = 60


# =====================================================================
#  ANIMATION LOOP
# =====================================================================

class Animation:
    """
    Calls on_frame(eased_progress) until the duration is over.

    It relies on widget.after(): the only clock available in Tk. But
    instead of counting frames, it re-reads the real time on every pass.
    If the machine lags, the animation skips positions instead of lasting
    longer.
    """

    def __init__(self, widget, duration, on_frame, on_done=None,
                 easing=ease_out_cubic, fps=DEFAULT_FPS, delay=0):
        self.widget = widget
        self.duration = max(1, int(duration))
        self.on_frame = on_frame
        self.on_done = on_done
        self.easing = easing
        self.interval = max(1, int(1000 / fps))
        self.delay = max(0, int(delay))
        self._job = None
        self._start = None
        self._cancelled = False

    # ---------- control ----------
    def start(self):
        if self.delay:
            self._job = self.widget.after(self.delay, self._begin)
        else:
            self._begin()
        return self

    def cancel(self):
        """Stops without calling on_done: the target is NOT reached."""
        self._cancelled = True
        if self._job is not None:
            try:
                self.widget.after_cancel(self._job)
            except tkinter.TclError:
                pass
            self._job = None

    def finish(self):
        """Jumps straight to the end (t = 1) and triggers on_done."""
        self.cancel()
        self._cancelled = False
        self._emit(1.0)
        self._done()

    # ---------- internal ----------
    def _begin(self):
        if self._cancelled:
            return
        self._start = time.perf_counter()
        self._emit(0.0)
        self._job = self.widget.after(self.interval, self._tick)

    def _tick(self):
        if self._cancelled:
            return
        elapsed = (time.perf_counter() - self._start) * 1000.0
        t = min(elapsed / self.duration, 1.0)
        if not self._emit(self.easing(t)):
            return                       # widget destroyed along the way
        if t < 1.0:
            self._job = self.widget.after(self.interval, self._tick)
        else:
            self._job = None
            self._done()

    def _emit(self, eased):
        try:
            self.on_frame(eased)
            return True
        except tkinter.TclError:
            self._cancelled = True
            return False

    def _done(self):
        if self.on_done is not None:
            try:
                self.on_done()
            except tkinter.TclError:
                pass


def animate(widget, duration, on_frame, on_done=None,
            easing=ease_out_cubic, delay=0):
    """Shortcut: creates the Animation and starts it."""
    return Animation(widget, duration, on_frame, on_done, easing,
                     delay=delay).start()


def animate_value(widget, setter, start, end, duration=260,
                  easing=ease_out_cubic, on_done=None, delay=0):
    """Interpolates a number: progress bar, height, margin..."""
    span = end - start
    return animate(widget, duration,
                   lambda e: setter(start + span * e),
                   on_done, easing, delay)


# =====================================================================
#  COLOURS
# =====================================================================
# CustomTkinter accepts "#1b1f27", "gray20", or a (light, dark) pair.
# winfo_rgb() can read the first two forms: all that is needed is to pick
# the right half of the pair before handing it over.

def resolve_color(color):
    """(light, dark) pair -> the colour of the current appearance mode."""
    if isinstance(color, (tuple, list)):
        if len(color) != 2:
            return color[0]
        return color[1] if ctk.get_appearance_mode() == "Dark" else color[0]
    return color


_RGB_CACHE = {}


def to_rgb(widget, color):
    """Tk colour -> (r, g, b) on 0-255. None if transparent or unreadable.

    The result is cached. winfo_rgb() is not a Python calculation: it is a
    round trip to the Tcl interpreter. A fade frame asked for two per
    colour being animated, which meant 722 calls every 16 ms on the pots
    screen. But the answer only depends on the colour string, never on the
    widget asking the question: it can therefore be cached safely, and the
    cache holds a few dozen entries since the palette is fixed in
    config.py.
    """
    color = resolve_color(color)
    if not color or color == "transparent":
        return None
    cached = _RGB_CACHE.get(color)
    if cached is not None:
        return cached
    try:
        r, g, b = widget.winfo_rgb(color)       # 16 bits per channel
    except tkinter.TclError:
        return None
    rgb = (r // 257, g // 257, b // 257)
    _RGB_CACHE[color] = rgb
    return rgb


def to_hex(rgb):
    return "#%02x%02x%02x" % rgb


def lerp_color(widget, start, end, t):
    """Blends two colours. None if either of them is unreadable."""
    a, b = to_rgb(widget, start), to_rgb(widget, end)
    if a is None or b is None:
        return None
    return to_hex(tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3)))


# --- colour animation registry ----------------------------------------
# Only one animation per (widget, property): if the cursor moves back and
# forth quickly, the new one cancels the previous one instead of fighting
# it frame by frame.

def _registry(widget):
    reg = getattr(widget, "_tr_color_anims", None)
    if reg is None:
        reg = {}
        widget._tr_color_anims = reg
    return reg


def animate_color(widget, prop, target, duration=150,
                  easing=ease_out_cubic, on_done=None):
    """
    Slides widget[prop] towards `target`.

    If the starting colour cannot be interpolated (transparent), the
    target is applied at once: better a jump than an exception.
    """
    reg = _registry(widget)
    running = reg.pop(prop, None)
    if running is not None:
        running.cancel()

    try:
        start = widget.cget(prop)
    except (ValueError, AttributeError, tkinter.TclError):
        return None

    if lerp_color(widget, start, target, 0.5) is None:
        widget.configure(**{prop: target})
        if on_done:
            on_done()
        return None

    def frame(e):
        mixed = lerp_color(widget, start, target, e)
        if mixed:
            widget.configure(**{prop: mixed})

    def done():
        reg.pop(prop, None)
        widget.configure(**{prop: target})    # the exact value, not the rounded one
        if on_done:
            on_done()

    anim = animate(widget, duration, frame, done, easing)
    reg[prop] = anim
    return anim


# =====================================================================
#  FADE (dissolve)
# =====================================================================
# Tk has no per-widget transparency: it is impossible to lower the alpha
# of a frame. So we cheat, by pulling ALL the colours of the subtree
# towards the background colour, then bringing them back to their
# original value. To the eye, the view appears.

_FADE_PROPS = ("fg_color", "text_color", "border_color", "progress_color")


_WRITABLE_CACHE = {}


def _writable(widget, prop, value):
    """Can widget[prop] be WRITTEN, and not only read?

    CustomTkinter trap: cget(prop) can answer while configure(prop=...)
    refuses. CTkSegmentedButton, for example, lets you read border_color
    but raises ValueError as soon as you write it. Without this test, the
    fade starts and then breaks on the first frame.

    The answer only depends on the widget's CLASS, never on the instance:
    it is therefore cached by (class, property). That is what makes the
    test free. Doing it on every widget cost 200 ms on its own on the pots
    screen, because a configure() on a CustomTkinter widget redraws its
    whole canvas.
    """
    key = (widget.__class__, prop)
    known = _WRITABLE_CACHE.get(key)
    if known is not None:
        return known
    try:
        widget.configure(**{prop: value})
        answer = True
    except (ValueError, AttributeError, tkinter.TclError):
        answer = False
    _WRITABLE_CACHE[key] = answer
    return answer


def _snapshot(widget, out, depth=0):
    """Collects the animatable colours of the widget and its descendants.

    `depth` is used for the cap in dissolve_in: the deeper a widget is in
    the tree, the less its fade is noticed, so it is the first to be
    sacrificed when the screen is too crowded.
    """
    for prop in _FADE_PROPS:
        try:
            value = widget.cget(prop)
        except (ValueError, AttributeError, tkinter.TclError):
            continue
        if not value or value == "transparent":
            continue
        if to_rgb(widget, value) is None:
            continue
        if not _writable(widget, prop, value):
            continue
        out.append((widget, prop, value, depth))

    for child in widget.winfo_children():
        _snapshot(child, out, depth + 1)
    return out


# Cap on the number of colours a single fade is allowed to animate.
# Each colour costs one configure() per frame, and a configure() on a
# CustomTkinter widget redraws its entire canvas. The pots screen has 361:
# animated in full, a single frame took 340 ms, twenty times the budget of
# a frame at 60 frames per second, so the fade lasted longer than the
# screen it was meant to reveal.
# Beyond the cap we keep the shallowest widgets: these are the large
# blocks, the ones whose appearance is really noticed. The leaves simply
# appear at once, which the eye does not notice.
MAX_FADE_TARGETS = 20


def dissolve_in(widget, background, duration=260, delay=0,
                easing=ease_out_cubic, on_done=None):
    """
    Fades `widget` in from the `background` colour.

    The original colours (light/dark pairs included) are restored exactly
    as they were at the end: switching theme remains possible afterwards.
    """
    found = _snapshot(widget, [])
    if len(found) > MAX_FADE_TARGETS:
        # Python's sort() is stable: at equal depth, the widgets stay in
        # the order in which the tree was walked.
        found.sort(key=lambda row: row[3])
        found = found[:MAX_FADE_TARGETS]

    # Both ends of each gradient are converted ONCE, here, and the
    # interpolation that follows is only integer arithmetic. Otherwise
    # every frame would reconvert the two colours of every target: the
    # real work was the conversion, not the fade.
    start = to_rgb(widget, background)
    targets = []
    if start is not None:
        for w, prop, value, _depth in found:
            end = to_rgb(w, value)
            if end is not None:
                targets.append((w, prop, value, start, end))

    if not targets:
        if on_done:
            on_done()
        return None

    def apply(t):
        for w, prop, value, a, b in targets:
            w.configure(**{prop: "#%02x%02x%02x" % (
                int(a[0] + (b[0] - a[0]) * t),
                int(a[1] + (b[1] - a[1]) * t),
                int(a[2] + (b[2] - a[2]) * t))})

    apply(0.0)

    def done():
        for w, prop, value, _a, _b in targets:
            try:
                w.configure(**{prop: value})
            except tkinter.TclError:
                pass
        if on_done:
            on_done()

    return animate(widget, duration, apply, done, easing, delay)


def stagger_in(widgets, background, duration=240, step_ms=70,
               easing=ease_out_cubic):
    """Same fade, but staggered: the cards arrive one after the other."""
    return [dissolve_in(w, background, duration, i * step_ms, easing)
            for i, w in enumerate(widgets)]


# =====================================================================
#  SCREEN TRANSITION
# =====================================================================

class Transition:
    """
    Animates the change from `old` to `new` in `container`.

    The available modes:
        slide_left / slide_right   horizontal push, with parallax
        slide_up   / slide_down    vertical push
        fade                       fade + slight upward slide
        none                       no effect

    `on_done` is ALWAYS called, including in "none" mode: it is what puts
    the old view away and hands control back to the router.
    """

    KINDS = ("slide_left", "slide_right", "slide_up", "slide_down",
             "fade", "none")

    DURATION = 300
    #  Parallax factor: the old view recedes more slowly than the new one
    #  advances. Below 1.0, no gap appears between the two; this is what
    #  gives the impression of depth.
    PARALLAX = 0.35

    @staticmethod
    def run(root, container, old, new, kind, on_done,
            duration=None, background=None):
        duration = duration or Transition.DURATION

        if old is None or kind == "none" or not kind:
            Transition._instant(new, on_done)
        elif kind == "slide_left":
            Transition._slide(root, container, old, new, (1, 0), duration, on_done)
        elif kind == "slide_right":
            Transition._slide(root, container, old, new, (-1, 0), duration, on_done)
        elif kind == "slide_up":
            Transition._slide(root, container, old, new, (0, 1), duration, on_done)
        elif kind == "slide_down":
            Transition._slide(root, container, old, new, (0, -1), duration, on_done)
        elif kind == "fade":
            Transition._fade(root, new, background, duration, on_done)
        else:
            Transition._instant(new, on_done)

    # ---------- modes ----------
    @staticmethod
    def _instant(new, on_done):
        new.place(x=0, y=0, relwidth=1, relheight=1)
        new.lift()
        on_done()

    @staticmethod
    def _slide(root, container, old, new, direction, duration, on_done):
        """direction = (+1, 0): the new view enters from the right."""
        dx, dy = direction
        width = container.winfo_width() or container.winfo_reqwidth()
        height = container.winfo_height() or container.winfo_reqheight()
        span_x, span_y = dx * width, dy * height

        new.place(x=span_x, y=span_y, relwidth=1, relheight=1)
        new.lift()

        def frame(e):
            new.place_configure(x=int(span_x * (1 - e)),
                                y=int(span_y * (1 - e)))
            old.place_configure(x=int(-span_x * Transition.PARALLAX * e),
                                y=int(-span_y * Transition.PARALLAX * e))

        def done():
            new.place_configure(x=0, y=0)
            old.place_configure(x=0, y=0)    # reset for next time
            on_done()

        animate(root, duration, frame, done, ease_out_cubic)

    @staticmethod
    def _fade(root, new, background, duration, on_done):
        new.place(x=0, y=0, relwidth=1, relheight=1)
        new.lift()
        rise = 16                            # the content rises a little as it appears
        animate(root, duration,
                lambda e: new.place_configure(y=int(rise * (1 - e))),
                lambda: new.place_configure(y=0), ease_out_cubic)
        dissolve_in(new, background or "#000000", duration, on_done=on_done)
