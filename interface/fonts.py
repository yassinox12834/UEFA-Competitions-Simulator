"""
fonts.py - the app's typography, in a single place.

CustomTkinter trap: a CTkFont can only exist AFTER the window has been
created (it needs a live Tk interpreter). The fonts therefore cannot be
declared as module constants. Hence this pattern:

    FONTS         a dictionary, empty at first, shared by everyone
    build_fonts() fills it; called once from App.__init__

Widgets read FONTS.get("body"): before the call they receive None, which
CustomTkinter accepts (default font). Afterwards everything is in place.

The family is chosen from those the system really has (_pick): Segoe UI
Variable on Windows 11, Segoe UI on Windows 10, Inter or SF elsewhere,
otherwise Tk's default font. The digits of Segoe UI and Inter all have the
same width, which lines up table columns without a monospaced font.

tk_font(px, weight) is for drawing on a Canvas (tables, final bracket): a
Canvas is not a CustomTkinter widget, so it does not benefit from the
automatic HiDPI scaling. We give it fonts already multiplied by the
window's scaling factor.
"""

import tkinter.font

import customtkinter as ctk

FONTS = {}
FAMILY = None
_TK_FONTS = {}

_UI_FAMILIES = ("Segoe UI Variable Text", "Segoe UI", "Inter", "SF Pro Text",
                "Helvetica Neue", "Roboto", "Noto Sans", "DejaVu Sans")
_DISPLAY_FAMILIES = ("Segoe UI Variable Display", "Segoe UI Semibold", "Segoe UI",
                     "Inter Display", "Inter", "SF Pro Display", "Roboto",
                     "Noto Sans", "DejaVu Sans")
_MONO_FAMILIES = ("Cascadia Mono", "Consolas", "JetBrains Mono", "Menlo",
                  "DejaVu Sans Mono", "Liberation Mono", "Courier New", "Courier")


def _families():
    try:
        return set(tkinter.font.families())
    except Exception:
        return set()


def _pick(candidates, available, fallback):
    for name in candidates:
        if name in available:
            return name
    return fallback


def build_fonts():
    global FAMILY
    available = _families()
    ui = _pick(_UI_FAMILIES, available, "TkDefaultFont")
    display = _pick(_DISPLAY_FAMILIES, available, ui)
    mono = _pick(_MONO_FAMILIES, available, "Courier")
    FAMILY = {"ui": ui, "display": display, "mono": mono}

    def f(size, weight="normal", family=ui):
        return ctk.CTkFont(family=family, size=size, weight=weight)

    FONTS.update({
        "display": f(30, "bold", display),     # winner's name
        "brand": f(16, "bold", display),
        "title": f(28, "bold", display),
        "h1": f(20, "bold", display),
        "h2": f(16, "bold"),
        "body": f(13),
        "body_b": f(13, "bold"),
        "small": f(12),
        "small_b": f(12, "bold"),
        "tiny": f(11),
        "overline": f(10, "bold"),              # small, spaced capitals
        "badge": f(12, "bold"),
        "cta": f(14, "bold"),
        "mono": f(11, family=mono),
    })
    return FONTS


def tk_font(widget, px, weight="normal", family="ui"):
    """A Tk font `px` logical pixels tall, already scaled to the window.

    A negative size means pixels to Tk (positive means points): we want
    pixels, as everywhere else in the Canvas drawings.
    """
    scale = scaling(widget)
    name = (FAMILY or {}).get(family, "TkDefaultFont")
    key = (name, px, weight, round(scale, 3))
    font = _TK_FONTS.get(key)
    if font is None:
        font = tkinter.font.Font(family=name, size=-max(1, round(px * scale)),
                                 weight=weight)
        _TK_FONTS[key] = font
    return font


def scaling(widget):
    """The CustomTkinter scaling factor of the window holding `widget`."""
    try:
        return ctk.ScalingTracker.get_widget_scaling(widget)
    except Exception:
        return 1.0
