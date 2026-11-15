"""
draw_widgets.py - the building blocks specific to the draw screen.

Same rule as widgets.py: nothing here knows the journey through the app
or the engine. A ClubChip does not know whether the club was replaced by
the user or read from a CSV; it knows how to display a name, a badge, and
signal a click.

Contents:
    offset_in       the position of a widget inside one of its ancestors
    ClubChip        a club in a pot
    PotColumn       a pot: a header and its clubs
    PotsBoard       the 4 (or 6) pots side by side
    ReplaceDialog   the "replace a club" window, reused
    ConstraintsDialog  the "forbidden fixtures" window, reused
    MessageDialog   a report: title, sentence, list of lines
    OpponentCard    an opponent that has just been drawn
    BowlStrip       the remaining balls of the current pot
    MatchRow        a fixture: home - away
    Spinner         the dot that spins during the calculation
"""

import time
import tkinter
from tkinter import filedialog

import customtkinter as ctk
from PIL import Image

import transition as tr
from config import (AWAY, BORDER, CARD, CHIP, CHIP_BORDER,
                    CHIP_DRAWN, CHIP_HOVER, CHIP_RADIUS, HOME,
                    POT_HEADER, REPLACED, SURFACE, SURFACE_2, TEXT,
                    TEXT_MUTED)
from canvas_views import _fit
from fonts import FONTS, scaling, tk_font
from images import ball_image, club_image, club_photo


def offset_in(widget, ancestor):
    """
    Position (x, y) of a widget inside one of its ancestors.

    Tk only gives the position of a widget within its direct parent
    (winfo_x/y). To animate a ball that leaves a bowl placed in one frame
    and arrives at the centre of another frame, we have to walk up the
    chain of parents, adding as we go. winfo_rootx would also have worked,
    but it counts the DPI scaling, which place() does not: the two do not
    speak the same unit, and the ball landed next to its target.
    """
    x = y = 0
    node = widget
    while node is not None and node is not ancestor:
        x += node.winfo_x()
        y += node.winfo_y()
        node = node.master
    return x, y


# =====================================================================
#  FLAT BLOCKS: PLAIN TK, FOR DENSE LISTS
# =====================================================================
# Measured on this machine, the cost of building a widget:
#
#     tkinter.Frame               0.02 ms
#     tkinter.Label               0.03 ms
#     CTkFrame (transparent)      2.34 ms      117x
#     CTkLabel                    1.80 ms       60x
#     CTkFrame (fill + border)    4.16 ms      208x
#
# A CustomTkinter widget is not a Tk widget: it is a canvas on which it
# redraws its rounded corners by hand, at construction and on every
# configure(). That is the price of the styling, and it is gladly paid for
# a card or a button. It is not worth paying a hundred times to align text
# in a list: the "by club" tab took 1.07 seconds to display, almost
# entirely in invisible widgets.
#
# Rule: anything that has a shape (rounded corners, border, hover) stays
# in CustomTkinter. Anything that only carries text or aligns children
# uses plain Tk.
#
# The price to pay: a Tk widget does not know the (light, dark) pair and
# so will not follow a theme change. Their colour is resolved at
# construction, and the results screen is rebuilt when the theme switches
# (see DrawView.refresh_text).


def flat_frame(parent, bg, **kwargs):
    """Layout container, unstyled. `bg` accepts a pair."""
    return tkinter.Frame(parent, bg=tr.resolve_color(bg),
                         highlightthickness=0, bd=0, **kwargs)


def flat_label(parent, text, bg, fg, font=None, photo=None, **kwargs):
    """Unstyled label. `photo` is a PhotoImage, NOT a CTkImage."""
    label = tkinter.Label(parent, text=text, bg=tr.resolve_color(bg),
                          fg=tr.resolve_color(fg), font=font,
                          highlightthickness=0, bd=0, **kwargs)
    if photo is not None:
        # Keeping the reference on the widget is the usual Tk idiom:
        # without it, the image would be garbage-collected and the label
        # left empty.
        label.configure(image=photo, compound="left")
        label.image = photo
    return label


# =====================================================================
#  A CLUB IN A POT
# =====================================================================
# Performance note (2026-11, measured headless with profile_ui.py):
#
# A chip used to be a CTkFrame holding a CTkLabel. Each of those is a
# canvas that CustomTkinter redraws by hand, and each one registers itself
# with the appearance-mode tracker and the scaling tracker; destroying it
# removes it from those lists again (a linear search). With 36 chips the
# pots board cost about 340 ms to build and was rebuilt up to three times
# per visit. CustomTkinter's own tracker lists issues #2652 ("rendering
# multiple widgets") and #2687 ("destroy does not delete children") for
# the same reason.
#
# A chip is now ONE plain tkinter.Canvas with three items: a background
# image (the rounded rectangle), the badge and the name. The rounded
# rectangle is drawn with Pillow at twice the size and scaled down, so the
# corners stay antialiased like CustomTkinter's; every (size, colours)
# combination is drawn once and cached, so hovering or greying a chip
# only swaps one image id. The theme is followed by PotsBoard, which
# registers a single callback for all its chips instead of 72.

_CHIP_BG_CACHE = {}


def _chip_background(w, h, radius, fill, border, border_w, behind):
    """The chip's rounded rectangle as a PhotoImage, cached.

    `behind` is the colour of whatever is under the chip: the corners are
    painted with it, so no transparency is needed.
    """
    key = (w, h, radius, fill, border, border_w, behind)
    photo = _CHIP_BG_CACHE.get(key)
    if photo is not None:
        return photo
    from PIL import ImageDraw, ImageTk
    k = 2                                   # supersampling factor
    img = Image.new("RGB", (w * k, h * k), behind)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w * k - 1, h * k - 1), radius=radius * k,
                        fill=border)
    inset = border_w * k
    d.rounded_rectangle((inset, inset, w * k - 1 - inset, h * k - 1 - inset),
                        radius=max(0, (radius - border_w) * k), fill=fill)
    photo = ImageTk.PhotoImage(img.resize((w, h), Image.LANCZOS))
    _CHIP_BG_CACHE[key] = photo
    return photo


def _colour_behind(widget):
    """The visible background colour under `widget` (first opaque ancestor)."""
    return _colour_behind_widget(widget.master)


def _colour_behind_widget(node):
    """The colour of `node`, or of its first ancestor that is not transparent."""
    while node is not None:
        try:
            colour = node.cget("fg_color")
        except (ValueError, tkinter.TclError, AttributeError):
            try:
                colour = node.cget("bg")
            except (ValueError, tkinter.TclError):
                colour = None
        if colour and colour != "transparent":
            return tr.resolve_color(colour)
        node = node.master
    return tr.resolve_color(SURFACE)


class ClubChip(tkinter.Canvas):
    """Badge + name, clickable. Greys out once the ball has come out."""

    BADGE = 22          # logical px

    def __init__(self, master, comp, club, accent, width=210, height=36,
                 command=None, logo_path=None, replaced=False, **kwargs):
        self.s = scaling(master)
        self.w, self.h = round(width * self.s), round(height * self.s)
        super().__init__(master, width=self.w, height=self.h,
                         highlightthickness=0, bd=0, **kwargs)
        self.comp, self.club, self.accent = comp, club, accent
        self.command = command
        self._hover = False
        self._drawn = False
        self._selected = False     # first club picked for a swap
        self.click_state = 0       # modifier keys held during the last click
        self._logo_path = logo_path
        self._replaced = replaced

        self._font = tk_font(self, 12)
        pad = round(8 * self.s)
        mid = self.h // 2
        self._bg_item = self.create_image(0, 0, anchor="nw")
        self._logo_item = self.create_image(pad, mid, anchor="w")
        self._text_x = pad + round((self.BADGE + 6) * self.s)
        self._text_item = self.create_text(self._text_x, mid, anchor="w",
                                           font=self._font)
        self._mark_item = None

        # One widget, no children: a single binding of each kind is
        # enough, and <Leave> is reliable (it no longer fires when the
        # pointer moves onto an inner label), so the old after(10)
        # pointer check is gone.
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Unmap>", self._on_unmap)
        if command is not None:
            self.configure(cursor="hand2")

        self._draw_content()
        self._paint()

    # ---------- content ----------
    def _draw_content(self):
        photo = club_photo(self.comp, self.club, round(self.BADGE * self.s),
                           self.accent, self._logo_path)
        self.itemconfigure(self._logo_item, image=photo or "")
        self._logo_ref = photo
        room = self.w - self._text_x - round(18 * self.s)
        self.itemconfigure(self._text_item, text=_fit(self._font, self.club, room))
        self._show_mark(self._replaced)

    def _show_mark(self, show):
        if show and self._mark_item is None:
            r = round(4 * self.s)
            cx, cy = self.w - round(13 * self.s), self.h // 2
            self._mark_item = self.create_oval(cx - r, cy - r, cx + r, cy + r,
                                               width=0)
            self._paint_mark()
        elif not show and self._mark_item is not None:
            self.delete(self._mark_item)
            self._mark_item = None

    def _paint_mark(self):
        if self._mark_item is not None:
            self.itemconfigure(self._mark_item, fill=tr.resolve_color(REPLACED))

    def refresh(self, club, logo_path=None, replaced=False):
        if club != self.club or logo_path is not None:
            self.club = club
            self._logo_path = logo_path
            self._replaced = replaced
            self._draw_content()
        else:
            self._replaced = replaced
            self._show_mark(replaced)

    def set_accent(self, accent):
        if accent == self.accent:
            return
        self.accent = accent
        self._paint()

    def set_selected(self, selected):
        """Picked as the first club of a swap: an accent frame that stays
        until the second click, so the user can see what they picked."""
        if selected == self._selected:
            return
        self._selected = selected
        self._paint()

    def set_drawn(self, drawn):
        """The ball has come out: the club dims without disappearing."""
        if drawn == self._drawn:
            return
        self._drawn = drawn
        self._paint()

    # ---------- colours ----------
    def _paint(self, animated=False):
        """Colours applied at once: a fade on 36 chips is not worth it.

        Also called by PotsBoard when the theme changes, which is why every
        colour is resolved here and not at construction.
        """
        if self._drawn:
            border, fill = CHIP_BORDER, CHIP_DRAWN
        elif self._selected or (self._hover and self.command is not None):
            border, fill = self.accent, CHIP_HOVER
        else:
            border, fill = CHIP_BORDER, CHIP
        behind = _colour_behind(self)
        width = 2 if self._selected else 1
        bg = _chip_background(self.w, self.h, round(CHIP_RADIUS * self.s),
                              tr.resolve_color(fill), tr.resolve_color(border),
                              max(1, round(width * self.s)), behind)
        self.configure(bg=behind)
        self.itemconfigure(self._bg_item, image=bg)
        self.itemconfigure(self._text_item, fill=tr.resolve_color(
            TEXT_MUTED if self._drawn else TEXT))
        self._paint_mark()

    # ---------- mouse ----------
    def _on_click(self, e=None):
        self.click_state = getattr(e, "state", 0) or 0 if e is not None else 0
        if self.command is not None:
            self.command(self)

    def _on_enter(self, _e=None):
        if not self._hover:
            self._hover = True
            self._paint()

    def _on_leave(self, _e=None):
        if self._hover:
            self._hover = False
            self._paint()

    _on_unmap = _on_leave

# =====================================================================
#  ONE POT, THEN ALL THE POTS
# =====================================================================

class PotColumn(ctk.CTkFrame):
    """A numbered header and the stack of clubs beneath it."""

    def __init__(self, master, app, comp, pot_number, clubs, model,
                 on_click=None, chip_width=210, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app, self.pot_number = app, pot_number

        self.header = ctk.CTkLabel(
            self, text=app.t("pot_n", n=pot_number), height=28,
            corner_radius=8, fg_color=POT_HEADER, font=FONTS.get("badge"),
            text_color=TEXT_MUTED, width=chip_width)
        self.header.pack(fill="x", pady=(0, 6))

        self.chips = []
        for slot, club in enumerate(clubs):
            chip = ClubChip(
                self, comp, club, app.accent, width=chip_width,
                logo_path=model.logo_for(club),
                replaced=model.is_replaced(club),
                command=(lambda c, s=slot: on_click(pot_number - 1, s, c))
                if on_click else None)
            chip.pack(pady=2)
            self.chips.append(chip)

    def refresh(self, model):
        """The whole pot. For a language or template change."""
        self.header.configure(text=self.app.t("pot_n", n=self.pot_number))
        clubs = model.pots[self.pot_number - 1]
        for chip, club in zip(self.chips, clubs):
            chip.set_accent(self.app.accent)
            chip.refresh(club, model.logo_for(club), model.is_replaced(club))

    def refresh_one(self, slot_index, model):
        """A single place. This is the path of a manual replacement.

        A replacement only touches one chip, but refresh() used to repaint
        all nine: each costs two configure() calls, and each configure()
        redraws a canvas. Across the four pots that meant more than
        seventy redraws for a single chip that changes, which is exactly
        the dead time you could feel after confirming the dialog.
        """
        if not 0 <= slot_index < len(self.chips):
            return
        club = model.pots[self.pot_number - 1][slot_index]
        self.chips[slot_index].refresh(club, model.logo_for(club),
                                       model.is_replaced(club))

    def set_drawn(self, club, drawn=True):
        for chip in self.chips:
            if chip.club == club:
                chip.set_drawn(drawn)

    def reset_drawn(self):
        for chip in self.chips:
            chip.set_drawn(False)


class PotsBoard(ctk.CTkScrollableFrame):
    """
    The pots side by side.

    Scrollable as a precaution: 9 clubs per column fit in 820 px of
    height, but the window is allowed to shrink to 660, and the user may
    enlarge the system font. A scrollbar that is never needed costs
    nothing; a club that is cut off and cannot be reached does.
    """

    def __init__(self, master, app, comp, model, on_click=None, lazy=False,
                 **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app, self.model = app, model
        self._comp, self._on_click = comp, on_click
        # 4 pots of 9 -> wide columns; 6 pots of 6 -> narrow ones.
        self._chip_width = 210 if len(model.pots) <= 4 else 152

        self._row = ctk.CTkFrame(self, fg_color="transparent")
        self._row.pack(expand=True)
        self.columns = []
        # lazy=True (the prewarm): one column per idle slot, so the screen
        # the user is looking at never stalls for the whole board at once.
        # complete() finishes the job synchronously if the board is needed
        # before the last slot came.
        self._idle_job = None
        if lazy:
            self._idle_job = self.after_idle(self._build_next)
        else:
            self.complete()

        # The chips are plain Tk canvases: they do not follow the theme by
        # themselves. ONE callback repaints all of them, instead of one
        # registration per CustomTkinter widget as before.
        ctk.AppearanceModeTracker.add(self._on_theme, self)
        self.bind("<Destroy>", self._on_destroy, add="+")

    def _build_column(self):
        index = len(self.columns) + 1
        column = PotColumn(self._row, self.app, self._comp, index,
                           self.model.pots[index - 1], self.model,
                           on_click=self._on_click, chip_width=self._chip_width)
        column.pack(side="left", padx=7, anchor="n")
        self.columns.append(column)

    def _build_next(self):
        self._idle_job = None
        if len(self.columns) < len(self.model.pots):
            self._build_column()
            if len(self.columns) < len(self.model.pots):
                # A short timer, not after_idle: Tk runs every idle callback
                # in a single pass, which would rebuild the whole board in
                # one block again. 10 ms lets clicks and repaints through.
                self._idle_job = self.after(10, self._build_next)

    def complete(self):
        """Builds whatever columns are still missing, right now."""
        if self._idle_job is not None:
            try:
                self.after_cancel(self._idle_job)
            except (tkinter.TclError, ValueError):
                pass
            self._idle_job = None
        while len(self.columns) < len(self.model.pots):
            self._build_column()

    def _on_theme(self, _mode=None):
        for column in self.columns:
            for chip in column.chips:
                try:
                    chip._paint()
                except tkinter.TclError:
                    pass

    def _on_destroy(self, event):
        if event.widget is self:
            ctk.AppearanceModeTracker.remove(self._on_theme)

    def refresh(self):
        """The four (or six) pots. Expensive: keep it for real upheavals,
        such as a language change or loading a template."""
        for column in self.columns:
            column.refresh(self.model)

    def refresh_one(self, pot_index, slot_index):
        """A single chip, after a manual replacement or half of a swap."""
        if 0 <= pot_index < len(self.columns):
            self.columns[pot_index].refresh_one(slot_index, self.model)

    def set_selected(self, pot_index, slot_index, selected=True):
        """Marks one chip as picked for a swap, or unmarks it."""
        if not 0 <= pot_index < len(self.columns):
            return
        chips = self.columns[pot_index].chips
        if 0 <= slot_index < len(chips) and chips[slot_index].winfo_exists():
            chips[slot_index].set_selected(selected)

    def set_drawn(self, club, drawn=True):
        for column in self.columns:
            column.set_drawn(club, drawn)

    def reset_drawn(self):
        for column in self.columns:
            column.reset_drawn()


# =====================================================================
#  REPLACING A CLUB
# =====================================================================

def association_values(model, catalogue):
    """The association drop-down list, the most useful first.

    First the associations already present in the pots, sorted: when a
    club is replaced, nine times out of ten it is by a club from a country
    that is already represented, and that half of the list fits without
    scrolling. Then the other UEFA members, for the day someone invents a
    Welsh or Faroese club.

    The duplicate comparison ignores case, otherwise a CSV that says
    "england" and a catalogue that says "England" would give two entries
    for a single country.
    """
    used = sorted({(model.country_of(club) or "").strip()
                   for club in model.all_clubs()} - {""},
                  key=str.casefold)
    seen = {name.casefold() for name in used}
    rest = [name for name in catalogue if name.casefold() not in seen]
    return used + rest


class ReplaceDialog(ctk.CTkToplevel):
    """
    Name, association, badge. Nothing else.

    The pot and the place cannot be edited: changing them would break the
    shape of the problem that the engine knows how to solve. The
    association can, because it carries the rule "two opponents at most
    per country": a club without a credible association would distort the
    draw.

    ONE SINGLE instance serves the whole session. Opening the box used to
    build a brand-new CTkToplevel on every click: a window to request from
    the system, then about thirty CustomTkinter widgets to draw, which was
    150 to 250 ms before anything appeared. The window is therefore built
    once, then hidden (withdraw) and brought back (deiconify) on demand,
    with open_for() restacking the fields. The second and later clicks are
    instantaneous.

    A consequence not to forget: whatever is WRITTEN inside must be able
    to change without a rebuild. Hence _apply_texts(), replayed on every
    opening, which rewrites all the labels in the current language.
    """

    def __init__(self, master, app, comp, model, catalogue=(), on_done=None):
        super().__init__(master, fg_color=SURFACE)
        self.app, self.comp, self.model = app, comp, model
        self.catalogue = tuple(catalogue)
        self.on_done = on_done
        self.pot_index = self.slot_index = 0
        self.image_path = None
        self._values = None          # last content of the drop-down list

        self.resizable(False, False)
        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", self.close)

        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.pack(padx=26, pady=22)

        self.h_title = ctk.CTkLabel(wrap, text="", font=app.fonts["h2"],
                                    text_color=TEXT)
        self.h_title.pack(anchor="w")
        self.h_hint = ctk.CTkLabel(wrap, text="", font=FONTS.get("small"),
                                   text_color=TEXT_MUTED)
        self.h_hint.pack(anchor="w", pady=(4, 14))

        # A reminder of who is leaving, with their badge: this avoids
        # replacing the wrong club by mistake.
        leaving = ctk.CTkFrame(wrap, fg_color=SURFACE_2, corner_radius=10)
        leaving.pack(fill="x", pady=(0, 16))
        self.leaving_badge = ctk.CTkLabel(leaving, text="")
        self.leaving_badge.pack(side="left", padx=(10, 8), pady=8)
        texts = ctk.CTkFrame(leaving, fg_color="transparent")
        texts.pack(side="left", pady=8)
        self.leaving_caption = ctk.CTkLabel(texts, text="",
                                            font=FONTS.get("tiny"),
                                            text_color=TEXT_MUTED)
        self.leaving_caption.pack(anchor="w")
        self.leaving_name = ctk.CTkLabel(texts, text="", font=FONTS.get("small"),
                                         text_color=TEXT)
        self.leaving_name.pack(anchor="w")

        self.name_label, self.name_entry = self._field(wrap)

        # The association is a drop-down list, not a free field: typing
        # "Engald" passed every check and silently broke the rule of at
        # most two opponents per country, since the engine only compares
        # strings. It can NEVERTHELESS still be typed, because an invented
        # club may very well come from an association missing from the CSV.
        self.country_label = ctk.CTkLabel(wrap, text="", font=FONTS.get("tiny"),
                                          text_color=TEXT_MUTED)
        self.country_label.pack(anchor="w", pady=(10, 4))
        self.country_box = ctk.CTkComboBox(
            wrap, width=330, height=36, corner_radius=10,
            font=FONTS.get("body"), dropdown_font=FONTS.get("small"),
            border_color=BORDER, button_color=BORDER,
            button_hover_color=app.accent, values=list(self.catalogue))
        self.country_box.pack(anchor="w")

        self.image_title = ctk.CTkLabel(wrap, text="", font=FONTS.get("tiny"),
                                        text_color=TEXT_MUTED)
        self.image_title.pack(anchor="w", pady=(12, 4))
        picker = ctk.CTkFrame(wrap, fg_color="transparent")
        picker.pack(fill="x")
        self.preview = ctk.CTkLabel(picker, text="", width=40)
        self.preview.pack(side="left", padx=(0, 10))
        self.pick_btn = ctk.CTkButton(
            picker, text="", height=34, width=150, corner_radius=10,
            font=FONTS.get("small"), fg_color="transparent", border_width=1,
            border_color=BORDER, text_color=TEXT, hover_color=SURFACE_2,
            command=self._pick_image)
        self.pick_btn.pack(side="left")
        self.image_label = ctk.CTkLabel(picker, text="", font=FONTS.get("tiny"),
                                        text_color=TEXT_MUTED)
        self.image_label.pack(side="left", padx=10)

        self.error = ctk.CTkLabel(wrap, text="", font=FONTS.get("tiny"),
                                  text_color="#E5484D")
        self.error.pack(anchor="w", pady=(12, 0))

        self.buttons = ctk.CTkFrame(wrap, fg_color="transparent")
        self.buttons.pack(fill="x", pady=(14, 0))
        self.confirm_btn = ctk.CTkButton(
            self.buttons, text="", height=38, width=130, corner_radius=10,
            font=FONTS.get("cta"), text_color="#FFFFFF", fg_color=app.accent,
            hover_color=app.accent_hover, command=self._confirm)
        self.confirm_btn.pack(side="right")
        self.cancel_btn = ctk.CTkButton(
            self.buttons, text="", height=38, width=110, corner_radius=10,
            font=FONTS.get("small"), fg_color="transparent", border_width=1,
            border_color=BORDER, text_color=TEXT_MUTED, hover_color=SURFACE_2,
            command=self.close)
        self.cancel_btn.pack(side="right", padx=8)
        # "Undo the replacement" button: built once and for all, shown or
        # hidden depending on the place. pack_forget() does not destroy the
        # widget, so showing it again costs nothing.
        self.restore_btn = ctk.CTkButton(
            self.buttons, text="", height=38, width=150, corner_radius=10,
            font=FONTS.get("small"), fg_color="transparent", border_width=1,
            border_color=REPLACED, text_color=REPLACED, hover_color=SURFACE_2,
            command=self._restore)

        self.bind("<Return>", lambda _e: self._confirm())
        self.bind("<Escape>", lambda _e: self.close())
        self.withdraw()             # built, but not shown yet

    # ---------- opening / closing ----------
    def open_for(self, pot_index, slot_index):
        """Restacks the box onto a place and shows it."""
        self.pot_index, self.slot_index = pot_index, slot_index
        self.image_path = None
        club = self.model.club_at(pot_index, slot_index)

        self._apply_texts()

        badge = club_image(self.comp, club, box=(26, 26), accent=self.app.accent,
                           custom_path=self.model.logo_for(club))
        self.leaving_badge.configure(image=badge)
        self.leaving_name.configure(
            text="%s  -  %s" % (club, self.model.country_of(club)))

        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, club)

        values = association_values(self.model, self.catalogue)
        if values != self._values:
            # configure(values=...) rebuilds the whole drop-down menu.
            # It only changes after a replacement that introduces a new
            # country: no need to redo it on every opening.
            self.country_box.configure(values=values)
            self._values = values
        self.country_box.set(self.model.country_of(club))

        self.preview.configure(image=club_image(
            self.comp, club, box=(34, 34), accent=self.app.accent,
            custom_path=self.model.logo_for(club)))
        self.error.configure(text="")

        if self.model.is_replaced(club):
            self.restore_btn.pack(side="left")
        else:
            self.restore_btn.pack_forget()

        self.deiconify()
        self.lift()
        self._centre_on(self.master)
        self.name_entry.focus_set()
        # grab_set before the window is placed raises a TclError on
        # Windows: we let Tk finish its work first.
        self.after(120, self._grab)

    def close(self):
        try:
            self.grab_release()
        except tkinter.TclError:
            pass
        self.withdraw()

    def _apply_texts(self):
        """Rewrites everything that is translated. Replayed on every opening.

        The box survives language and theme changes since it is no longer
        rebuilt: if nobody rewrites its labels, it stays in the language
        of the first click of the session.
        """
        app = self.app
        self.title(app.t("replace_title"))
        self.h_title.configure(text=app.t("replace_title"))
        self.h_hint.configure(text=app.t("replace_h"))
        self.leaving_caption.configure(text=app.t("replace_current"))
        self.name_label.configure(text=app.t("f_name"))
        self.country_label.configure(text=app.t("f_country"))
        self.image_title.configure(text=app.t("f_image"))
        self.pick_btn.configure(text=app.t("choose_image"))
        self.image_label.configure(text=app.t("no_image"))
        self.confirm_btn.configure(text=app.t("confirm"),
                                   fg_color=app.accent,
                                   hover_color=app.accent_hover)
        self.cancel_btn.configure(text=app.t("cancel"))
        self.restore_btn.configure(text=app.t("restore"))
        self.country_box.configure(button_hover_color=app.accent)

    def _centre_on(self, master):
        """Places the box in the middle of the main window.

        Without this, it appears wherever the window manager decides,
        often at the top left of the screen, far from the club that was
        just clicked. update_idletasks() first: before it, winfo_width()
        returns 1, not the real width.
        """
        try:
            self.update_idletasks()
            x = master.winfo_rootx() + (master.winfo_width() - self.winfo_width()) // 2
            y = master.winfo_rooty() + (master.winfo_height() - self.winfo_height()) // 3
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
        except tkinter.TclError:
            pass                        # placement impossible: never mind, not important

    def _grab(self):
        try:
            if self.winfo_viewable():
                self.grab_set()
        except tkinter.TclError:
            pass

    def _field(self, parent):
        label = ctk.CTkLabel(parent, text="", font=FONTS.get("tiny"),
                             text_color=TEXT_MUTED)
        label.pack(anchor="w", pady=(10, 4))
        entry = ctk.CTkEntry(parent, width=330, height=36, corner_radius=10,
                             font=FONTS.get("body"), border_color=BORDER)
        entry.pack(anchor="w")
        return label, entry

    def _pick_image(self):
        path = filedialog.askopenfilename(
            parent=self, title=self.app.t("f_image"),
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.gif *.bmp"),
                       ("All files", "*.*")])
        if not path:
            return
        # We open it straight away: an unreadable file must be refused
        # here, not three screens later in the middle of the ceremony.
        try:
            Image.open(path).convert("RGBA")
        except Exception:
            self.error.configure(text=self.app.t("err_image"))
            return
        self.image_path = path
        self.error.configure(text="")
        name = path.replace("\\", "/").rsplit("/", 1)[-1]
        self.image_label.configure(text=name[:28])
        self.preview.configure(image=club_image(
            self.comp, self.name_entry.get().strip() or "?", box=(34, 34),
            accent=self.app.accent, custom_path=path))

    def _confirm(self):
        name = self.name_entry.get().strip()
        country = self.country_box.get().strip()
        problem = self.model.validate(self.pot_index, self.slot_index, name)
        if problem is None and not country:
            problem = "err_country"
        if problem:
            self.error.configure(text=self.app.t(problem))
            return
        self.model.replace(self.pot_index, self.slot_index, name, country,
                           self.image_path)
        self._done()

    def _restore(self):
        self.model.restore(self.pot_index, self.slot_index)
        self._done()

    def _done(self):
        # We tell the view WHICH place was touched: it then repaints a
        # single chip instead of the board's thirty-six.
        if self.on_done is not None:
            self.on_done(self.pot_index, self.slot_index)
        self.close()



# =====================================================================
#  FORBIDDEN FIXTURES
# =====================================================================

class ConstraintsDialog(ctk.CTkToplevel):
    """
    Fixtures forbidden at home: "A does not host B".

    A constraint is an ORDERED pair. ("Liverpool", "Real Madrid") and
    ("Real Madrid", "Liverpool") are two DIFFERENT prohibitions, and both
    together mean "these two never meet". Hence two separate drop-down
    lists rather than one: a single field could not say in which
    direction the prohibition applies.

    Same discipline as ReplaceDialog: ONE instance for the whole session,
    withdraw/deiconify instead of build and destroy, and _apply_texts()
    replayed on every opening to follow the language.

    The list, for its part, is rebuilt on every change: it only holds a
    handful of rows, and an addition or a removal changes its height
    anyway.
    """

    LIST_HEIGHT = 190

    def __init__(self, master, app, comp, model, on_change=None):
        super().__init__(master, fg_color=SURFACE)
        self.app, self.comp, self.model = app, comp, model
        self.on_change = on_change
        self._values = None          # last content of the drop-down lists

        self.resizable(False, False)
        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", self.close)

        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.pack(padx=26, pady=22)

        self.h_title = ctk.CTkLabel(wrap, text="", font=app.fonts["h2"],
                                    text_color=TEXT)
        self.h_title.pack(anchor="w")
        self.h_hint = ctk.CTkLabel(wrap, text="", font=FONTS.get("small"),
                                   text_color=TEXT_MUTED, justify="left",
                                   wraplength=480)
        self.h_hint.pack(anchor="w", pady=(4, 14))

        picker = ctk.CTkFrame(wrap, fg_color="transparent")
        picker.pack(fill="x")

        left = ctk.CTkFrame(picker, fg_color="transparent")
        left.pack(side="left")
        self.host_label = ctk.CTkLabel(left, text="", font=FONTS.get("tiny"),
                                       text_color=TEXT_MUTED)
        self.host_label.pack(anchor="w", pady=(0, 4))
        self.host_box = self._combo(left)
        self.host_box.pack()

        self.arrow = ctk.CTkLabel(picker, text="\u2192", font=app.fonts["h2"],
                                  text_color=TEXT_MUTED, width=30)
        self.arrow.pack(side="left", padx=6, pady=(18, 0))

        right = ctk.CTkFrame(picker, fg_color="transparent")
        right.pack(side="left")
        self.guest_label = ctk.CTkLabel(right, text="", font=FONTS.get("tiny"),
                                        text_color=TEXT_MUTED)
        self.guest_label.pack(anchor="w", pady=(0, 4))
        self.guest_box = self._combo(right)
        self.guest_box.pack()

        self.add_btn = ctk.CTkButton(
            picker, text="", height=36, width=90, corner_radius=10,
            font=FONTS.get("small"), text_color="#FFFFFF",
            fg_color=app.accent, hover_color=app.accent_hover,
            command=self._add)
        self.add_btn.pack(side="left", padx=(10, 0), pady=(18, 0))

        self.error = ctk.CTkLabel(wrap, text="", font=FONTS.get("tiny"),
                                  text_color="#E5484D")
        self.error.pack(anchor="w", pady=(10, 0))

        self.listbox = ctk.CTkScrollableFrame(
            wrap, fg_color=SURFACE_2, corner_radius=10, width=470,
            height=self.LIST_HEIGHT)
        self.listbox.pack(fill="x", pady=(4, 0))

        self.count_label = ctk.CTkLabel(wrap, text="", font=FONTS.get("tiny"),
                                        text_color=TEXT_MUTED)
        self.count_label.pack(anchor="w", pady=(8, 0))

        self.close_btn = ctk.CTkButton(
            wrap, text="", height=38, width=120, corner_radius=10,
            font=FONTS.get("cta"), text_color="#FFFFFF", fg_color=app.accent,
            hover_color=app.accent_hover, command=self.close)
        self.close_btn.pack(anchor="e", pady=(14, 0))

        self.bind("<Return>", lambda _e: self._add())
        self.bind("<Escape>", lambda _e: self.close())
        self.withdraw()

    # ---------- construction ----------
    def _combo(self, parent):
        return ctk.CTkComboBox(
            parent, width=190, height=36, corner_radius=10,
            font=FONTS.get("small"), dropdown_font=FONTS.get("small"),
            border_color=BORDER, button_color=BORDER,
            button_hover_color=self.app.accent, values=[])

    # ---------- opening / closing ----------
    def open(self):
        self._apply_texts()
        self._fill_boxes()
        self._rebuild()
        self.error.configure(text="")
        self.deiconify()
        self.lift()
        self._centre_on(self.master)
        # grab_set before the window is placed raises a TclError on
        # Windows: we let Tk finish its work first.
        self.after(120, self._grab)

    def close(self):
        try:
            self.grab_release()
        except tkinter.TclError:
            pass
        self.withdraw()

    def _apply_texts(self):
        app = self.app
        self.title(app.t("cst_title"))
        self.h_title.configure(text=app.t("cst_title"))
        self.h_hint.configure(text=app.t("cst_h"))
        self.host_label.configure(text=app.t("cst_host"))
        self.guest_label.configure(text=app.t("cst_guest"))
        self.add_btn.configure(text=app.t("cst_add"), fg_color=app.accent,
                               hover_color=app.accent_hover)
        self.close_btn.configure(text=app.t("close"), fg_color=app.accent,
                                 hover_color=app.accent_hover)
        for box in (self.host_box, self.guest_box):
            box.configure(button_hover_color=app.accent)

    def _fill_boxes(self):
        """The 36 clubs, in alphabetical order, in both lists.

        configure(values=...) rebuilds the whole drop-down menu, so we only
        redo it if the list has really changed, that is, after a club
        replacement, not on every opening.
        """
        values = sorted(self.model.all_clubs(), key=str.casefold)
        if values != self._values:
            for box in (self.host_box, self.guest_box):
                box.configure(values=values)
            self._values = values
            if values:
                self.host_box.set(values[0])
                self.guest_box.set(values[1] if len(values) > 1 else values[0])

    # ---------- the list ----------
    def _rebuild(self):
        for child in self.listbox.winfo_children():
            child.destroy()

        pairs = self.model.constraint_list()
        self.count_label.configure(text=self.app.t("cst_count", n=len(pairs)))

        if not pairs:
            ctk.CTkLabel(self.listbox, text=self.app.t("cst_none"),
                         font=FONTS.get("tiny"),
                         text_color=TEXT_MUTED).pack(anchor="w", padx=10,
                                                     pady=10)
            return

        for host, guest in pairs:
            row = ctk.CTkFrame(self.listbox, fg_color="transparent")
            row.pack(fill="x", padx=6, pady=2)
            ctk.CTkButton(
                row, text="\u2715", width=28, height=28, corner_radius=8,
                font=FONTS.get("tiny"), fg_color="transparent",
                border_width=1, border_color=BORDER, text_color=TEXT_MUTED,
                hover_color=SURFACE,
                # h=host, g=guest: without these default values, the
                # lambda would capture the loop VARIABLES, not their
                # contents, and all eight buttons would delete the last
                # pair. The classic closure trap in a loop.
                command=lambda h=host, g=guest: self._remove(h, g),
            ).pack(side="left", padx=(0, 8))
            ctk.CTkLabel(row, text="%s   \u2192   %s" % (host, guest),
                         font=FONTS.get("small"), text_color=TEXT,
                         anchor="w").pack(side="left", fill="x")

    # ---------- actions ----------
    def _add(self):
        problem = self.model.add_constraint(self.host_box.get(),
                                            self.guest_box.get())
        if problem:
            self.error.configure(text=self.app.t(problem))
            return
        self.error.configure(text="")
        self._rebuild()
        self._notify()

    def _remove(self, host, guest):
        self.model.remove_constraint(host, guest)
        self.error.configure(text="")
        self._rebuild()
        self._notify()

    def _notify(self):
        if self.on_change is not None:
            self.on_change()

    # ---------- placement ----------
    def _grab(self):
        try:
            if self.winfo_viewable():
                self.grab_set()
        except tkinter.TclError:
            pass

    def _centre_on(self, master):
        try:
            self.update_idletasks()
            x = master.winfo_rootx() + (master.winfo_width() - self.winfo_width()) // 2
            y = master.winfo_rooty() + (master.winfo_height() - self.winfo_height()) // 3
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
        except tkinter.TclError:
            pass


# =====================================================================
#  A BOX THAT SAYS SOMETHING
# =====================================================================

class MessageDialog(ctk.CTkToplevel):
    """
    A title, a sentence, and a list of lines that scrolls if needed.

    Used for the report on a JSON template: a refused file can have
    thirty-six faults, and showing them all at once saves correcting the
    file one error at a time.
    """

    MAX_LINES = 14          # beyond this we summarise: nobody reads 36 lines

    def __init__(self, master, app, title, summary, lines=(), tone="error"):
        super().__init__(master, fg_color=SURFACE)
        self.app = app
        self.title(title)
        self.resizable(False, False)
        self.transient(master)

        accent = {"error": "#E5484D", "warn": REPLACED,
                  "ok": app.accent}.get(tone, app.accent)

        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.pack(padx=26, pady=22)

        ctk.CTkLabel(wrap, text=title, font=app.fonts["h2"],
                     text_color=TEXT).pack(anchor="w")
        ctk.CTkLabel(wrap, text=summary, font=FONTS.get("small"),
                     text_color=TEXT_MUTED, justify="left",
                     wraplength=460).pack(anchor="w", pady=(4, 12))

        lines = list(lines)
        if lines:
            box = ctk.CTkFrame(wrap, fg_color=SURFACE_2, corner_radius=10)
            box.pack(fill="x")
            shown = lines[:self.MAX_LINES]
            for text in shown:
                row = flat_frame(box, SURFACE_2)
                row.pack(fill="x", padx=12, pady=1)
                flat_label(row, "•", SURFACE_2, accent,
                           font=FONTS.get("tiny")).pack(side="left", padx=(0, 6))
                flat_label(row, text, SURFACE_2, TEXT, font=FONTS.get("tiny"),
                           justify="left", anchor="w",
                           wraplength=430).pack(side="left", fill="x")
            if len(lines) > self.MAX_LINES:
                flat_label(box, "+ %d" % (len(lines) - self.MAX_LINES),
                           SURFACE_2, TEXT_MUTED,
                           font=FONTS.get("tiny")).pack(anchor="w", padx=12,
                                                        pady=(2, 0))
            ctk.CTkFrame(box, fg_color="transparent", height=8).pack()

        ctk.CTkButton(wrap, text=app.t("close"), height=38, width=120,
                      corner_radius=10, font=FONTS.get("cta"),
                      text_color="#FFFFFF", fg_color=app.accent,
                      hover_color=app.accent_hover,
                      command=self.destroy).pack(anchor="e", pady=(16, 0))

        self.bind("<Return>", lambda _e: self.destroy())
        self.bind("<Escape>", lambda _e: self.destroy())
        self.after(120, self._grab)
        self.after(10, lambda: self._centre_on(master))

    def _grab(self):
        try:
            self.grab_set()
        except tkinter.TclError:
            pass

    def _centre_on(self, master):
        try:
            self.update_idletasks()
            x = master.winfo_rootx() + (master.winfo_width() - self.winfo_width()) // 2
            y = master.winfo_rooty() + (master.winfo_height() - self.winfo_height()) // 3
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
        except tkinter.TclError:
            pass


# =====================================================================
#  THE CEREMONY
# =====================================================================

class OpponentCard(ctk.CTkFrame):
    """A drawn opponent: side (home / away), pot, badge."""

    def __init__(self, master, comp, club, pot_number, home, accent,
                 width=196, height=42, logo_path=None, **kwargs):
        super().__init__(master, width=width, height=height,
                         corner_radius=CHIP_RADIUS, fg_color=CARD,
                         border_width=1, border_color=CHIP_BORDER, **kwargs)
        self.pack_propagate(False)

        side = HOME if home else AWAY
        # A strip of colour on the left: home / away can be read without
        # reading the word, even out of the corner of the eye.
        ctk.CTkFrame(self, width=4, corner_radius=2,
                     fg_color=side).pack(side="left", fill="y", padx=(4, 6),
                                         pady=6)
        ctk.CTkLabel(self, text="", width=22,
                     image=club_image(comp, club, box=(22, 22), accent=accent,
                                      custom_path=logo_path)).pack(side="left")
        ctk.CTkLabel(self, text=club, font=FONTS.get("small"), text_color=TEXT,
                     anchor="w").pack(side="left", padx=(8, 0), fill="x",
                                      expand=True)
        ctk.CTkLabel(self, text=f"P{pot_number}", width=24, height=18,
                     corner_radius=9, fg_color=SURFACE_2,
                     font=FONTS.get("tiny"),
                     text_color=TEXT_MUTED).pack(side="right", padx=(4, 8))


class BowlStrip(ctk.CTkFrame):
    """The balls of the current pot: filled = to come, empty = drawn."""

    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", height=30, **kwargs)
        self.app = app
        self.label = ctk.CTkLabel(self, text="", font=FONTS.get("badge"),
                                  text_color=TEXT_MUTED, width=76, anchor="w")
        self.label.pack(side="left")
        self.row = ctk.CTkFrame(self, fg_color="transparent")
        self.row.pack(side="left")
        self.dots = []

    def set_pot(self, pot_number, count):
        for dot in self.dots:
            dot.destroy()
        self.dots = []
        self.label.configure(text=self.app.t("pot_n", n=pot_number))
        for _ in range(count):
            dot = ctk.CTkFrame(self.row, width=13, height=13, corner_radius=7,
                               fg_color=self.app.accent)
            dot.pack(side="left", padx=3)
            self.dots.append(dot)

    def pop(self, index):
        """Ball number `index` has just come out of the bowl."""
        if 0 <= index < len(self.dots):
            tr.animate_color(self.dots[index], "fg_color", SURFACE_2, 260)

    def anchor_dot(self, index):
        """The widget the ball must fly from."""
        if 0 <= index < len(self.dots):
            return self.dots[index]
        return self.row


class MatchRow(tkinter.Canvas):
    """A matchday fixture: home on the left, away on the right.

    One plain canvas, like ClubChip (same cached rounded background). It
    used to be a CTkFrame shell around three Tk labels: about 13 ms per
    row, so a matchday of 18 fixtures had to be built in slices. Colours
    are resolved once, as before: DrawView rebuilds the results panel when
    the theme changes.
    """

    # Same size as ClubChip.BADGE on purpose: club_photo() caches by size,
    # so the 36 badges decoded for the pots are reused here as they are
    # (decoding them again at 20 px cost about 45 ms per results screen).
    BADGE = ClubChip.BADGE

    def __init__(self, master, comp, home, away, accent, width=330, height=36,
                 home_logo=None, away_logo=None, **kwargs):
        s = scaling(master)
        w, h = round(width * s), round(height * s)
        behind = _colour_behind_widget(master)
        super().__init__(master, width=w, height=h, bg=behind,
                         highlightthickness=0, bd=0, **kwargs)
        self.create_image(0, 0, anchor="nw", image=_chip_background(
            w, h, round(CHIP_RADIUS * s), tr.resolve_color(CARD),
            tr.resolve_color(CHIP_BORDER), max(1, round(s)), behind))

        font = tk_font(self, 12)
        tiny = tk_font(self, 11)
        pad, badge, gap = round(8 * s), round(self.BADGE * s), round(6 * s)
        mid, centre = h // 2, w // 2
        half = centre - round(12 * s) - pad - badge - gap

        self._photos = (club_photo(comp, home, badge, accent, home_logo),
                        club_photo(comp, away, badge, accent, away_logo))
        if self._photos[0] is not None:
            self.create_image(pad, mid, anchor="w", image=self._photos[0])
        if self._photos[1] is not None:
            self.create_image(w - pad, mid, anchor="e", image=self._photos[1])
        self.create_text(pad + badge + gap, mid, anchor="w", font=font,
                         text=_fit(font, home, half),
                         fill=tr.resolve_color(TEXT))
        self.create_text(w - pad - badge - gap, mid, anchor="e", font=font,
                         text=_fit(font, away, half),
                         fill=tr.resolve_color(TEXT_MUTED))
        self.create_text(centre, mid, text="v", font=tiny,
                         fill=tr.resolve_color(TEXT_MUTED))


_DOT_CACHE = {}


def _dot_image(d, colour, behind):
    """An antialiased round dot (Tk's own ovals are jagged at 10 px)."""
    key = (d, colour, behind)
    photo = _DOT_CACHE.get(key)
    if photo is None:
        from PIL import ImageDraw, ImageTk
        k = 4
        img = Image.new("RGB", (d * k, d * k), behind)
        ImageDraw.Draw(img).ellipse((0, 0, d * k - 1, d * k - 1), fill=colour)
        photo = ImageTk.PhotoImage(img.resize((d, d), Image.LANCZOS))
        _DOT_CACHE[key] = photo
    return photo


class Spinner(tkinter.Canvas):
    """
    Three dots that breathe during the calculation.

    Deliberately not a CTkProgressBar: the draw cannot say how far along
    it is (a backtrack can undo half the work already done), so a bar that
    moved forward would be lying.

    One plain canvas with three ovals and ONE timer. It used to be three
    CTkFrame dots, each with its own 60 fps colour fade: every frame
    redrew CustomTkinter canvases, while the draw thread held the GIL, and
    one frame of the spinner was measured at about 75 ms. Now a frame is
    three itemconfigure() calls.
    """

    STEP_MS = 230        # time spent on each dot
    FRAME_MS = 33        # about 30 frames per second is plenty for a dot

    def __init__(self, master, app, count=3, **kwargs):
        s = scaling(master)
        self._d, self._gap = round(10 * s), round(8 * s)
        w = count * self._d + (count - 1) * self._gap
        super().__init__(master, width=w, height=self._d,
                         bg=_colour_behind_widget(master),
                         highlightthickness=0, bd=0, **kwargs)
        self.app = app
        self.dots = [self.create_image(i * (self._d + self._gap), 0, anchor="nw")
                     for i in range(count)]
        self._job = None
        self._t0 = 0.0
        # The 9 glow levels are drawn NOW, on the click, before the draw
        # thread starts. Drawn lazily, the first frames made Pillow images
        # while the engine held the GIL: about 150 ms of stalls spread over
        # the first turns of the spinner.
        self._images = self._render_levels()

    def _render_levels(self):
        rest, lit = tr.resolve_color(SURFACE_2), self.app.accent
        behind = self.cget("bg")
        return [_dot_image(self._d, tr.lerp_color(self, rest, lit, level / 8) or rest,
                           behind)
                for level in range(9)]

    def start(self):
        self.stop()
        self._t0 = time.perf_counter()
        self._tick()

    def _tick(self):
        elapsed = (time.perf_counter() - self._t0) * 1000
        pos = (elapsed / self.STEP_MS) % len(self.dots)   # 0..count, fractional
        try:
            for i, dot in enumerate(self.dots):
                # 1 on the active dot, fading to 0 over the next step.
                # Rounded to 8 levels so only a handful of images exist.
                level = round(max(0.0, 1.0 - ((pos - i) % len(self.dots))) * 8)
                self.itemconfigure(dot, image=self._images[level])
            self._job = self.after(self.FRAME_MS, self._tick)
        except tkinter.TclError:
            self._job = None                 # destroyed meanwhile

    def stop(self):
        if self._job is not None:
            try:
                self.after_cancel(self._job)
            except (tkinter.TclError, ValueError):
                pass
            self._job = None

    def destroy(self):
        self.stop()
        super().destroy()


def flying_ball(parent, accent, box=(74, 74), label=None):
    """The ball crossing the screen. Placed with place(), never with pack()."""
    return ctk.CTkLabel(parent, text="", fg_color="transparent",
                        image=ball_image(accent, box=box, label=label))
