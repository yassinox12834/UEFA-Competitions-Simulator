"""
app.py - the window and the router.

App is the only class that knows about:
    - the global menu state (lang, comp, mode) that every view reads,
    - translation, through t(),
    - the router: which screen is shown, and how we move on to the next one.

It does not know what is INSIDE the screens, nor what happens after the
menu: that part goes to the on_complete callback, which main.py provides.
This lets the draw engine be plugged in without touching the interface.
"""

import customtkinter as ctk

import platform_utils as platform_utils
import transition as tr
from chrome import AppBar, StepRail
from config import (APPEARANCE, BG, COLOR_THEME, COMP, DEFAULT_COMP,
                    DEFAULT_LANG, DEFAULT_MODE, MIN_HEIGHT, MIN_WIDTH,
                    START_HEIGHT, START_WIDTH, STRINGS, SURFACE,
                    TRANS_DURATION_MS, TRANSITION, WINDOW_TITLE)
from fonts import build_fonts
from theme import apply_theme
from images import window_icon


class App(ctk.CTk):

    # The step rail counts three phases. The three menu screens are three
    # questions of a single phase, "Welcome"; the draw is the second phase
    # and the simulation the third. StepHeader still announces "step n of 3"
    # inside the menu: that is a different level of reading.
    STEPS = {"language": 1, "competition": 1, "mode": 1, "draw": 2,
             "simulation": 3}

    def __init__(self, on_complete=None):
        super().__init__()
        ctk.set_appearance_mode(APPEARANCE)
        # Before any widget: CustomTkinter's default colours are read when
        # each widget is created (see theme.py).
        apply_theme(COMP[DEFAULT_COMP]["accent"], COMP[DEFAULT_COMP]["accent_hover"],
                    base=COLOR_THEME)
        self.title(WINDOW_TITLE)
        self._install_geometry()
        self.configure(fg_color=BG)

        # What the menu triggers once the 3 choices are made. Provided by
        # main.py; None means draft mode, where the choices are simply
        # printed to the console.
        self._on_complete = on_complete

        self.fonts = build_fonts()

        # --- global state, read by every view ---
        self.lang = DEFAULT_LANG
        self.comp = DEFAULT_COMP
        self.mode = DEFAULT_MODE
        # Set by DrawView when the user moves on to the simulation:
        # (comp, teams, matchdays, pots_model). Read by SimulateView.
        self.draw_result = None

        self.appbar = AppBar(self, self)
        self.appbar.pack(fill="x")
        self.rail = StepRail(self, self)
        self.rail.pack(fill="x")

        self.container = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0)
        self.container.pack(fill="both", expand=True)
        self.container.pack_propagate(False)

        self._views = {}
        self._current = None
        self._current_name = None
        self._busy = False        # prevents two animations at the same time

        if ctk.get_appearance_mode() == "Dark":
            self.appbar.theme_switch.select()

        self.bind("<Escape>", lambda _e: self._key(lambda v: v.on_back()))
        self.bind("<Return>", lambda _e: self._key(lambda v: v.on_enter()))
        self._apply_window_icon()

    @property
    def current_view(self):
        """The name of the screen being shown. The bars need it: the step
        number no longer tells screens apart, since the three menu screens
        share step 1."""
        return self._current_name

    # ---------- translation ----------
    def t(self, key, /, **kw):
        """The text for `key` in the current language, placeholders filled.

        The slash is not decoration: it makes `key` positional-only.
        Without it, a text containing a placeholder named {key} (and there
        is one, the message for an unknown pot key) would be called as
        t("...", key=...), and Python would see two values for the same
        parameter. The word "key" then becomes a placeholder name like any
        other.

        Keyword arguments are passed as they are to str.format:
        t("pot_n", n=3) returns "Pot 3", and t("tpl_pot_size", n=1, got=8,
        want=9) returns the complete sentence. With no keyword the raw text
        is returned, which lets a caller do its own .format() later, as the
        results screen does.

        A missing text returns its own key: a forgotten key stands out on
        screen instead of raising a KeyError in the middle of the ceremony.
        """
        text = STRINGS[self.lang].get(key, key)
        if not kw:
            return text
        try:
            return text.format(**kw)
        except (KeyError, IndexError):
            # Key translated in one language but not the other, or a stray
            # literal brace: show the raw text rather than crash the
            # interface.
            return text

    # ---------- router ----------
    def register(self, name, view_cls):
        self._views[name] = view_cls(self.container, self)

    def prewarm(self, name):
        """Tell a screen that it will be needed soon.

        A screen that is heavy to build can use this to get ready while the
        user is still looking at the previous one. The calling screen does
        not need to know whether the next one cares: if it has no
        prewarm(), nothing happens.
        """
        view = self._views.get(name)
        hook = getattr(view, "prewarm", None)
        if hook is not None:
            hook()

    def show(self, name, transition=TRANSITION):
        if self._busy:
            return
        new = self._views[name]
        old = self._current
        if new is old:
            return

        if old is not None:
            old.on_hide()
        new.on_show()
        self._current_name = name
        self.refresh_chrome()

        if old is None:
            # First display: the blocks settle one after another, which
            # sets the tone for the rest of the app.
            new.place(x=0, y=0, relwidth=1, relheight=1)
            new.lift()
            self._current = new
            tr.stagger_in(new.blocks() or [new], self.surface_hex(),
                          duration=300, step_ms=70)
            return

        self._busy = True

        def done():
            old.place_forget()
            self._current = new
            self._busy = False

        tr.Transition.run(self, self.container, old, new, transition, done,
                          duration=TRANS_DURATION_MS,
                          background=self.surface_hex())

    def back(self, name):
        self.show(name, "slide_right")

    def _key(self, action):
        if self._current is not None and not self._busy:
            action(self._current)

    # ---------- appearance ----------
    def surface_hex(self):
        return tr.resolve_color(SURFACE)

    def toggle_appearance(self):
        dark = bool(self.appbar.theme_switch.get())
        ctk.set_appearance_mode("dark" if dark else "light")
        self.refresh_chrome()
        if self._current is not None:
            self._current.refresh_text()

        # Switching the whole theme is expensive to redraw: lock the switch
        # for a few seconds to avoid flipping back and forth.
        self.appbar.theme_switch.configure(state="disabled")
        self.appbar.theme_switch.after(
            5000,
            lambda: self.appbar.theme_switch.configure(state="normal"))

    def refresh_chrome(self):
        step = self.STEPS.get(self._current_name, 1)
        self.appbar.refresh(step)
        self.rail.refresh(step)
        self._apply_window_icon()

    def _install_geometry(self):
        """
        Preferred size, but never larger than the screen: on a laptop the
        window shrinks instead of spilling under the taskbar. CustomTkinter
        trap: in geometry(), the SIZE is multiplied by the scaling factor
        but the POSITION is not, hence the mix of units below.
        """
        scaling = ctk.ScalingTracker.get_window_scaling(self)
        area_w, area_h = platform_utils._work_area(self)
        w = int(min(START_WIDTH, (area_w - 40) / scaling))
        h = int(min(START_HEIGHT, (area_h - 50) / scaling))
        x = max(0, int((area_w - w * scaling) / 2))
        y = max(0, int((area_h - h * scaling) / 2))
        self.minsize(min(MIN_WIDTH, w), min(MIN_HEIGHT, h))
        self.geometry(f"{w}x{h}+{x}+{y}")

    _icon_comp = None

    def _apply_window_icon(self):
        """Window icon = logo of the current competition."""
        # refresh_chrome() comes through here on every screen change, and
        # window_icon() re-reads and resizes the PNG on every call: without
        # this guard we would pay for a full decode for nothing on every
        # navigation.
        if self._icon_comp == self.comp:
            return
        self._icon_comp = self.comp
        # Keep the reference in self._icon: without it Python's garbage
        # collector would free the image and the icon would disappear.
        self._icon = window_icon(self.comp)
        if self._icon is not None:
            try:
                self.iconphoto(True, self._icon)
            except Exception:
                pass               # a missing icon stops nothing

    # ---------- accents ----------
    @property
    def accent(self):
        return COMP[self.comp]["accent"]

    @property
    def accent_hover(self):
        return COMP[self.comp]["accent_hover"]

    # ---------- menu exit point ----------
    def on_menu_complete(self):
        """
        Called when the 3 choices are made (language, competition, mode).

        Two independent things happen, in this order: main.py is notified
        (it logs the choices), then we move on to the draw screen. The menu
        still does not know what is behind that screen name; the router
        does.
        """
        if self._on_complete is not None:
            self._on_complete(self.lang, self.comp, self.mode)
        else:
            print(f"lang={self.lang}  comp={self.comp}  mode={self.mode}")
        self.show("draw")
