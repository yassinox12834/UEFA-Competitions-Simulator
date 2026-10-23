"""
views.py - the three menu screens: language, competition, mode, then
the draw. The simulation screen lives in sim_view.py and is only
registered here, at the end of VIEW_REGISTRY.

Each view inherits from BaseView and only does three things:
    build()        place its widgets, once
    refresh_text() rewrite every text in the current language
    choose(...)    store the choice in App, then ask for the next screen

No view knows the next one through a direct reference: it calls
self.app.show("name"). App holds the map of the journey, so adding or
reordering a screen does not touch this file.
"""

import tkinter
from tkinter import filedialog

import customtkinter as ctk

import transition as tr
from base_view import BaseView
from config import (AWAY, BALL_FLY_MS, BALL_OPEN_MS, USER_DIR, BORDER, CARD,
                    CARD_RADIUS, CHIP_BORDER, CHIP_DRAWN, CHIP_RADIUS,
                    CLUB_HOLD_MS, COMP, DEFAULT_SPEED, DRAW_SPEEDS, FORMAT,
                    HOME, LANG_NAMES, MODES, OPPONENT_GAP_MS, OPPONENT_MS,
                    POT_BREAK_MS, REPLACED, STAGE, SURFACE, SURFACE_2,
                    TEXT, TEXT_MUTED, UEFA_ASSOCIATIONS)
from draw_engine import (ConstraintError, DrawJob, PotsModel, SaveError,
                         TemplateError, fixtures_by_club, load_template,
                         replay_order, save_template)
from draw_widgets import (BowlStrip, ConstraintsDialog, MatchRow,
                          MessageDialog, OpponentCard, PotsBoard,
                          ReplaceDialog, Spinner, flat_frame, flat_label,
                          flying_ball, offset_in)
from fonts import FONTS
from images import (club_image, club_logo_path, club_photo, comp_image,
                    flag_image, mode_image, run_image)
from widgets import StepHeader, card_button, ghost_button


# =====================================================================
#  STEP 1: language
# =====================================================================

class LanguageView(BaseView):
    def build(self):
        self.header = StepHeader(self.body, self.app, 1)
        self.header.pack(pady=(44, 30))

        self.row = ctk.CTkFrame(self.body, fg_color="transparent")
        self.row.pack()
        self.cards = {}
        for code, name in LANG_NAMES.items():
            card = card_button(self.row, title=name, subtitle=code.upper(),
                               image=flag_image(code), width=230, height=208,
                               command=lambda c=code: self.choose(c))
            card.pack(side="left", padx=12)
            self.cards[code] = card

        self.keys_hint = ctk.CTkLabel(self.body, text="", font=self.app.fonts["tiny"],
                                      text_color=TEXT_MUTED)
        self.keys_hint.pack(pady=(34, 0))

    def blocks(self):
        return [self.header, *self.cards.values(), self.keys_hint]

    def choose(self, code):
        self.app.lang = code
        self.app.refresh_chrome()
        self.app.show("competition")

    def on_enter(self):
        self.choose(self.app.lang)

    def refresh_text(self):
        self.header.refresh("language_q", "language_h")
        self.keys_hint.configure(text=self.app.t("keys_hint"))
        for code, card in self.cards.items():
            card.set_accent(self.app.accent)
            card.set_selected(code == self.app.lang)


# =====================================================================
#  STEP 2: competition
# =====================================================================

class CompetitionView(BaseView):
    def build(self):
        self.header = StepHeader(self.body, self.app, 2)
        self.header.pack(pady=(40, 28))

        self.row = ctk.CTkFrame(self.body, fg_color="transparent")
        self.row.pack()
        self.cards = {}
        for key in COMP:
            card = card_button(self.row, title="", subtitle="",
                               image=comp_image(key), width=230, height=236,
                               accent=COMP[key]["accent"],
                               command=lambda k=key: self.choose(k))
            card.pack(side="left", padx=12)
            self.cards[key] = card

        self.back_btn = ghost_button(self.body, command=self.on_back)
        self.back_btn.pack(pady=32)

    def blocks(self):
        return [self.header, *self.cards.values(), self.back_btn]

    def choose(self, key):
        self.app.comp = key
        self.app.refresh_chrome()
        self.app.show("mode")

    def on_back(self):
        self.app.back("language")

    def on_enter(self):
        self.choose(self.app.comp)

    def refresh_text(self):
        self.header.refresh("competition_q", "competition_h")
        for key, card in self.cards.items():
            card.set_text(self.app.t(key), self.app.t(key + "_sub"))
            card.set_selected(key == self.app.comp)
        self.back_btn.configure(text=self.app.t("back"))


# =====================================================================
#  STEP 3: mode
# =====================================================================

class ModeView(BaseView):
    def build(self):
        self.header = StepHeader(self.body, self.app, 3)
        self.header.pack(pady=(22, 20))

        self.row = ctk.CTkFrame(self.body, fg_color="transparent")
        self.row.pack()
        self.cards = {}
        for m in MODES:
            card = card_button(self.row, title="", subtitle="",
                               width=310, height=192,
                               command=lambda k=m: self.choose(k))
            card.pack(side="left", padx=12)
            self.cards[m] = card

        # A reminder of the two previous choices: the user can start
        # without having to go back.
        self.recap = ctk.CTkFrame(self.body, fg_color=SURFACE_2, corner_radius=999,
                                  height=34)
        self.recap.pack(pady=(22, 0))
        self.recap_label = ctk.CTkLabel(self.recap, text="",
                                        font=self.app.fonts["small"],
                                        text_color=TEXT_MUTED)
        self.recap_label.pack(padx=18, pady=6)

        self.start_btn = ctk.CTkButton(self.body, text="", width=210, height=46,
                                       corner_radius=12,
                                       font=self.app.fonts["cta"],
                                       text_color="#FFFFFF",
                                       command=self.start)
        self.start_btn.pack(pady=(16, 0))

        self.back_btn = ghost_button(self.body, command=self.on_back)
        self.back_btn.pack(pady=14)

    def blocks(self):
        return [self.header, *self.cards.values(), self.recap,
                self.start_btn, self.back_btn]

    def choose(self, mode):
        self.app.mode = mode
        # The step rail shows or hides the "Simulation" badge depending on
        # the mode: it must be told, as for the competition.
        self.app.refresh_chrome()
        self.refresh_text()

    def on_show(self):
        # Last screen before the draw: the competition is known, so the
        # pots screen can already be built. It will do so when Tk has
        # nothing urgent left to do.
        super().on_show()
        self.app.prewarm("draw")

    def start(self):
        self.app.on_menu_complete()

    def on_back(self):
        self.app.back("competition")

    def on_enter(self):
        self.start()

    def refresh_text(self):
        self.header.refresh("mode_q", "mode_h")
        accent = self.app.accent
        for m, card in self.cards.items():
            card.set_text(self.app.t("mode_" + m), self.app.t("mode_" + m + "_d"))
            card.set_image(mode_image(m, accent))
            card.set_accent(accent)
            card.set_selected(m == self.app.mode)

        self.recap_label.configure(
            text="%s:  %s     |     %s" % (self.app.t("your_picks"),
                                           LANG_NAMES[self.app.lang],
                                           self.app.t(self.app.comp)))
        self.start_btn.configure(text=self.app.t("start"), fg_color=accent,
                                 hover_color=self.app.accent_hover)
        self.back_btn.configure(text=self.app.t("back"))

# =====================================================================
#  STEP 4: THE DRAW
# =====================================================================

class DrawView(BaseView):
    """
    A single screen, five states. They always follow each other in this
    order:

        pots      the pots, where a club can be replaced
        choice    all at once, or ceremony?
        working   the engine runs on another thread
        ceremony  the ceremony, ball by ball          (optional)
        results   the matchdays and the fixtures

    Only one panel exists at a time: changing state destroys the previous
    one and builds the next. It is more work for the machine than a set of
    hidden tabs, but it removes a whole family of bugs at once: a
    forgotten widget that keeps the old draw, an after() that wakes a
    panel nobody is looking at any more.

    Everything that is scheduled goes through _later() and _anim(), so
    that everything can be cancelled at once on leaving the screen. An
    after() that outlives its widget brings Tk down with a TclError that
    never points to the real culprit.
    """

    # ---------- construction ----------
    def build(self):
        # BaseView centres its body; here we want all the space.
        self.body.pack_configure(fill="both", expand=True)

        self.comp = None
        self.model = None
        # The mode for which the panels kept in memory were built. Without
        # it, going from "draw only" to "full simulation" brought back the
        # pots panel built while the chips were still clickable.
        self._mode = None
        self._dialog = None        # the "replace" box, kept open
        self._cst_dialog = None    # the "constraints" box, kept as well
        self.job = None
        self.teams = None
        self.matchdays = None
        self.script = None

        self._phase = None
        self._panel = None
        self._panels = {}          # phase -> panel kept in memory
        self._jobs = set()
        self._anims = []
        self._paused = False
        self._pending = None
        self._speed = DEFAULT_SPEED
        self._kind = "instant"
        self._error = None
        self._chunk_token = 0

        self.host = ctk.CTkFrame(self.body, fg_color="transparent")
        self.host.pack(fill="both", expand=True)

    def blocks(self):
        return [self.host]

    # ---------- life cycle ----------
    def on_show(self):
        # The competition may have changed since the last visit: the pots
        # are no longer the same, so we start again from scratch.
        if not self._ensure_model():
            return
        # If we were already on "pots" when leaving, _go() would stop
        # short. So we reset the phase to None: _go() will do the work
        # again, and will pick up the panel kept in memory if the
        # competition and the language have not changed.
        self._phase = None
        self._go("pots")

    def _ensure_model(self):
        """Brings the model AND the kept panels in line with the current choices.

        False if the model cannot be built; the caller must then stop,
        since the view has already moved to the error screen.

        Pulled out of on_show() so that prewarm() can use it too: when the
        mode screen warms things up, the draw view has never been displayed
        yet, so it has neither a competition nor a model. Without this
        sharing, the warm-up did nothing.

        Two things may have changed since the last visit, and they do not
        cost the same:

          the competition  other clubs, so a new model and new chips.
                           Everything is thrown away.
          the mode         the same clubs, but clickable or not. The model
                           stays valid; only the panels kept in memory are
                           out of date, because they froze the on_click at
                           the time they were built.

        The second case is the subtle one: _build_pots does read
        self.app.mode, but a kept panel is not rebuilt, so it would be
        served again as it was, with the chips of the previous mode.
        """
        same_comp = self.comp == self.app.comp and self.model is not None
        same_mode = self._mode == self.app.mode
        if same_comp and same_mode:
            return True

        self._mode = self.app.mode
        self._drop_dialog()            # it carries the old competition
        self._drop_panels()

        if same_comp:
            return True                # only the mode changed: the model holds

        self.comp = self.app.comp
        self.teams = self.matchdays = self.script = None
        try:
            self.model = PotsModel(self.comp)
        except Exception as exc:                # CSV missing, club missing
            self.model = None
            # force=True: we may already be on "failed" (we are retrying
            # from there), and without it _go() would exit immediately,
            # leaving the previous failure's message on screen.
            self._go("failed", force=True, error=exc)
            return False
        return True

    @property
    def editable(self):
        """Can the pots be touched on this screen?

        Only in "draw only". The full simulation starts from the same pots
        but goes all the way to the final: letting clubs be replaced there
        would give a whole season played by invented teams, which makes
        sense neither for the prediction engine nor for whoever is
        watching the result.
        """
        return self.app.mode == "draw"

    def on_hide(self):
        self._cancel_all()
        # A modal box left open would keep the keyboard and the mouse
        # while the screen underneath has disappeared: the main window
        # looks frozen, and nothing says why.
        for dialog in (self._dialog, self._cst_dialog):
            if dialog is not None and dialog.winfo_exists():
                dialog.close()

    def refresh_text(self):
        # Rebuilding the panel is the surest way to rewrite all its texts.
        # But we do NOT do it while the engine is running or during the
        # ceremony: _go() cancels every timer in progress, which would
        # leave the view frozen on its spinner or in the middle of a ball.
        # The colours of these two panels are (light, dark) pairs, so
        # CustomTkinter handles the theme change by itself.
        if self._phase in ("pots", "choice", "results", "failed"):
            self._drop_panels()        # the kept panels are in the old language
            self._go(self._phase, force=True)

    def on_back(self):
        if self._phase in ("choice", "results", "failed"):
            self._go("pots")
        elif self._phase == "ceremony":
            self._skip()
        else:
            self.app.back("mode")

    def on_enter(self):
        if self._phase == "pots":
            self._go("choice")
        elif self._phase == "ceremony":
            self._toggle_pause()
        elif self._phase == "results" and self.app.mode == "simulate":
            self._to_simulation()

    def _to_simulation(self):
        """Hands over to the simulation screen, with the draw under its arm.

        The draw (teams, matchdays) and the pots model (for replaced
        badges) are placed on App: SimulateView reads them in its
        on_show(). The two screens do not know each other.
        """
        if self.teams is None or self.matchdays is None:
            return
        self.app.draw_result = (self.comp, self.teams, self.matchdays, self.model)
        self.app.show("simulation")

    # ---------- timers ----------
    def _later(self, ms, fn):
        """An after() that we keep track of, so that everything can be cancelled."""
        job = None

        def wrapped():
            self._jobs.discard(job)
            fn()

        job = self.after(max(1, int(ms)), wrapped)
        self._jobs.add(job)
        return job

    def _anim(self, animation):
        if animation is not None:
            self._anims.append(animation)
        return animation

    def _cancel_all(self):
        for job in list(self._jobs):
            try:
                self.after_cancel(job)
            except (tkinter.TclError, ValueError):
                pass
        self._jobs.clear()
        for animation in self._anims:
            try:
                animation.cancel()
            except Exception:
                pass
        self._anims.clear()
        self._pending = None

    # ---------- internal router ----------
    # The panels we are allowed to keep from one visit to the next.
    #
    # "pots" costs 330 ms to build: thirty-six chips, and each
    # CustomTkinter widget draws its rounded corners by hand on a canvas.
    # Destroying it to rebuild it identically on every round trip to
    # "choice" was the real cause of the sluggish clicks. Its content only
    # depends on self.model, and _after_replace() updates just the place
    # that was touched: keeping it is therefore safe.
    #
    # The others are rebuilt every time, and that is deliberate:
    #   working   its animation must start from zero
    #   ceremony  it carries the state of a draw in progress
    #   results   it depends on the draw, which changes with every launch
    #   failed    it depends on the error message
    # All four are light, so the rebuild cannot be felt.
    CACHEABLE = ("pots", "choice")

    def _drop_panels(self):
        """Throws away the panels kept in memory.

        To be called as soon as what they DISPLAY changes without them
        knowing: a different competition (other clubs), a different
        language (other texts).
        """
        for panel in self._panels.values():
            # The displayed panel may be one of those being thrown away.
            # If it is not detached here, _go() would call pack_forget()
            # on a destroyed widget, and Tk would raise a TclError whose
            # message would never name the real culprit.
            if panel is self._panel:
                self._panel = None
            panel.destroy()
        self._panels.clear()

    def _go(self, phase, force=False, error=None):
        if phase == self._phase and not force:
            return
        # Every panel except "failed" reads self.model. It may be absent:
        # _ensure_model() failed and put us on "failed", from where we
        # come back here through "try again" or "back", two paths that
        # call _go() directly, without going through on_show() again.
        # _build_pots would then call len(model.pots) on None. So we
        # rebuild the model before building anything, and give up if it
        # still does not come: in that case _ensure_model() has already
        # recalled the error screen with an up-to-date message.
        if phase != "failed" and self.model is None:
            if not self._ensure_model():
                return
        self._cancel_all()
        if self._panel is not None and self._panel.winfo_exists():
            # pack_forget, not destroy: a kept panel must survive.
            self._panel.pack_forget()
            # We test the WIDGET, not self._phase: on_show() resets _phase
            # to None, and the kept panel would then be destroyed.
            if self._panel not in self._panels.values():
                self._panel.destroy()
        self._panel = None
        self._phase = phase
        self._error = error

        panel = None if force else self._panels.get(phase)
        if panel is not None and not panel.winfo_exists():
            self._panels.pop(phase, None)   # stale cache: we rebuild
            panel = None
        fresh = panel is None
        if fresh:
            stale = self._panels.pop(phase, None)
            if stale is not None:
                stale.destroy()
            builder = {"pots": self._build_pots,
                       "choice": self._build_choice,
                       "working": self._build_working,
                       "ceremony": self._build_ceremony,
                       "results": self._build_results,
                       "failed": self._build_failed}[phase]
            panel = ctk.CTkFrame(self.host, fg_color="transparent")
            panel.pack(fill="both", expand=True)
            builder(panel)
            if phase in self.CACHEABLE:
                self._panels[phase] = panel
        else:
            panel.pack(fill="both", expand=True)

        self._panel = panel
        # The fade is only for the first appearance. A panel that is
        # brought back already has its right colours: fading it again is
        # expensive and shows nothing new.
        if fresh:
            self._anim(tr.dissolve_in(panel, self.app.surface_hex(),
                                      duration=220))

    def prewarm(self):
        """Builds the pots screen BEFORE it is asked for.

        App calls this from the mode screen, that is, one click before the
        draw. The 330 ms of construction are then spent while the user is
        reading their two cards, and the "Start" button responds
        instantly instead of pausing.

        after_idle: nothing is built while Tk has work outstanding,
        otherwise we would make the current screen sluggish to make the
        next one snappy.
        """
        if "pots" in self._panels:
            return
        self.after_idle(self._prewarm_now)

    def _prewarm_now(self):
        if "pots" in self._panels:
            return
        if not self._ensure_model():
            return
        panel = ctk.CTkFrame(self.host, fg_color="transparent")
        self._build_pots(panel)
        self._panels["pots"] = panel    # built, but not shown yet

    def _header(self, parent, question_key, hint_key=None, hint_text=None,
                compact=False):
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.pack(pady=(14, 10) if compact else (18, 14))
        ctk.CTkLabel(wrap, text=self.app.t(question_key),
                     font=self.app.fonts["h2" if compact else "title"],
                     text_color=TEXT).pack()
        text = hint_text if hint_text is not None else (
            self.app.t(hint_key) if hint_key else "")
        if text:
            ctk.CTkLabel(wrap, text=text, font=self.app.fonts["small"
                         if compact else "body"],
                         text_color=TEXT_MUTED).pack(pady=(5, 0))
        return wrap

    # =================================================================
    #  STATE 1: THE POTS
    # =================================================================
    def _build_pots(self, parent):
        editable = self.editable
        self._header(parent, "pots_q", "pots_h" if editable else "pots_h_ro",
                     compact=True)

        # Buttons side by side, not one under the other: nine clubs per
        # pot only fit in 660 px of height if the footer stays on a single
        # line. Stacked, it stole the last row.
        footer = ctk.CTkFrame(parent, fg_color="transparent")
        footer.pack(side="bottom", pady=(8, 14))
        self.swaps_label = ctk.CTkLabel(footer, text="",
                                        font=self.app.fonts["tiny"],
                                        text_color=REPLACED)
        self.swaps_label.pack(pady=(0, 6))
        row = ctk.CTkFrame(footer, fg_color="transparent")
        row.pack()

        # Loading a template means replacing all thirty-six clubs at once:
        # it is therefore the same permission as the manual replacement,
        # and it stops at the same boundary.
        # The constraints follow exactly the same permission as the
        # replacement and the templates: none of this appears in full
        # simulation, where the pots are shown read-only. self.cst_btn
        # stays None in that case, and _refresh_constraints() knows to do
        # nothing.
        self.cst_btn = None
        if editable:
            for key, action in (("load_template", self._load_template),
                                ("save_template", self._save_template)):
                ctk.CTkButton(row, text=self.app.t(key), height=42,
                              width=170, corner_radius=12,
                              font=self.app.fonts["small"],
                              fg_color="transparent", border_width=1,
                              border_color=BORDER, text_color=TEXT_MUTED,
                              hover_color=SURFACE_2,
                              command=action).pack(side="left", padx=6)
            self.cst_btn = ctk.CTkButton(
                row, text="", height=42, width=170, corner_radius=12,
                font=self.app.fonts["small"], fg_color="transparent",
                border_width=1, border_color=BORDER, text_color=TEXT_MUTED,
                hover_color=SURFACE_2, command=self._open_constraints)
            self.cst_btn.pack(side="left", padx=6)

        back = ghost_button(row, command=self.on_back)
        back.configure(text=self.app.t("back"))
        back.pack(side="left", padx=6)
        ctk.CTkButton(row, text=self.app.t("continue"), width=200,
                      height=42, corner_radius=12, font=self.app.fonts["cta"],
                      text_color="#FFFFFF", fg_color=self.app.accent,
                      hover_color=self.app.accent_hover,
                      command=lambda: self._go("choice")).pack(side="left",
                                                               padx=6)

        self.board = PotsBoard(parent, self.app, self.comp, self.model,
                               on_click=self._open_replace if editable else None)
        self.board.pack(fill="both", expand=True, padx=16)
        # No board.refresh() here: the chips have just been built with the
        # right values. The refresh would rewrite the name, badge and
        # colours of all thirty-six clubs for nothing.
        self._refresh_swaps()
        self._refresh_constraints()

    def _refresh_swaps(self):
        count = self.model.swap_count() if self.model else 0
        self.swaps_label.configure(
            text=self.app.t("swaps_n").format(n=count) if count else "")

    def _refresh_constraints(self):
        """The count on the button: two loaded constraints can be seen
        without having to open the box."""
        if getattr(self, "cst_btn", None) is None:
            return
        count = len(self.model.constraints) if self.model else 0
        self.cst_btn.configure(text=self.app.t("cst_btn_n", n=count) if count
                               else self.app.t("cst_btn"))

    # ---------- forbidden fixtures ----------
    def _open_constraints(self):
        """Same reuse as the replacement box: a single instance, hidden and
        brought back rather than rebuilt."""
        if self._cst_dialog is None or not self._cst_dialog.winfo_exists():
            self._cst_dialog = ConstraintsDialog(
                self.winfo_toplevel(), self.app, self.comp, self.model,
                on_change=self._after_constraints)
        self._cst_dialog.open()

    def _after_constraints(self):
        # The previous draw is worthless: it may have been resolved with a
        # fixture that has just been forbidden.
        self.teams = self.matchdays = self.script = None
        self._refresh_constraints()

    # ---------- replacing a club by hand ----------
    def _open_replace(self, pot_index, slot_index, _chip):
        """Opens the box. BUILDS it only the first time.

        A brand-new CTkToplevel on every click means a window to request
        from the system plus about thirty CustomTkinter widgets to draw.
        So we keep it, and open_for() just restacks the fields and brings
        it back.
        """
        if self._dialog is None or not self._dialog.winfo_exists():
            self._dialog = ReplaceDialog(
                self.winfo_toplevel(), self.app, self.comp, self.model,
                catalogue=UEFA_ASSOCIATIONS, on_done=self._after_replace)
        self._dialog.open_for(pot_index, slot_index)

    def _drop_dialog(self):
        """Throws the boxes away: their competition or their model is no longer valid.

        Both together, and not only the replacement one: the constraints
        box also holds a reference to the PotsModel and the list of the 36
        clubs of the old competition.
        """
        for name in ("_dialog", "_cst_dialog"):
            dialog = getattr(self, name)
            if dialog is not None:
                if dialog.winfo_exists():
                    dialog.destroy()
                setattr(self, name, None)

    def _after_replace(self, pot_index, slot_index):
        # The previous draw is worthless: the clubs have changed.
        self.teams = self.matchdays = self.script = None
        # refresh_one, not refresh: one place moved, not thirty-six. The
        # whole board cost more than seventy configure() calls, hence as
        # many canvases redrawn, right after confirming the box.
        self.board.refresh_one(pot_index, slot_index)
        self._refresh_swaps()

    # ---------- loading a JSON template ----------
    def _load_template(self):
        """Replaces all thirty-six clubs at once, from a file.

        Nothing is applied until the file has been fully checked: a
        half-loaded template would leave inconsistent pots, far more
        painful to diagnose than a clean refusal.
        """
        path = filedialog.askopenfilename(
            parent=self.winfo_toplevel(), title=self.app.t("tpl_pick"),
            filetypes=[("JSON", "*.json"), ("All files", "*.*")])
        if not path:
            return
        shape = FORMAT[self.comp]
        try:
            pots, constraints, warnings = load_template(
                path, self.app.t(self.comp), shape["per_pot"], shape["pots"],
                UEFA_ASSOCIATIONS)
        # ConstraintError BEFORE TemplateError, not after: it inherits
        # from it, so an except TemplateError written first would swallow
        # it and the constraints branch would never run. Python tries the
        # excepts in file order, from top to bottom, without looking for
        # the most specific one.
        except ConstraintError as exc:
            self._report("cst_bad_title",
                         self.app.t("cst_bad", n=len(exc.problems)),
                         exc.problems, tone="error")
            return
        except TemplateError as exc:
            self._report("tpl_bad_title",
                         self.app.t("tpl_bad", n=len(exc.problems)),
                         exc.problems, tone="error")
            return

        count = self.model.apply_template(pots, constraints)
        self.teams = self.matchdays = self.script = None
        # Here the whole board has changed: a full refresh(), justified
        # for once.
        self.board.refresh()
        self._refresh_swaps()
        self._refresh_constraints()

        name = path.replace("\\", "/").rsplit("/", 1)[-1]
        self._report("tpl_ok_title",
                     self.app.t("tpl_ok", n=count, file=name),
                     warnings, tone="warn" if warnings else "ok")

    # ---------- saving the current pots ----------
    def _save_template(self):
        """Writes the thirty-six displayed clubs to templates/saved/.

        The exact counterpart of _load_template: what this button
        produces, the other must be able to read back without anyone
        touching the file in between.

        club_logo_path is passed as an argument rather than imported by
        draw_engine: the engine is not allowed to know images.py, which
        drags customtkinter in behind it.
        """
        try:
            path, warnings = save_template(
                self.model,
                logo_lookup=lambda club: club_logo_path(self.comp, club))
        except SaveError as exc:
            self._report("sv_bad_title", self.app.t("sv_bad"),
                         exc.problems, tone="error")
            return

        count = len(self.model.all_clubs())
        # The path from the project root, not the absolute path:
        # "templates/saved/UCL_20260826-143012.json" can be found by eye,
        # "C:/Users/.../UEFA/templates/..." overflows the box.
        try:
            shown = path.relative_to(USER_DIR).as_posix()
        except ValueError:
            shown = str(path)
        self._report("sv_ok_title",
                     self.app.t("sv_ok", n=count, file=shown),
                     warnings, tone="warn" if warnings else "ok")

    def _report(self, title_key, summary, entries, tone):
        """Shows a loading report, translated here and not earlier.

        draw_engine speaks no language: it returns (key, arguments) pairs,
        and the view is what puts them into French or English. The day a
        third language arrives, the engine does not move.
        """
        MessageDialog(self.winfo_toplevel(), self.app,
                      self.app.t(title_key), summary,
                      [self.app.t(key, **kw) for key, kw in entries],
                      tone=tone)

    # =================================================================
    #  STATE 2: ALL AT ONCE, OR CEREMONY?
    # =================================================================
    def _build_choice(self, parent):
        self._header(parent, "how_q", "how_h")

        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(expand=True)
        for kind in ("instant", "live"):
            card = card_button(
                row, title=self.app.t("run_" + kind),
                subtitle=self.app.t("run_" + kind + "_d"),
                image=run_image(kind, self.app.accent), width=310, height=250,
                accent=self.app.accent,
                command=lambda k=kind: self._launch(k))
            card.pack(side="left", padx=14)

        back = ghost_button(parent, command=lambda: self._go("pots"))
        back.configure(text=self.app.t("back"))
        back.pack(pady=(0, 26))

    # =================================================================
    #  STATE 3: THE ENGINE IS RUNNING
    # =================================================================
    def _launch(self, kind):
        self._kind = kind
        self.job = DrawJob(self.comp, self.model).start()
        self._go("working")
        self._poll_job()

    def _build_working(self, parent):
        middle = ctk.CTkFrame(parent, fg_color="transparent")
        middle.pack(expand=True)
        ctk.CTkLabel(middle, text="", image=comp_image(self.comp, box=(84, 84),
                                                       plate="#FFFFFF")).pack()
        self.work_label = ctk.CTkLabel(middle, text=self.app.t("drawing"),
                                       font=self.app.fonts["h2"],
                                       text_color=TEXT)
        self.work_label.pack(pady=(20, 14))
        self.spinner = Spinner(middle, self.app)
        self.spinner.pack()
        self.spinner.start()

    def _poll_job(self):
        answer = self.job.poll() if self.job else None
        if answer is None:
            self._later(70, self._poll_job)
            return
        if answer[0] == "error":
            self._go("failed", error=answer[1])
            return
        self.teams, self.matchdays = answer[1], answer[2]
        if self._kind == "live":
            self.script = replay_order(self.teams, self.model.pots,
                                       seed=self.job.seed)
            self._go("ceremony")
            self._start_ceremony()
        else:
            self._go("results")

    # =================================================================
    #  STATE 4: THE CEREMONY
    # =================================================================
    def _build_ceremony(self, parent):
        self.bowl = BowlStrip(parent, self.app)
        self.bowl.pack(fill="x", padx=26, pady=(16, 10))

        self.arena = ctk.CTkFrame(parent, fg_color=STAGE, corner_radius=CARD_RADIUS)
        self.arena.pack(fill="both", expand=True, padx=26)

        # Left: the stage where the ball lands and opens.
        self.stage = ctk.CTkFrame(self.arena, fg_color="transparent", width=330)
        self.stage.pack(side="left", fill="y", padx=(10, 0))
        self.stage.pack_propagate(False)
        # Pinned to the top, not centred: the club and the column of
        # opponents must start at the same height, otherwise the eye
        # travels back and forth between two offset blocks.
        self.stage_box = ctk.CTkFrame(self.stage, fg_color="transparent")
        self.stage_box.pack(pady=(26, 0))

        # Right: the opponents, home on the left, away on the right.
        board = ctk.CTkFrame(self.arena, fg_color="transparent")
        board.pack(side="left", fill="both", expand=True, padx=(6, 10), pady=10)
        self.sides = {}
        for key, colour in (("home", HOME), ("away", AWAY)):
            column = ctk.CTkFrame(board, fg_color="transparent")
            column.pack(side="left", fill="both", expand=True, padx=6)
            head = ctk.CTkFrame(column, fg_color="transparent")
            head.pack(anchor="w", pady=(0, 8))
            ctk.CTkFrame(head, width=10, height=10, corner_radius=5,
                         fg_color=colour).pack(side="left")
            ctk.CTkLabel(head, text=self.app.t(key), font=FONTS.get("badge"),
                         text_color=TEXT_MUTED).pack(side="left", padx=8)
            slots = ctk.CTkFrame(column, fg_color="transparent")
            slots.pack(fill="both", expand=True)
            self.sides[key] = slots

        # Bottom: where we are, and the controls.
        controls = ctk.CTkFrame(parent, fg_color="transparent")
        controls.pack(fill="x", padx=26, pady=(10, 16))

        self.progress = ctk.CTkLabel(controls, text="",
                                     font=self.app.fonts["small"],
                                     text_color=TEXT_MUTED)
        self.progress.pack(side="left")

        self.skip_btn = ghost_button(controls, command=self._skip, width=150)
        self.skip_btn.configure(text=self.app.t("skip"))
        self.skip_btn.pack(side="right")

        self.pause_btn = ghost_button(controls, command=self._toggle_pause,
                                      width=110)
        self.pause_btn.configure(text=self.app.t("pause"))
        self.pause_btn.pack(side="right", padx=8)

        speeds = ctk.CTkFrame(controls, fg_color="transparent")
        speeds.pack(side="right", padx=14)
        ctk.CTkLabel(speeds, text=self.app.t("speed"), font=FONTS.get("tiny"),
                     text_color=TEXT_MUTED).pack(side="left", padx=(0, 8))
        self.speed_btns = {}
        for value in DRAW_SPEEDS:
            button = ctk.CTkButton(
                speeds, text=f"x{value}", width=40, height=30,
                corner_radius=8, font=FONTS.get("tiny"),
                command=lambda v=value: self._set_speed(v))
            button.pack(side="left", padx=2)
            self.speed_btns[value] = button
        self._paint_speeds()

    def _set_speed(self, value):
        self._speed = value
        self._paint_speeds()

    def _paint_speeds(self):
        for value, button in self.speed_btns.items():
            chosen = value == self._speed
            button.configure(
                fg_color=self.app.accent if chosen else "transparent",
                hover_color=self.app.accent_hover if chosen else SURFACE_2,
                border_width=0 if chosen else 1, border_color=BORDER,
                text_color="#FFFFFF" if chosen else TEXT_MUTED)

    def _toggle_pause(self):
        self._paused = not self._paused
        self.pause_btn.configure(
            text=self.app.t("resume" if self._paused else "pause"))
        if not self._paused and self._pending is not None:
            pending, self._pending = self._pending, None
            pending()

    def _skip(self):
        self._cancel_all()
        self._go("results")

    # ---------- the sequence ----------
    def _start_ceremony(self):
        self._index = 0            # which club in the script
        self._ball_index = 0       # which ball in the current pot
        self._current_pot = None
        self._paused = False
        self._pending = None
        self._run_club()

    def _step_later(self, ms, fn):
        """Like _later, but respects the pause and the chosen speed."""
        def guarded():
            if self._phase != "ceremony":
                return
            if self._paused:
                self._pending = fn
                return
            fn()

        return self._later(ms / self._speed, guarded)

    def _run_club(self):
        if self._index >= len(self.script):
            self._step_later(CLUB_HOLD_MS, lambda: self._go("results"))
            return

        entry = self.script[self._index]
        self.progress.configure(
            text=self.app.t("club_of").format(i=self._index + 1,
                                              total=len(self.script)))

        # New pot: we fill the bowl and let it breathe.
        if entry["pot"] != self._current_pot:
            self._current_pot = entry["pot"]
            self._ball_index = 0
            self.bowl.set_pot(entry["pot"], len(self.model.pots[entry["pot"] - 1]))
            self._clear_stage()
            self._step_later(POT_BREAK_MS, lambda: self._fly_ball(entry))
            return

        self._clear_stage()
        self._fly_ball(entry)

    def _clear_stage(self):
        for child in self.stage_box.winfo_children():
            child.destroy()
        for slots in self.sides.values():
            for child in slots.winfo_children():
                child.destroy()

    def _fly_ball(self, entry):
        """The ball leaves the bowl and reaches the centre of the stage."""
        self.arena.update_idletasks()
        ball = flying_ball(self.arena, self.app.accent, box=(74, 74),
                           label=str(entry["pot"]))

        try:
            source = self.bowl.anchor_dot(self._ball_index)
            # The bowl lives above the arena: the starting y coordinate is
            # therefore negative, the ball enters from the top. That is
            # exactly the intended effect.
            sx, sy = offset_in(source, self.arena)
            tx = self.stage.winfo_x() + self.stage.winfo_width() // 2 - 37
            ty = 33          # where the club's badge is going to appear
        except (tkinter.TclError, AttributeError):
            sx = sy = 0
            tx, ty = 140, 33

        ball.place(x=sx, y=sy)
        self.bowl.pop(self._ball_index)
        self._ball_index += 1

        def frame(t):
            try:
                ball.place(x=sx + (tx - sx) * t, y=sy + (ty - sy) * t)
            except tkinter.TclError:
                pass

        def landed():
            self._open_ball(ball, entry)

        self._anim(tr.animate(self.arena, BALL_FLY_MS / self._speed, frame,
                              landed, easing=tr.ease_out_cubic))

    def _open_ball(self, ball, entry):
        """The ball fades away, the club appears in its place."""
        try:
            ball.destroy()
        except tkinter.TclError:
            pass

        card = ctk.CTkFrame(self.stage_box, fg_color="transparent")
        card.pack()
        ctk.CTkLabel(card, text="", image=club_image(
            self.comp, entry["club"], box=(88, 88), accent=self.app.accent,
            custom_path=self.model.logo_for(entry["club"]))).pack()
        ctk.CTkLabel(card, text=entry["club"], font=self.app.fonts["title"],
                     text_color=TEXT, wraplength=300).pack(pady=(14, 0))
        ctk.CTkLabel(card,
                     text=f'{entry["country"]}   |   '
                          f'{self.app.t("pot_n", n=entry["pot"])}',
                     font=self.app.fonts["small"],
                     text_color=TEXT_MUTED).pack(pady=(6, 0))
        ctk.CTkLabel(card, text=self.app.t("stage_hint"),
                     font=FONTS.get("tiny"),
                     text_color=TEXT_MUTED).pack(pady=(16, 0))

        self._anim(tr.dissolve_in(card, tr.resolve_color(STAGE),
                                  duration=BALL_OPEN_MS / self._speed,
                                  on_done=lambda: self._reveal(entry, 0)))

    def _reveal(self, entry, position):
        """The opponents settle in one after the other."""
        if self._phase != "ceremony":
            return
        if position >= len(entry["opponents"]):
            self._step_later(CLUB_HOLD_MS, self._next_club)
            return

        row = entry["opponents"][position]
        parent = self.sides["home" if row["home"] else "away"]
        card = OpponentCard(parent, self.comp, row["club"], row["pot"],
                            row["home"], self.app.accent,
                            logo_path=self.model.logo_for(row["club"]))
        card.pack(pady=3, fill="x")

        if row["fresh"]:
            # A genuinely new one: it arrives with a fade, and we mark
            # time before the next.
            self._anim(tr.dissolve_in(card, tr.resolve_color(STAGE),
                                      duration=OPPONENT_MS / self._speed))
            self._step_later(OPPONENT_MS + OPPONENT_GAP_MS,
                             lambda: self._reveal(entry, position + 1))
        else:
            # Already known from a previous pot: placed without ceremony.
            card.configure(fg_color=CHIP_DRAWN)
            self._reveal(entry, position + 1)

    def _next_club(self):
        self._index += 1
        self._run_club()

    # =================================================================
    #  STATE 5: THE RESULTS
    # =================================================================
    def _build_results(self, parent):
        matches = sum(len(day) for day in self.matchdays)
        self._header(parent, "results_q", compact=True, hint_text=self.app.t(
            "results_h").format(matches=matches, days=len(self.matchdays)))

        footer = ctk.CTkFrame(parent, fg_color="transparent")
        footer.pack(side="bottom", pady=(8, 16))
        # In full simulation, the main button is no longer "draw again"
        # but "simulate": the draw was only the first half of the
        # journey. "Draw again" stays, as a secondary button.
        if self.app.mode == "simulate":
            ctk.CTkButton(footer, text=self.app.t("simulate_btn"), width=200,
                          height=40, corner_radius=11,
                          font=self.app.fonts["cta"], text_color="#FFFFFF",
                          fg_color=self.app.accent,
                          hover_color=self.app.accent_hover,
                          command=self._to_simulation).pack(side="left", padx=6)
            again = ghost_button(footer, command=lambda: self._go("choice"),
                                 width=170)
            again.configure(text=self.app.t("draw_again"))
        else:
            again = ctk.CTkButton(footer, text=self.app.t("draw_again"), width=170,
                                  height=40, corner_radius=11,
                                  font=self.app.fonts["cta"], text_color="#FFFFFF",
                                  fg_color=self.app.accent,
                                  hover_color=self.app.accent_hover,
                                  command=lambda: self._go("choice"))
        again.pack(side="left", padx=6)
        menu = ghost_button(footer, command=lambda: self.app.back("mode"),
                            width=170)
        menu.configure(text=self.app.t("to_menu"))
        menu.pack(side="left", padx=6)

        self.tabs = ctk.CTkSegmentedButton(
            parent, values=[self.app.t("tab_matchdays"),
                            self.app.t("tab_clubs")],
            font=self.app.fonts["small"], selected_color=self.app.accent,
            selected_hover_color=self.app.accent_hover,
            command=self._switch_tab)
        self.tabs.pack(pady=(0, 10))
        self.tabs.set(self.app.t("tab_matchdays"))

        self.day_bar = ctk.CTkFrame(parent, fg_color="transparent")
        self.day_bar.pack(pady=(0, 10))
        self.day_btns = {}
        for number in range(1, len(self.matchdays) + 1):
            button = ctk.CTkButton(
                self.day_bar, text=self.app.t("md_short").format(i=number),
                width=48, height=30, corner_radius=8, font=FONTS.get("tiny"),
                command=lambda n=number: self._show_day(n))
            button.pack(side="left", padx=3)
            self.day_btns[number] = button

        self.results_body = ctk.CTkScrollableFrame(parent,
                                                   fg_color="transparent")
        self.results_body.pack(fill="both", expand=True, padx=20)
        self._show_day(1)

    def _switch_tab(self, value):
        """
        Shows or hides the row of matchdays, above the list.

        We place the TWO blocks again in order rather than use pack()'s
        before= option. CustomTkinter trap: a CTkScrollableFrame is not
        itself packed in its parent, it places an internal canvas there.
        before=self.results_body therefore points at a widget that the
        parent does not know, and Tk answers "window ... isn't packed".
        Detaching then reattaching in the right order does not depend on
        any implementation detail.
        """
        self.day_bar.pack_forget()
        self.results_body.pack_forget()
        matchdays = value == self.app.t("tab_matchdays")
        if matchdays:
            self.day_bar.pack(pady=(0, 10))
        self.results_body.pack(fill="both", expand=True, padx=20)
        if matchdays:
            self._show_day(1)
        else:
            self._show_clubs()

    # ---------- building in slices ----------
    def _chunk(self, items, render, size=6):
        """
        Puts `items` on screen in small batches, not in one block.

        A matchday is eighteen fixtures; the "by club" tab is thirty-six
        blocks. Building everything in the click handler freezes the
        window for as long as it takes: a measured second and a half for
        "by club". Here the first slice goes out straight away and the
        following ones are slotted in between two frames, so the list
        fills up before the user's eyes instead of making them wait.

        The token avoids a race: if another matchday is clicked while a
        list is filling up, _clear_results() increments the token and the
        late slice finds itself out of date, so it stops.
        """
        token = self._chunk_token

        def step(start):
            if token != self._chunk_token or self._phase != "results":
                return
            for item in items[start:start + size]:
                render(item)
            if start + size < len(items):
                self._later(1, lambda: step(start + size))

        step(0)

    def _clear_results(self):
        self._chunk_token += 1         # makes any slice still in flight stale
        for child in self.results_body.winfo_children():
            child.destroy()

    def _show_day(self, number):
        self._clear_results()
        for value, button in self.day_btns.items():
            chosen = value == number
            button.configure(
                fg_color=self.app.accent if chosen else "transparent",
                hover_color=self.app.accent_hover if chosen else SURFACE_2,
                border_width=0 if chosen else 1, border_color=BORDER,
                text_color="#FFFFFF" if chosen else TEXT_MUTED)

        ctk.CTkLabel(self.results_body,
                     text=self.app.t("matchday_n").format(i=number),
                     font=self.app.fonts["h2"], text_color=TEXT).pack(
                         pady=(4, 10))

        grid = flat_frame(self.results_body, SURFACE)
        grid.pack()
        day = sorted(self.matchdays[number - 1])
        half = (len(day) + 1) // 2
        columns = []
        for _ in range(2):
            column = flat_frame(grid, SURFACE)
            column.pack(side="left", padx=8, anchor="n")
            columns.append(column)

        def row(entry):
            index, (home, away) = entry
            MatchRow(columns[0 if index < half else 1], self.comp, home, away,
                     self.app.accent, home_logo=self.model.logo_for(home),
                     away_logo=self.model.logo_for(away)).pack(pady=3)

        # size=4: a fixture keeps a CustomTkinter shell for its rounded
        # corners, so it costs more than a line of text. Four per slice
        # keeps the blocking under fifty milliseconds, the threshold below
        # which a click feels instantaneous.
        self._chunk(list(enumerate(day)), row, size=4)

    def _show_clubs(self):
        self._clear_results()
        seen_pots = set()

        def block(entry):
            pot_number, club, rows = entry
            if pot_number not in seen_pots:
                seen_pots.add(pot_number)
                ctk.CTkLabel(self.results_body,
                             text=self.app.t("pot_n", n=pot_number),
                             font=self.app.fonts["h2"],
                             text_color=TEXT).pack(anchor="w", pady=(14, 8))

            # Thirty-six blocks, eight widgets each: in CustomTkinter this
            # meant a second of waiting for a list of text. Here everything
            # is plain Tk: no rounded corners, but at this density a flat
            # list reads better than a pile of cards, and it appears a
            # hundred times faster.
            card = flat_frame(self.results_body, CARD)
            card.pack(fill="x", pady=2)
            flat_label(card, "  " + club, CARD, TEXT, FONTS.get("h2"),
                       anchor="w",
                       photo=club_photo(self.comp, club, 22, self.app.accent,
                                        self.model.logo_for(club))).pack(
                           anchor="w", padx=10, pady=(8, 2))

            for home in (True, False):
                names = ", ".join(f"{other} (P{pot})"
                                  for other, pot, side in rows if side is home)
                line = flat_frame(card, CARD)
                line.pack(fill="x", padx=10, pady=(0, 6))
                flat_label(line, self.app.t("home" if home else "away"), CARD,
                           HOME if home else AWAY, FONTS.get("tiny"),
                           width=9, anchor="w").pack(side="left")
                flat_label(line, names, CARD, TEXT_MUTED, FONTS.get("small"),
                           anchor="w", justify="left").pack(
                               side="left", fill="x", expand=True)

        # size=4 rather than 6: a "by club" block costs more than a
        # fixture, so the slice is shortened to hold the same time budget
        # between two frames.
        self._chunk(fixtures_by_club(self.teams, self.model.pots), block,
                    size=4)

    # =================================================================
    #  FALLBACK STATE: THE DRAW FAILED
    # =================================================================
    def _build_failed(self, parent):
        middle = ctk.CTkFrame(parent, fg_color="transparent")
        middle.pack(expand=True)
        ctk.CTkLabel(middle, text=self.app.t("draw_failed"),
                     font=self.app.fonts["title"], text_color=TEXT).pack()
        # The exception's raw message, not a rewording: when a replaced
        # club has no valid association, or a CSV has moved, that line is
        # what says where to look.
        ctk.CTkLabel(middle, text=str(self._error or "")[:300],
                     font=self.app.fonts["small"], text_color=TEXT_MUTED,
                     wraplength=620, justify="center").pack(pady=(14, 22))
        retry = ctk.CTkButton(middle, text=self.app.t("retry"), width=170,
                              height=42, corner_radius=11,
                              font=self.app.fonts["cta"], text_color="#FFFFFF",
                              fg_color=self.app.accent,
                              hover_color=self.app.accent_hover,
                              command=lambda: self._go("pots"))
        retry.pack()
        back = ghost_button(middle, command=lambda: self.app.back("mode"))
        back.configure(text=self.app.t("to_menu"))
        back.pack(pady=14)

from sim_view import SimulateView                            # noqa: E402

# The catalogue that main.py reads to register the screens. The order
# matters: it is the order of the journey, and the first name is the
# starting screen. Adding a screen = adding a line here.
VIEW_REGISTRY = (
    ("language", LanguageView),
    ("competition", CompetitionView),
    ("mode", ModeView),
    ("draw", DrawView),
    ("simulation", SimulateView),
)
