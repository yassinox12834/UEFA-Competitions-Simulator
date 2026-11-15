"""
sim_view.py - the simulation screen: from the draw to the final.

A single screen, four states, like DrawView:

    setup     the settings: two-legged method, expert mode, Monte
              Carlo, seed
    working   the engine runs on another thread (SimJob), progress bar
              for the Monte Carlo
    results   a "winner" banner, then four tabs: standings, knockout
              bracket, probabilities, expert log
    failed    the raw error message, and "try again"

The screen computes nothing: it reads self.app.draw_result, set by
DrawView when the user clicks "Simulate the season", and passes the lot
to SimJob. Everything displayed comes from a SimulationResult.

Density rule: the standings, the probabilities and the knockout bracket
are drawn on a Canvas (canvas_views.py), one single widget each; the
expert log, several thousand lines, is a tkinter.Text. None of the four
builds one widget per cell.
"""

import time
import tkinter

import customtkinter as ctk

import transition as tr
from base_view import BaseView, SliceBuild, is_sliced
from canvas_views import BracketView, LeagueTable, ProbTable, draw_shootout
from config import (USER_DIR, BORDER, CARD, GOLD, MC_RUNS, SURFACE_2,
                    TEXT, TEXT_FAINT, TEXT_MUTED, ZONE_OUT, ZONE_PO, ZONE_R16)
from draw_widgets import MessageDialog, flat_frame
from fonts import FONTS, scaling, tk_font
from images import club_image, comp_image, method_image, trophy_image
from sim_engine import (DEFAULT_METHOD, DEFAULT_RUNS, METHODS, STAGES,
                        SimJob, error_text, resources, save_log)
from widgets import card_button, ghost_button

ROUNDS = ("playoff", "r16", "qf", "sf", "final")
BIG_RUNS = 2000            # from here on, the Monte Carlo uses every core


class SimulateView(BaseView):

    # ---------- construction ----------
    def build(self):
        self.body.pack_configure(fill="both", expand=True)
        self.host = ctk.CTkFrame(self.body, fg_color="transparent")
        self.host.pack(fill="both", expand=True)

        self.comp = None
        self.teams = None
        self.matchdays = None
        self.pots_model = None          # for replaced badges
        self.result = None
        self.mc = None
        self.job = None

        self._phase = None
        self._panel = None
        self._slicing = None            # a SliceBuild of the shown screen in progress
        # The settings panel is kept between visits and built in advance
        # (see prewarm): it depends only on the competition and the language.
        self._setup_panel = None
        self._setup_key = None
        self._warm_job = None
        self._jobs = set()
        self._anims = []
        self._error = None
        self._tab = "table"
        self._t0 = 0.0
        self._shown_progress = None

        # The settings survive from one run to the next.
        self.method = DEFAULT_METHOD
        self.expert = True
        self.poisson = False            # goal model: False = table of real scores
        self.runs = DEFAULT_RUNS
        self.seed_text = ""

    def blocks(self):
        return [self.host]

    # ---------- life cycle ----------
    def on_show(self):
        handoff = getattr(self.app, "draw_result", None)
        if handoff is None:
            self._go("failed", force=True,
                     error="No draw to simulate: run the draw first.")
            return
        comp, teams, matchdays, pots_model = handoff
        same = (comp == self.comp and teams is self.teams
                and matchdays is self.matchdays)
        self.comp, self.teams = comp, teams
        self.matchdays, self.pots_model = matchdays, pots_model
        if not same:
            self.result = self.mc = None       # another draw: everything is out of date
        self._phase = None
        self._go("results" if self.result is not None else "setup")

    def on_hide(self):
        self._cancel_all()
        if self.job is not None:
            self.job.cancel()

    def refresh_text(self):
        if self._phase in ("setup", "results", "failed"):
            self._go(self._phase, force=True)
        else:
            self._drop_setup()           # the kept settings are in the old language

    def on_theme_change(self):
        """Only the results hold plain Tk canvases, whose colours are fixed
        when drawn. Settings, progress and error panels are CustomTkinter,
        which repaints itself: rebuilding them (the old behaviour, through
        refresh_text) cost about 190 ms per switch on the settings."""
        if self._phase == "results":
            self._go("results", force=True)

    def on_back(self):
        if self._phase == "results":
            self._go("setup")
        elif self._phase == "working":
            pass
        else:
            self.app.back("draw")

    def on_enter(self):
        if self._phase == "setup":
            self._launch()

    # ---------- timers ----------
    def _later(self, ms, fn):
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
        job, self._slicing = self._slicing, None
        if job is not None:
            job.cancel()
            if job.panel.winfo_exists():
                job.panel.destroy()

    # ---------- the settings panel, kept and built in advance ----------
    def _setup_key_now(self):
        return (self.app.comp, self.app.lang)

    def _drop_setup(self):
        job, self._warm_job = self._warm_job, None
        if job is not None:
            job.cancel()
        panel, self._setup_panel = self._setup_panel, None
        self._setup_key = None
        if panel is not None:
            if panel is self._panel:
                self._panel = None
            if panel.winfo_exists():
                panel.destroy()

    def prewarm(self):
        """Builds the settings panel BEFORE the screen is shown.

        App calls this once the draw results are on screen in full
        simulation. The settings used to cost about 190 ms, spent in the
        click on "Simulate the season" before the slide could even start;
        built here, in slices, while the user reads the fixtures, the click
        answers at once.
        """
        panel = self._setup_panel
        if (panel is not None and panel.winfo_exists()
                and self._setup_key == self._setup_key_now()):
            return                       # already built, or being built
        self._drop_setup()
        panel = ctk.CTkFrame(self.host, fg_color="transparent")
        self._setup_panel, self._setup_key = panel, self._setup_key_now()
        def done():
            if self._warm_job is job:
                self._warm_job = None

        def failed(_exc):
            if self._warm_job is job:
                self._drop_setup()

        job = SliceBuild(self, self._build_setup(panel), done, failed)
        self._warm_job = job
        job.start()

    def _take_setup(self):
        """The kept settings panel if it can be shown as it is, else None."""
        if self._warm_job is not None:
            job, self._warm_job = self._warm_job, None
            job.finish_now()             # still filling: finish it now
        panel = self._setup_panel
        if (panel is None or not panel.winfo_exists()
                or self._setup_key != self._setup_key_now()):
            self._drop_setup()
            return None
        # "Simulate again" clears the seed (_launch_again). The kept entry
        # would still show the old one: rebuild rather than lie.
        try:
            shown = self.seed_entry.get().strip()
        except (AttributeError, tkinter.TclError):
            shown = None
        if shown != self.seed_text:
            self._drop_setup()
            return None
        return panel

    # ---------- internal router ----------
    # Built in slices (generators, see base_view.SliceBuild): the panel
    # being left stays on screen, alive, until the new one is complete. The
    # results used to cost about 200 ms in one callback, with the progress
    # bar frozen at 100 %.
    SLICED = ("setup", "results")

    def _go(self, phase, force=False, error=None):
        if phase == self._phase and not force:
            return
        self._cancel_all()
        self._phase = phase
        self._error = error

        if phase == "setup":
            if force:
                self._drop_setup()       # texts or colours have changed
            panel = self._take_setup()
            if panel is not None:
                self._swap_to(panel, phase, fresh=False)
                return

        builder = {"setup": self._build_setup,
                   "working": self._build_working,
                   "results": self._build_results,
                   "failed": self._build_failed}[phase]
        panel = ctk.CTkFrame(self.host, fg_color="transparent")
        built = builder(panel)
        if not is_sliced(built):
            self._swap_to(panel, phase, fresh=True)
            return

        def done():
            if self._slicing is job:
                self._slicing = None
                self._swap_to(panel, phase, fresh=True)

        def failed(exc):
            if self._slicing is not job:
                return
            self._slicing = None
            if panel.winfo_exists():
                panel.destroy()
            if phase == "setup":
                self._setup_panel = None
            self._go("failed", force=True, error=error_text(exc))

        job = SliceBuild(self, built, done, failed)
        job.panel = panel
        self._slicing = job
        # Entering the screen: the slide needs the finished panel, and
        # nothing of the old one is visible anyway.
        if self.app.sliding:
            job.finish_now()
        else:
            job.start()

    def _swap_to(self, panel, phase, fresh):
        old = self._panel
        if old is not None and old is not panel and old.winfo_exists():
            if old is self._setup_panel:
                old.pack_forget()        # kept for the next visit
            else:
                old.destroy()
        panel.pack(fill="both", expand=True)
        self._panel = panel
        if phase == "setup":
            self._setup_panel, self._setup_key = panel, self._setup_key_now()
        # No fade on "working": the simulation thread holds the GIL there,
        # which makes each fade frame 10 times slower (see DrawView._go).
        # None on a kept panel (its colours are already right) and none
        # while the whole screen slides in (the slide is the entrance).
        if fresh and phase != "working" and not self.app.sliding:
            self._anim(tr.dissolve_in(panel, self.app.surface_hex(), duration=200))

    # ---------- small factories ----------
    def _header(self, parent, question_key, hint_text=None):
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.pack(pady=(18, 14))
        ctk.CTkLabel(wrap, text=self.app.t(question_key),
                     font=self.app.fonts["title"], text_color=TEXT).pack()
        if hint_text:
            ctk.CTkLabel(wrap, text=hint_text, font=self.app.fonts["body"],
                         text_color=TEXT_MUTED, wraplength=760,
                         justify="center").pack(pady=(6, 0))
        return wrap

    def _primary(self, parent, key, command, width=180, height=40):
        return ctk.CTkButton(parent, text=self.app.t(key), width=width, height=height,
                             corner_radius=10, font=self.app.fonts["cta"],
                             text_color="#FFFFFF", fg_color=self.app.accent,
                             hover_color=self.app.accent_hover, command=command)

    def _ghost(self, parent, key, command, width=130):
        button = ghost_button(parent, command=command, width=width)
        button.configure(text=self.app.t(key))
        return button

    def _card(self, parent, **kw):
        return ctk.CTkFrame(parent, fg_color=CARD, corner_radius=16,
                            border_width=1, border_color=BORDER, **kw)

    def _runs_label(self, n):
        if n == 0:
            return self.app.t("sim_runs_0")
        sep = " " if self.app.lang == "fr" else ","
        return self.app.t("sim_runs_n", n=f"{n:,}".replace(",", sep))

    # =================================================================
    #  STATE 1: THE SETTINGS
    # =================================================================
    def _build_setup(self, parent):
        # A generator: each bare `yield` is a cut point (see SLICED).
        self._header(parent, "sim_setup_q", self.app.t("sim_setup_h"))

        footer = ctk.CTkFrame(parent, fg_color="transparent")
        footer.pack(side="bottom", pady=(8, 16))
        row = ctk.CTkFrame(footer, fg_color="transparent")
        row.pack()
        self._ghost(row, "back", lambda: self.app.back("draw")).pack(side="left", padx=6)
        self._primary(row, "sim_run", self._launch, width=200, height=42).pack(
            side="left", padx=6)
        self.model_line = ctk.CTkLabel(footer, text="", font=FONTS.get("tiny"),
                                       text_color=TEXT_FAINT, wraplength=820)
        self.model_line.pack(pady=(10, 0))
        self._describe_model()
        yield

        # --- the two-legged method: three cards with an icon ---
        ctk.CTkLabel(parent, text=self.app.t("sim_method").upper(),
                     font=self.app.fonts["overline"], text_color=TEXT_MUTED).pack(
                         pady=(0, 8))
        cards_row = ctk.CTkFrame(parent, fg_color="transparent")
        cards_row.pack()
        self.method_cards = {}
        for method in METHODS:
            card = card_button(cards_row, title=self.app.t("sim_m_" + method),
                               subtitle=self.app.t("sim_m_" + method + "_d"),
                               image=method_image(method, self.app.accent),
                               width=292, height=196, accent=self.app.accent,
                               command=lambda m=method: self._pick_method(m))
            card.pack(side="left", padx=7)
            if method == DEFAULT_METHOD:
                tag = ctk.CTkLabel(card, text=self.app.t("sim_default_tag"),
                                   font=self.app.fonts["overline"],
                                   text_color=self.app.accent, fg_color=SURFACE_2,
                                   corner_radius=8, height=20)
                tag.place(relx=1.0, x=-12, y=12, anchor="ne")
                tag.bind("<Button-1>", lambda _e, m=method: self._pick_method(m))
            self.method_cards[method] = card
            yield
        self._paint_methods()
        yield

        # --- expert, Monte Carlo, seed: a label / control / help grid ---
        box = self._card(parent)
        box.pack(pady=(18, 0), padx=40, fill="x")
        grid = ctk.CTkFrame(box, fg_color="transparent")
        grid.pack(fill="x", padx=20, pady=14)
        grid.grid_columnconfigure(2, weight=1)

        def label(r, key):
            ctk.CTkLabel(grid, text=self.app.t(key), font=self.app.fonts["body_b"],
                         text_color=TEXT, anchor="w").grid(
                             row=r, column=0, sticky="w", pady=7, padx=(0, 18))

        def hint(r, text):
            lab = ctk.CTkLabel(grid, text=text, font=FONTS.get("small"),
                               text_color=TEXT_MUTED, anchor="w", justify="left",
                               wraplength=420)
            lab.grid(row=r, column=2, sticky="w", padx=(16, 0))
            return lab

        label(0, "sim_expert_short")
        self.expert_switch = ctk.CTkSwitch(grid, text="", width=46,
                                           progress_color=self.app.accent,
                                           command=self._toggle_expert)
        self.expert_switch.grid(row=0, column=1, sticky="w")
        if self.expert:
            self.expert_switch.select()
        hint(0, self.app.t("sim_expert_h"))
        yield

        label(1, "sim_runs")
        self.run_labels = {self._runs_label(n): n for n in MC_RUNS}
        self.runs_seg = ctk.CTkSegmentedButton(
            grid, values=list(self.run_labels), font=self.app.fonts["small"],
            height=32, selected_color=self.app.accent,
            selected_hover_color=self.app.accent_hover, command=self._pick_runs)
        self.runs_seg.grid(row=1, column=1, sticky="w")
        self.runs_seg.set(self._runs_label(self.runs if self.runs in MC_RUNS else 0))
        self.runs_hint = hint(1, "")
        self._paint_runs_hint()
        yield

        label(2, "sim_seed")
        self.seed_entry = ctk.CTkEntry(grid, width=180, height=32,
                                       font=self.app.fonts["small"],
                                       placeholder_text="42")
        self.seed_entry.grid(row=2, column=1, sticky="w")
        if self.seed_text:
            self.seed_entry.insert(0, self.seed_text)
        hint(2, self.app.t("sim_seed_h"))
        yield

        label(3, "sim_goals_short")
        self.goals_switch = ctk.CTkSwitch(grid, text="", width=46,
                                          progress_color=self.app.accent,
                                          command=self._toggle_goals)
        self.goals_switch.grid(row=3, column=1, sticky="w")
        if self.poisson:
            self.goals_switch.select()
        self.goals_hint = hint(3, "")
        self._paint_goals_hint()

    def _describe_model(self):
        try:
            model = resources().model
        except Exception as exc:                 # weights missing, broken JSON
            self.model_line.configure(text=error_text(exc), text_color="#E5484D")
            return
        hold = model.meta.get("holdout") or {}
        self.model_line.configure(text=self.app.t(
            "sim_model_line", rows=model.meta.get("rows"),
            seasons=model.meta.get("seasons"), ll=hold.get("log_loss", 0.0),
            ns=hold.get("log_loss_no_skill", 0.0)))

    def _pick_method(self, method):
        self.method = method
        self._paint_methods()
        self._paint_goals_hint()

    def _paint_methods(self):
        for method, card in self.method_cards.items():
            card.set_accent(self.app.accent)
            card.set_selected(method == self.method)

    def _toggle_expert(self):
        self.expert = bool(self.expert_switch.get())

    def _toggle_goals(self):
        self.poisson = bool(self.goals_switch.get())

    def _paint_goals_hint(self):
        """What the goal model changes depends on how two-legged ties are settled."""
        self.goals_hint.configure(text=self.app.t("sim_goals_h") + " "
                                       + self.app.t("sim_goals_" + self.method))

    def _pick_runs(self, label):
        self.runs = self.run_labels.get(label, 0)
        self._paint_runs_hint()

    def _paint_runs_hint(self):
        text = self.app.t("sim_runs_h")
        if self.runs >= BIG_RUNS:
            text += " " + self.app.t("sim_runs_big")
        self.runs_hint.configure(text=text)

    # =================================================================
    #  STATE 2: THE ENGINE IS RUNNING
    # =================================================================
    def _launch(self, seed_text=None):
        if seed_text is None:
            seed_text = (self.seed_entry.get().strip()
                         if getattr(self, "seed_entry", None) is not None
                         and self.seed_entry.winfo_exists() else self.seed_text)
        self.seed_text = seed_text
        seed = None
        if self.seed_text:
            # An integer stays an integer (readable in the log), anything
            # else is passed as it is: random.Random accepts a string.
            try:
                seed = int(self.seed_text)
            except ValueError:
                seed = self.seed_text
        self.job = SimJob(self.comp, self.teams, self.matchdays,
                          method=self.method, expert=self.expert,
                          runs=self.runs, seed=seed,
                          goals="poisson" if self.poisson else "table")
        # Screen FIRST, thread SECOND. The worker is pure Python and holds
        # the GIL; while it runs, every Tk call made by this thread waits
        # for the lock (up to 5 ms each). Tearing down the settings panel
        # with the simulation already running took about 0.8 s instead of
        # about 0.1 s. The short delay below lets Tk paint the "working" panel
        # before the competition for the lock begins.
        self._go("working")
        job = self.job

        def begin():
            if self.job is job and self._phase == "working":
                self._t0 = time.perf_counter()
                self._shown_progress = None
                job.start()
                self._poll_job()

        # Tracked timer: leaving the screen before it fires cancels it
        # (_cancel_all), so no thread is started for a screen nobody sees.
        self._later(1, begin)

    def _launch_again(self):
        self._launch(seed_text="")             # a new season, not the same one

    def _build_working(self, parent):
        middle = ctk.CTkFrame(parent, fg_color="transparent")
        middle.pack(expand=True)
        ctk.CTkLabel(middle, text="", image=comp_image(self.comp, box=(84, 84),
                                                       plate="#FFFFFF")).pack()
        ctk.CTkLabel(middle, text=self.app.t("simulating"),
                     font=self.app.fonts["h1"], text_color=TEXT).pack(pady=(20, 14))
        self.bar = ctk.CTkProgressBar(middle, width=360, height=8,
                                      progress_color=self.app.accent)
        self.bar.pack()
        if self.runs:
            self.bar.set(0)
        else:
            self.bar.configure(mode="indeterminate")
            self.bar.start()
        self.progress_label = ctk.CTkLabel(middle, text="", font=self.app.fonts["small"],
                                           text_color=TEXT_MUTED)
        self.progress_label.pack(pady=(12, 0))
        self.rate_label = ctk.CTkLabel(middle, text="", font=FONTS.get("tiny"),
                                       text_color=TEXT_FAINT)
        self.rate_label.pack(pady=(2, 0))

    def _poll_job(self):
        answer = self.job.poll() if self.job else None
        if answer is None:
            done, total = self.job.progress()
            # Redraw only what changed, and at most every 100 ms: each
            # configure() redraws a CustomTkinter canvas, and each Tk call
            # is slow while the worker thread holds the GIL.
            if total and self._phase == "working" and (done, total) != self._shown_progress:
                self._shown_progress = (done, total)
                self.bar.set(done / total)
                self.progress_label.configure(
                    text=self.app.t("sim_mc_progress", i=f"{done:,}", n=f"{total:,}"))
                elapsed = time.perf_counter() - self._t0
                if done and elapsed > 0.2:
                    self.rate_label.configure(
                        text=self.app.t("sim_mc_rate", rate=done / elapsed))
            self._later(100, self._poll_job)
            return
        if answer[0] == "error":
            self._go("failed", error=error_text(answer[1]))
            return
        self.result, self.mc = answer[1], answer[2]
        self._go("results")

    # =================================================================
    #  STATE 3: THE RESULTS
    # =================================================================
    def _build_results(self, parent):
        # A generator: each bare `yield` is a cut point (see SLICED).
        yield from self._hero(parent)
        yield

        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.pack(fill="x", padx=24, pady=(10, 6))
        self.tab_keys = {"table": self.app.t("tab_table"),
                         "knockout": self.app.t("tab_knockout"),
                         "probs": self.app.t("tab_probs"),
                         "expert": self.app.t("tab_expert")}
        self.tabs = ctk.CTkSegmentedButton(
            bar, values=list(self.tab_keys.values()), font=self.app.fonts["body_b"],
            height=34, selected_color=self.app.accent,
            selected_hover_color=self.app.accent_hover, command=self._switch_tab)
        self.tabs.pack(side="left")

        self._ghost(bar, "to_menu", lambda: self.app.back("mode"), width=120).pack(
            side="right", padx=(6, 0))
        self._ghost(bar, "sim_save", self._save, width=150).pack(side="right", padx=6)
        self._ghost(bar, "sim_settings", lambda: self._go("setup"), width=110).pack(
            side="right", padx=6)
        self._primary(bar, "sim_again", self._launch_again, width=130, height=38).pack(
            side="right", padx=6)
        yield

        self.tab_host = ctk.CTkFrame(parent, fg_color="transparent")
        self.tab_host.pack(fill="both", expand=True, padx=24, pady=(0, 14))
        if self._tab not in self.tab_keys:
            self._tab = "table"
        self.tabs.set(self.tab_keys[self._tab])
        yield from self._show_steps(self._tab)

    def _hero(self, parent):
        """The winner banner: cup, badge, name, the final, the figures.

        Deliberately low (a single row): on a laptop, every pixel taken
        here is one pixel less for the knockout bracket.
        """
        # A generator, driven by _build_results.
        r = self.result
        final = r.rounds["final"][0]
        hero = self._card(parent)
        hero.pack(fill="x", padx=24, pady=(12, 0))
        hero.configure(border_color=GOLD)
        inner = ctk.CTkFrame(hero, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=8)

        ctk.CTkLabel(inner, text="", image=trophy_image(tr.resolve_color(GOLD),
                                                        box=(34, 34))).pack(side="left")
        ctk.CTkLabel(inner, text="", image=club_image(
            self.comp, r.champion, box=(48, 48), accent=self.app.accent,
            custom_path=self._logo(r.champion), plate=None)).pack(side="left", padx=(8, 12))

        titles = ctk.CTkFrame(inner, fg_color="transparent")
        titles.pack(side="left")
        ctk.CTkLabel(titles, text=self.app.t("sim_champion_over",
                                             comp=self.app.t(self.comp).upper()),
                     font=self.app.fonts["overline"], text_color=GOLD,
                     height=14).pack(anchor="w")
        ctk.CTkLabel(titles, text=r.champion, font=self.app.fonts["display"],
                     text_color=TEXT, height=34).pack(anchor="w")
        ctk.CTkLabel(titles, text=self._final_line(final), height=16,
                     font=self.app.fonts["small"], text_color=TEXT_MUTED).pack(anchor="w")
        yield

        stats = ctk.CTkFrame(inner, fg_color="transparent")
        stats.pack(side="right")
        matches = sum(len(day) for day in r.league) + sum(
            len(tie.legs) for stage in ROUNDS for tie in r.rounds[stage])
        ms = r.elapsed * 1000
        seed = r.config.seed
        seed_text = f"{seed:.6f}" if isinstance(seed, float) else str(seed)
        items = (("stat_matches", str(matches)),
                 ("stat_time", f"{ms:.0f} ms" if ms >= 1 else "<1 ms"),
                 ("stat_method", self.app.t("sim_m_" + r.config.method)),
                 ("stat_seed", seed_text))
        for i, (key, value) in enumerate(items):
            chip = ctk.CTkFrame(stats, fg_color=SURFACE_2, corner_radius=8)
            chip.grid(row=i // 2, column=i % 2, padx=3, pady=2, sticky="ew")
            ctk.CTkLabel(chip, text=self.app.t(key).upper(), font=self.app.fonts["overline"],
                         text_color=TEXT_FAINT, height=24).pack(side="left", padx=(10, 8))
            ctk.CTkLabel(chip, text=value, font=self.app.fonts["small_b"],
                         text_color=TEXT, height=24).pack(side="right", padx=(0, 10))
            yield

    def _final_line(self, final):
        m = final.legs[0]
        w, loser = final.winner, final.loser
        gw = m.home_goals if m.home == w else m.away_goals
        gl = m.away_goals if m.home == w else m.home_goals
        text = self.app.t("sim_final_line", opp=loser, score=f"{gw}-{gl}")
        if final.extra_time:
            ew = final.extra_time[0] if w == final.a else final.extra_time[1]
            el = final.extra_time[1] if w == final.a else final.extra_time[0]
            text = self.app.t("sim_final_line", opp=loser,
                              score=f"{gw + ew}-{gl + el}") + self.app.t("sim_final_aet")
        if final.pens_won:
            text += self.app.t("sim_final_pens", a=final.pens_won[0], b=final.pens_won[1])
        return text

    def _logo(self, club):
        return self.pots_model.logo_for(club) if self.pots_model else None

    def _switch_tab(self, value):
        for key, label in self.tab_keys.items():
            if label == value:
                self._show(key)
                return

    def _show(self, key):
        for _ in self._show_steps(key):
            pass

    def _show_steps(self, key):
        """_show() as a generator, so the results build can slice it."""
        self._tab = key
        for child in self.tab_host.winfo_children():
            child.destroy()
        built = {"table": self._show_table, "knockout": self._show_knockout,
                 "probs": self._show_probs, "expert": self._show_expert}[key]()
        if is_sliced(built):
            yield from built

    def _legend(self, parent, items):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 8))
        for text, colour in items:
            if colour is None:
                ctk.CTkLabel(row, text=text, font=FONTS.get("small"),
                             text_color=TEXT_MUTED).pack(side="left")
                continue
            ctk.CTkFrame(row, width=10, height=10, corner_radius=3,
                         fg_color=colour).pack(side="left", padx=(0, 6))
            ctk.CTkLabel(row, text=text, font=FONTS.get("small"),
                         text_color=TEXT_MUTED).pack(side="left", padx=(0, 18))
        return row

    # ---------- tab 1: the standings ----------
    def _show_table(self):
        self._legend(self.tab_host, ((self.app.t("zone_r16"), ZONE_R16),
                                     (self.app.t("zone_po"), ZONE_PO),
                                     (self.app.t("zone_out"), ZONE_OUT)))
        yield
        LeagueTable(self.tab_host, self.app, self, self.result).pack(
            fill="both", expand=True)

    # ---------- tab 2: the knockout bracket ----------
    def _show_knockout(self):
        self._legend(self.tab_host, ((self.app.t("ko_hint"), None),))
        # The detail is placed BEFORE the bracket (at the bottom): same
        # reason as ScrollCanvas's horizontal bar, the bracket takes
        # whatever is left.
        self.detail = self._card(self.tab_host, height=128)
        self.detail.pack(side="bottom", fill="x", pady=(10, 0))
        self.detail.pack_propagate(False)
        self.bracket = BracketView(self.tab_host, self.app, self, self.result,
                                   on_select=self._show_tie)
        self.bracket.pack(fill="both", expand=True)
        self._show_tie(self.result.rounds["final"][0])
        self._later(80, self.bracket.focus_final)

    def _show_tie(self, tie):
        for child in self.detail.winfo_children():
            child.destroy()
        t = self.app.t
        s = scaling(self)
        bg = tr.resolve_color(CARD)
        cv = tkinter.Canvas(self.detail, bg=bg, highlightthickness=0, bd=0)
        cv.pack(fill="both", expand=True, padx=2, pady=2)
        self.detail.update_idletasks()

        title_f = tk_font(self, 15, "bold")
        body_f = tk_font(self, 12)
        bold_f = tk_font(self, 12, "bold")
        over_f = tk_font(self, 10, "bold")
        pad = int(18 * s)
        width = max(self.detail.winfo_width(), int(900 * s))
        so = tie.shootout

        # Column 1: the round and the verdict.
        y = int(16 * s)
        cv.create_text(pad, y, anchor="nw", text=t("ko_" + tie.stage).upper(),
                       font=over_f, fill=tr.resolve_color(TEXT_FAINT))
        headline = (t("tie_champions", club=tie.winner) if tie.method == "final"
                    else t("tie_through", club=tie.winner))
        cv.create_text(pad, y + int(18 * s), anchor="nw", text=headline, font=title_f,
                       width=int(230 * s),
                       fill=tr.resolve_color(GOLD if tie.method == "final" else TEXT))

        # Column 2: the matches, line by line.
        lines = []
        if tie.method == "oneshot":
            lines.append(("P", t("tie_oneshot", club=tie.a, p=tie.p_advance)))
        elif tie.method == "final":
            m = tie.legs[0]
            lines.append((t("tie_final"), f"{m.home} {m.score} {m.away}"))
        else:
            l1, l2 = tie.legs
            lines.append((t("tie_leg1"), f"{l1.home} {l1.score} {l1.away}"))
            lines.append((t("tie_leg2"), f"{l2.home} {l2.score} {l2.away}"))
            if tie.method == "aggregate":
                lines.append(("Σ", t("tie_agg", a=tie.score_a, b=tie.score_b)))
            else:
                lines.append(("Σ", t("tie_legs_pts", a=f"{tie.score_a:g}",
                                     b=f"{tie.score_b:g}")))
        if tie.extra_time:
            lines.append((t("tie_et"),
                          f"{tie.a} {tie.extra_time[0]}-{tie.extra_time[1]} {tie.b}"))
        if tie.method == "legs" and so is not None and so.p_winner is not None:
            lines.append(("Elo", t("tie_elo_pick", club=tie.winner, p=so.p_winner)))

        x2 = pad + int(250 * s)
        x3 = width - int(300 * s) if so is not None else width
        label_w = max([bold_f.measure(label) for label, _ in lines] + [0]) + int(16 * s)
        value_w = max(int(160 * s), x3 - x2 - label_w - int(20 * s))
        y = int(16 * s)
        for label, text in lines:
            cv.create_text(x2, y, anchor="nw", text=label, font=bold_f,
                           fill=tr.resolve_color(TEXT_MUTED))
            item = cv.create_text(x2 + label_w, y, anchor="nw", text=text, font=body_f,
                                  fill=tr.resolve_color(TEXT), width=value_w)
            bbox = cv.bbox(item)
            y = (bbox[3] if bbox else y + int(16 * s)) + int(5 * s)

        # Column 3: the penalty shootout sheet.
        if so is not None:
            y = int(16 * s)
            cv.create_text(x3, y, anchor="nw", font=over_f,
                           fill=tr.resolve_color(TEXT_FAINT),
                           text=f"{t('tie_pens').upper()}  "
                                f"{so.goals_first}-{so.goals_second}")
            y += int(22 * s)
            _, h = draw_shootout(cv, x3, y, so, so.first, so.second, body_f, s,
                                 max_width=width - x3 - pad)
            cv.create_text(x3, y + h + int(10 * s), anchor="nw", font=body_f,
                           fill=tr.resolve_color(TEXT_MUTED),
                           text=t("tie_first", club=so.first))

    # ---------- tab 3: the probabilities ----------
    def _show_probs(self):
        if self.mc is None:
            ctk.CTkLabel(self.tab_host, text=self.app.t("probs_off"),
                         font=self.app.fonts["body"], text_color=TEXT_MUTED,
                         wraplength=700).pack(pady=40)
            return
        n = f"{self.mc.runs:,}"
        self._legend(self.tab_host, ((self.app.t("probs_h", n=n) + "  " +
                                      self.app.t("probs_sort"), None),))
        ProbTable(self.tab_host, self.app, self, self.mc, STAGES).pack(
            fill="both", expand=True)

    # ---------- tab 4: the expert log ----------
    def _show_expert(self):
        trace = self.result.trace
        if not trace:
            ctk.CTkLabel(self.tab_host, text=self.app.t("expert_off"),
                         font=self.app.fonts["body"], text_color=TEXT_MUTED,
                         wraplength=700).pack(pady=40)
            return

        bar = ctk.CTkFrame(self.tab_host, fg_color="transparent")
        bar.pack(fill="x", pady=(0, 8))
        self.expert_count = ctk.CTkLabel(bar, text=self.app.t("expert_h", n=len(trace)),
                                         font=FONTS.get("small"), text_color=TEXT_MUTED)
        self.expert_count.pack(side="left")
        self.filter_entry = ctk.CTkEntry(bar, width=280, height=32,
                                         placeholder_text=self.app.t("expert_filter"),
                                         font=self.app.fonts["small"])
        self.filter_entry.pack(side="right")
        self.filter_entry.bind("<KeyRelease>", lambda _e: self._schedule_filter())

        # tkinter.Text and not CTkTextbox: the latter wraps the former in
        # a canvas with rounded corners, and two thousand lines take
        # several tenths of a second to arrive there instead of the blink
        # of an eye.
        frame = self._card(self.tab_host)
        frame.pack(fill="both", expand=True)
        holder = flat_frame(frame, CARD)
        holder.pack(fill="both", expand=True, padx=8, pady=8)
        self.text = tkinter.Text(holder, wrap="none", bd=0, highlightthickness=0,
                                 bg=tr.resolve_color(CARD),
                                 fg=tr.resolve_color(TEXT), font=FONTS.get("mono"),
                                 padx=10, pady=6, insertwidth=0,
                                 selectbackground=self.app.accent,
                                 selectforeground="#FFFFFF")
        ybar = ctk.CTkScrollbar(holder, orientation="vertical", command=self.text.yview)
        xbar = ctk.CTkScrollbar(holder, orientation="horizontal", command=self.text.xview)
        self.text.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
        ybar.pack(side="right", fill="y")
        xbar.pack(side="bottom", fill="x")
        self.text.pack(fill="both", expand=True)
        self.text.tag_configure("section", foreground=self.app.accent,
                                font=tk_font(self, 12, "bold", "mono"),
                                spacing1=8, spacing3=2)
        self.text.tag_configure("match", foreground=tr.resolve_color(TEXT),
                                font=tk_font(self, 11, "bold", "mono"), spacing1=4)
        self.text.tag_configure("muted", foreground=tr.resolve_color(TEXT_MUTED))
        self.text.tag_configure("hit", background=self.app.accent, foreground="#FFFFFF")
        self._filter_job = None
        self._fill_text(trace)

    def _fill_text(self, lines, needle=None):
        text = self.text
        text.configure(state="normal")
        text.delete("1.0", "end")
        # One insert per group of lines with the same tag: Tk inserts one
        # big string much faster than a thousand small ones.
        chunk, tag = [], None
        for line in lines:
            kind = ("section" if line.startswith("== ") else
                    "match" if line.startswith("-- ") else "muted")
            if kind != tag and chunk:
                text.insert("end", "\n".join(chunk) + "\n", tag)
                chunk = []
            tag = kind
            chunk.append(line)
        if chunk:
            text.insert("end", "\n".join(chunk) + "\n", tag)
        if needle:
            start = "1.0"
            while True:
                pos = text.search(needle, start, stopindex="end", nocase=True)
                if not pos:
                    break
                end = f"{pos}+{len(needle)}c"
                text.tag_add("hit", pos, end)
                start = end
        text.configure(state="disabled")

    def _schedule_filter(self):
        # We wait for the typing to settle: filtering 2000 lines on every
        # keystroke would make typing lag.
        if self._filter_job is not None:
            try:
                self.after_cancel(self._filter_job)
            except (tkinter.TclError, ValueError):
                pass
        self._filter_job = self.after(120, self._apply_filter)

    def _apply_filter(self):
        self._filter_job = None
        needle = self.filter_entry.get().strip()
        trace = self.result.trace
        if not needle:
            self._fill_text(trace)
            self.expert_count.configure(text=self.app.t("expert_h", n=len(trace)))
            return
        low = needle.casefold()
        # A section or a match that matches is shown with its detail
        # lines; a detail line that matches is shown alone. Enough for
        # "Arsenal" as well as for "penalties". A detail line that matches
        # also brings along the more indented lines that follow it (the
        # penalty shootout sheet, the two lines of a neutral-venue
        # probability calculation).
        shown, keep, hit_indent = [], False, None
        for line in trace:
            if line.startswith("== ") or line.startswith("-- "):
                keep, hit_indent = low in line.casefold(), None
                if keep:
                    shown.append(line)
                continue
            indent = len(line) - len(line.lstrip(" "))
            if hit_indent is not None and indent > hit_indent:
                shown.append(line)
                continue
            hit_indent = None
            if keep:
                shown.append(line)
            elif low in line.casefold():
                shown.append(line)
                hit_indent = indent
        self._fill_text(shown, needle)
        self.expert_count.configure(text=self.app.t("expert_h", n=len(shown)))

    # ---------- saving ----------
    def _save(self):
        try:
            path = save_log(self.result)
        except OSError as exc:
            MessageDialog(self.winfo_toplevel(), self.app,
                          self.app.t("sim_save_bad_title"), str(exc), tone="error")
            return
        try:
            shown = path.relative_to(USER_DIR).as_posix()
        except ValueError:
            shown = str(path)
        MessageDialog(self.winfo_toplevel(), self.app, self.app.t("sim_saved_title"),
                      self.app.t("sim_saved", file=shown),
                      [self.app.t("sim_not_found", club=w.split(":")[0])
                       for w in self.result.warnings], tone="ok")

    # =================================================================
    #  FALLBACK STATE
    # =================================================================
    def _build_failed(self, parent):
        middle = ctk.CTkFrame(parent, fg_color="transparent")
        middle.pack(expand=True)
        ctk.CTkLabel(middle, text=self.app.t("sim_failed"),
                     font=self.app.fonts["title"], text_color=TEXT).pack()
        ctk.CTkLabel(middle, text=str(self._error or "")[:400],
                     font=self.app.fonts["small"], text_color=TEXT_MUTED,
                     wraplength=620, justify="center").pack(pady=(14, 22))
        self._primary(middle, "retry", lambda: self._go("setup"), width=170).pack()
        self._ghost(middle, "back", lambda: self.app.back("draw")).pack(pady=14)
