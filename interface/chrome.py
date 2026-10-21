"""
chrome.py - the two bars that never move.

In interface design, "chrome" is the permanent frame around the content:
here the top bar (AppBar) and the step rail (StepRail). They are placed
once by App and survive view changes; only the central block is replaced
during a transition.

Each one exposes a refresh(step) method: App calls it again whenever a
choice changes, and the bar updates itself.
"""

import tkinter

import customtkinter as ctk

import transition as tr
from config import (BORDER, SURFACE, SURFACE_2, TEXT, TEXT_MUTED,
                    WINDOW_TITLE)
from fonts import FONTS, scaling
from images import brand_image, comp_image


def _rule(parent, colour, width=None):
    """A line 2 logical px thick.

    A tkinter.Frame and not a CTkFrame: at 125 % Windows scaling, a
    CTkFrame 2 px high is not drawn at all (it rounds its usable height down
    to zero). The Tk Frame is measured in real pixels, so we apply the
    scaling ourselves.
    """
    s = scaling(parent)
    kw = {"width": int(width * s)} if width else {}
    return tkinter.Frame(parent, height=max(2, round(2 * s)), bd=0,
                         highlightthickness=0, bg=tr.resolve_color(colour), **kw)


class AppBar(ctk.CTkFrame):
    """Always visible: the app's identity on the left, settings on the right."""

    def __init__(self, master, app):
        super().__init__(master, fg_color=SURFACE, corner_radius=0, height=64)
        self.app = app
        self.pack_propagate(False)

        # A hairline under the bar, in the competition's colour: it is what
        # "signs" the screen when moving from the UCL to the UEL.
        self.hairline = _rule(self, app.accent)
        self.hairline.pack(side="bottom", fill="x")

        left = ctk.CTkFrame(self, fg_color="transparent")
        left.pack(side="left", padx=24)
        self.mark = ctk.CTkLabel(left, text="", image=brand_image(app.accent))
        self.mark.pack(side="left")
        titles = ctk.CTkFrame(left, fg_color="transparent")
        titles.pack(side="left", padx=12)
        ctk.CTkLabel(titles, text=WINDOW_TITLE, font=FONTS["brand"],
                     text_color=TEXT).pack(anchor="w")
        self.tagline = ctk.CTkLabel(titles, text="", font=FONTS["tiny"],
                                    text_color=TEXT_MUTED)
        self.tagline.pack(anchor="w")

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.pack(side="right", padx=26)
        self.theme_switch = ctk.CTkSwitch(
            right, text="", font=FONTS["small"], text_color=TEXT_MUTED,
            width=44, switch_width=40, switch_height=20,
            progress_color=app.accent, command=app.toggle_appearance)
        self.theme_switch.pack(side="right")

        # The "competition" chip: logo + short name, on a pill.
        self.comp_badge = ctk.CTkFrame(right, fg_color=SURFACE_2, corner_radius=18,
                                       border_width=1, border_color=BORDER)
        self.comp_logo = ctk.CTkLabel(self.comp_badge, text="")
        self.comp_logo.pack(side="left", padx=(5, 6), pady=4)
        self.comp_name = ctk.CTkLabel(self.comp_badge, text="", font=FONTS["small_b"],
                                      text_color=TEXT)
        self.comp_name.pack(side="left", padx=(0, 14))

    def refresh(self, step):
        self.tagline.configure(text=self.app.t("tagline"))
        self.theme_switch.configure(text=self.app.t("dark_mode"),
                                    progress_color=self.app.accent)
        tr.animate_color(self.hairline, "bg", self.app.accent, 200)
        self.mark.configure(image=brand_image(self.app.accent))

        # The competition logo only makes sense once the competition has
        # been chosen. We take it out of the layout rather than clearing the
        # image: that is the only safe way to leave nothing behind. The step
        # number cannot tell us any more, since the three menu screens share
        # step 1, so we look at the screen itself.
        if self.app.current_view in ("mode", "draw", "simulation"):
            self.comp_logo.configure(
                image=comp_image(self.app.comp, box=(26, 26), plate="#FFFFFF"))
            self.comp_name.configure(text=self.app.t(self.app.comp))
            if not self.comp_badge.winfo_ismapped():
                self.comp_badge.pack(side="right", padx=(0, 18))
        else:
            self.comp_badge.pack_forget()


class StepRail(ctk.CTkFrame):
    """The step rail: where I am, what is left. Linked badges."""

    def __init__(self, master, app):
        super().__init__(master, fg_color=SURFACE, corner_radius=0, height=60)
        self.app = app
        self.pack_propagate(False)

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(expand=True)

        # Three steps at most. The three menu screens (language,
        # competition, mode) sit under a single "Welcome" badge: they are
        # three questions but one phase. The draw is the second. The
        # simulation is the third, and it only appears if the chosen mode
        # goes that far: in "draw only" mode the rail stops at two badges.
        self.keys = ("s_welcome", "s_draw", "s_sim")
        self.badges, self.labels, self.links = [], [], []
        self._sim_shown = True

        for i, key in enumerate(self.keys):
            if i:
                link = _rule(row, BORDER, width=130)
                link.pack(side="left", padx=10)
                self.links.append(link)

            badge = ctk.CTkLabel(row, text=str(i + 1), width=26, height=26,
                                 corner_radius=13, fg_color=SURFACE_2,
                                 font=FONTS["badge"], text_color=TEXT_MUTED)
            badge.pack(side="left")
            label = ctk.CTkLabel(row, text="", font=FONTS["small"],
                                 text_color=TEXT_MUTED)
            label.pack(side="left", padx=(8, 0))
            self.badges.append(badge)
            self.labels.append(label)

    def _show_sim(self, shown):
        """Show or hide the third badge and its link."""
        if shown == self._sim_shown:
            return
        self._sim_shown = shown
        widgets = (self.links[1], self.badges[2], self.labels[2])
        if shown:
            self.links[1].pack(side="left", padx=10)
            self.badges[2].pack(side="left")
            self.labels[2].pack(side="left", padx=(8, 0))
        else:
            for widget in widgets:
                widget.pack_forget()

    def refresh(self, step):
        accent = self.app.accent
        self._show_sim(self.app.mode == "simulate")
        for i, (badge, label) in enumerate(zip(self.badges, self.labels), start=1):
            label.configure(text=self.app.t(self.keys[i - 1]))
            done, current = i < step, i == step
            tr.animate_color(badge, "fg_color",
                             accent if (done or current) else SURFACE_2, 220)
            tr.animate_color(badge, "text_color",
                             "#FFFFFF" if (done or current) else TEXT_MUTED, 220)
            tr.animate_color(label, "text_color",
                             TEXT if current else TEXT_MUTED, 220)
        for i, link in enumerate(self.links, start=2):
            tr.animate_color(link, "bg", tr.resolve_color(accent if i <= step else BORDER),
                             220)
