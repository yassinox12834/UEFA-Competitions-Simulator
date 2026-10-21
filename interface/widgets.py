"""
widgets.py - the reusable building blocks of the interface.

Nothing here knows the journey through the app: a card does not know
whether it stands for a language or a competition; it only knows how to
display itself, react to hovering and signal a click. This is what allows
the same blocks to be reused on later screens (results, live draw, and so
on).

Contents:
    CardButton   the clickable card (image + title + subtitle)
    card_button  card factory
    ghost_button secondary button, outline only
    StepHeader   step header (number + question + hint)
"""

import tkinter

import customtkinter as ctk

import transition as tr
from config import (BORDER, CARD, CARD_HOVER, CARD_RADIUS, COMP, DEFAULT_COMP,
                    HOVER_MS, SURFACE_2, TEXT, TEXT_MUTED)
from fonts import FONTS


# =====================================================================
#  CLICKABLE CARD
# =====================================================================

class CardButton(ctk.CTkFrame):
    """
    A card = an image, a title, a subtitle, and a chosen state.

    Why a CTkFrame rather than a CTkButton: a button has only one font and
    one text colour. Here the title must be bold and the subtitle discreet,
    so we need real labels. We simply recreate what a button provides:
    hover, cursor, click.
    """

    def __init__(self, master, title="", subtitle=None, image=None, emoji=None,
                 width=170, height=190, command=None, accent=None, **kwargs):
        super().__init__(master, width=width, height=height,
                         corner_radius=CARD_RADIUS, fg_color=CARD,
                         border_width=2, border_color=BORDER, **kwargs)
        self.pack_propagate(False)
        self.grid_propagate(False)

        self.command = command
        self.accent = accent or COMP[DEFAULT_COMP]["accent"]
        self._selected = False
        self._hover = False

        # An intermediate frame with expand=True: the block stays vertically
        # centred whatever height is requested for the card.
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(expand=True, fill="x", padx=14)

        self.icon = ctk.CTkLabel(inner, text=emoji or "", image=image,
                                 fg_color="transparent",
                                 font=FONTS.get("title"), text_color=TEXT)
        self.icon.pack(pady=(0, 14))

        self.title_label = ctk.CTkLabel(inner, text=title, fg_color="transparent",
                                        font=FONTS.get("h2"), text_color=TEXT)
        self.title_label.pack()

        self.subtitle_label = ctk.CTkLabel(
            inner, text=subtitle or "", fg_color="transparent",
            font=FONTS.get("small"), text_color=TEXT_MUTED,
            wraplength=width - 44, justify="center")
        self.subtitle_label.pack(pady=(6, 0))

        self._bind_tree(self)
        # Leaving the screen with the cursor over the card would leave the
        # hover state on when coming back: we switch it off on unmap.
        self.bind("<Unmap>", self._on_unmap, add="+")

    # ---------- content ----------
    def set_text(self, title=None, subtitle=None):
        if title is not None:
            self.title_label.configure(text=title)
        if subtitle is not None:
            self.subtitle_label.configure(text=subtitle)

    def set_image(self, image):
        self.icon.configure(image=image)

    def set_accent(self, accent):
        self.accent = accent
        self._paint(animated=False)

    # ---------- state ----------
    def set_selected(self, selected):
        if selected == self._selected:
            return
        self._selected = selected
        self._paint()

    @property
    def selected(self):
        return self._selected

    def _paint(self, animated=True):
        """A single function decides the colours: no contradictory state."""
        # Card not displayed yet: paint at once. Otherwise the animation
        # would fight the view's entry fade, which memorises the colours at
        # the start and restores them at the end.
        animated = animated and bool(self.winfo_viewable())
        if self._selected:
            border, fill = self.accent, CARD_HOVER
        elif self._hover:
            border, fill = tr.lerp_color(self, BORDER, self.accent, 0.55) or self.accent, CARD_HOVER
        else:
            border, fill = BORDER, CARD

        if animated:
            tr.animate_color(self, "border_color", border, HOVER_MS)
            tr.animate_color(self, "fg_color", fill, HOVER_MS)
        else:
            self.configure(border_color=border, fg_color=fill)

    # ---------- mouse ----------
    def _bind_tree(self, widget):
        """
        Tk does not bubble events up to the parent: we therefore have to
        subscribe on every inner widget (including the hidden Tk label in a
        CTkLabel), otherwise the card is only clickable between its texts.
        """
        widget.bind("<Button-1>", self._on_click, add="+")
        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")
        try:
            widget.configure(cursor="hand2")
        except (tkinter.TclError, ValueError):
            pass
        for child in widget.winfo_children():
            self._bind_tree(child)

    def _on_click(self, _event=None):
        if self.command is not None:
            self.command()

    def _on_enter(self, _event=None):
        if not self._hover:
            self._hover = True
            self._paint()

    def _on_unmap(self, _event=None):
        if self._hover:
            self._hover = False
            self._paint()

    def _on_leave(self, _event=None):
        # <Leave> also fires when moving over a child: so we check where the
        # cursor really is, a moment later.
        self.after(10, self._check_pointer)

    def _check_pointer(self):
        try:
            px, py = self.winfo_pointerxy()
            x, y = self.winfo_rootx(), self.winfo_rooty()
            inside = (x <= px < x + self.winfo_width()
                      and y <= py < y + self.winfo_height())
        except tkinter.TclError:
            return
        if not inside and self._hover:
            self._hover = False
            self._paint()


def card_button(parent, title, emoji=None, image=None, subtitle=None,
                width=170, height=190, command=None, accent=None):
    """Card factory: the only way to create a choice in the app."""
    return CardButton(parent, title=title, subtitle=subtitle, image=image,
                      emoji=emoji, width=width, height=height,
                      command=command, accent=accent)


def ghost_button(parent, command, width=130):
    """Secondary button: outline only, so it does not compete with the accent."""
    return ctk.CTkButton(parent, text="", width=width, height=38,
                         corner_radius=10, fg_color="transparent",
                         hover_color=SURFACE_2, border_width=1,
                         border_color=BORDER, text_color=TEXT_MUTED,
                         font=FONTS.get("small"), command=command)


# =====================================================================
#  STEP HEADER
# =====================================================================

class StepHeader(ctk.CTkFrame):
    """The step number / question / hint trio, at the top of each view."""

    def __init__(self, master, app, n, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app, self.n = app, n
        self.step = ctk.CTkLabel(self, text="", font=app.fonts["tiny"],
                                 text_color=TEXT_MUTED)
        self.step.pack()
        self.question = ctk.CTkLabel(self, text="", font=app.fonts["title"],
                                     text_color=TEXT)
        self.question.pack(pady=(6, 0))
        self.hint = ctk.CTkLabel(self, text="", font=app.fonts["body"],
                                 text_color=TEXT_MUTED)
        self.hint.pack(pady=(8, 0))

    def refresh(self, question_key, hint_key=None):
        self.step.configure(text=self.app.t("step", n=self.n).upper())
        self.question.configure(text=self.app.t(question_key))
        self.hint.configure(text=self.app.t(hint_key) if hint_key else "")
