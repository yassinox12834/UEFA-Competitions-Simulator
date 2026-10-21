"""
canvas_views.py - the three large tables of the results screen,
drawn on a tkinter.Canvas.

Why a Canvas. Building a Frame and a Label per cell would mean 36 rows x
11 columns = nearly 800 widgets for the standings alone, which would have
to be built in batches so as not to freeze the window. A Canvas is only
ONE widget; a cell in it is an "item" (a piece of text, a rectangle) that
Tk draws without creating a window. The whole standings table is drawn in
a few milliseconds, in one go, and hovering over a row comes down to
moving a single rectangle.

What a Canvas does not do by itself, and what is therefore done here:
    - HiDPI scaling: every measurement goes through self.px() and the
      fonts through fonts.tk_font(), already multiplied;
    - colours (light, dark): resolved at every draw;
    - the mouse wheel: bound on the canvas itself (Windows/mac:
      <MouseWheel>, Linux: <Button-4>/<Button-5>);
    - resizing: we redraw when the width changes, with a short delay so as
      not to redraw 60 times during a drag.

Contents:
    ScrollCanvas    the base: canvas + scrollbar + fixed header
    LeagueTable     the league-phase standings, with form
    ProbTable       the Monte Carlo probabilities, heat-map cells, sorted
                    by clicking a header
    BracketView     the knockout bracket, from the play-offs to the final,
                    clickable
"""

import tkinter

import customtkinter as ctk

import transition as tr
from config import (BORDER, CARD, DRAW_C, GOLD, LOSS, SURFACE,
                    SURFACE_2, TEXT, TEXT_FAINT, TEXT_MUTED, WIN, ZONE_OUT,
                    ZONE_PO, ZONE_R16)
from fonts import scaling, tk_font
from images import club_photo

C = tr.resolve_color


def _mix(widget, a, b, t):
    """Colour between a and b (t from 0 to 1), as hex. a and b accept a pair."""
    return tr.lerp_color(widget, a, b, max(0.0, min(1.0, t))) or C(b)


def _ink_on(hex_colour):
    """White or dark ink, depending on the background's luminance (WCAG, approximate)."""
    h = hex_colour.lstrip("#")
    if len(h) != 6:
        return "#FFFFFF"
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return "#0F131A" if lum > 0.55 else "#FFFFFF"


def _fit(font, text, width):
    """Truncates `text` with an ellipsis so that it fits within `width` pixels."""
    if width <= 0:
        return ""
    if font.measure(text) <= width:
        return text
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if font.measure(text[:mid] + "…") <= width:
            lo = mid
        else:
            hi = mid - 1
    return text[:lo].rstrip() + "…"


# =====================================================================
#  BASE
# =====================================================================

class ScrollCanvas(ctk.CTkFrame):
    """A fixed header, a scrolling body, a redraw at every width."""

    HEADER = 0          # header height in logical px, 0 = no header
    MAX_WIDTH = None    # maximum content width, centred beyond it
    XSCROLL = False

    def __init__(self, master, app, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self.app = app
        self.s = scaling(self)
        bg = C(SURFACE)
        self.head = None
        if self.HEADER:
            self.head = tkinter.Canvas(self, height=self.px(self.HEADER), bg=bg,
                                       highlightthickness=0, bd=0)
            self.head.pack(fill="x", padx=(0, self.px(14)))
        # The horizontal bar is packed BEFORE the body: with pack, a widget with
        # expand=True takes all the remaining space, and anything packed after it
        # gets none.
        self.xbar = None
        if self.XSCROLL:
            self.xbar = ctk.CTkScrollbar(self, orientation="horizontal",
                                         command=self._xview, height=12)
            self.xbar.pack(side="bottom", fill="x")
        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.pack(fill="both", expand=True)
        self.canvas = tkinter.Canvas(wrap, bg=bg, highlightthickness=0, bd=0)
        self.ybar = ctk.CTkScrollbar(wrap, orientation="vertical",
                                     command=self.canvas.yview, width=12)
        self.ybar.pack(side="right", fill="y")
        if self.xbar is not None:
            self.canvas.configure(xscrollcommand=self.xbar.set)
        self.canvas.configure(yscrollcommand=self.ybar.set)
        self.canvas.pack(side="left", fill="both", expand=True)

        self._width = None
        self._pending = None
        self.canvas.bind("<Configure>", self._on_configure)
        for widget in (self.canvas, self.head):
            if widget is None:
                continue
            widget.bind("<MouseWheel>", self._on_wheel)
            widget.bind("<Shift-MouseWheel>", self._on_hwheel)
            widget.bind("<Button-4>", lambda e: self._scroll(-3))
            widget.bind("<Button-5>", lambda e: self._scroll(3))
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", lambda e: self.on_hover(None))
        self.canvas.bind("<Button-1>", self._on_click)
        if self.head is not None:
            self.head.bind("<Button-1>", self._on_head_click)

    # ---------- units ----------
    def px(self, v):
        return int(round(v * self.s))

    def font(self, size, weight="normal"):
        return tk_font(self, size, weight)

    # ---------- scrolling ----------
    def _xview(self, *args):
        self.canvas.xview(*args)
        if self.head is not None:
            self.head.xview(*args)

    def _scroll(self, units):
        if self.canvas.yview() != (0.0, 1.0):
            self.canvas.yview_scroll(units, "units")

    def _on_wheel(self, event):
        # Windows: delta = +-120 per notch. macOS: small values.
        step = -event.delta // 120 if abs(event.delta) >= 120 else -event.delta
        self._scroll(int(step) * 3 or (-1 if event.delta > 0 else 1))
        return "break"

    def _on_hwheel(self, event):
        if self.XSCROLL:
            step = -event.delta // 120 if abs(event.delta) >= 120 else -event.delta
            self._xview("scroll", int(step) * 3, "units")
        return "break"

    # ---------- redraw ----------
    def _on_configure(self, event):
        if event.width == self._width:
            return
        self._width = event.width
        if self._pending is not None:
            self.after_cancel(self._pending)
        self._pending = self.after(30, self.redraw)

    def redraw(self):
        self._pending = None
        width = self.canvas.winfo_width()
        if width <= 1:
            return
        for c in (self.canvas, self.head):
            if c is not None:
                c.delete("all")
                c.configure(bg=C(SURFACE))
        self.canvas.configure(yscrollincrement=self.px(12),
                              xscrollincrement=self.px(12))
        total_w, height = self.draw(width)
        total_w = max(total_w, width)
        self.canvas.configure(scrollregion=(0, 0, total_w, height))
        if self.head is not None:
            self.head.configure(scrollregion=(0, 0, total_w, self.px(self.HEADER)))

    def content_box(self, width):
        """(x0, usable width): the content is centred below MAX_WIDTH."""
        pad = self.px(4)
        usable = width - 2 * pad
        if self.MAX_WIDTH:
            usable = min(usable, self.px(self.MAX_WIDTH))
        return (width - usable) // 2, usable

    # ---------- to override ----------
    def draw(self, width):
        return width, 0

    def on_hover(self, item):
        pass

    def _on_motion(self, event):
        self.on_hover((self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)))

    def _on_click(self, event):
        self.on_click(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))

    def on_click(self, x, y):
        pass

    def _on_head_click(self, event):
        self.on_head_click(self.head.canvasx(event.x))

    def on_head_click(self, x):
        pass

    def photo(self, club, size):
        view = self.master_view
        return club_photo(view.comp, club, self.px(size), self.app.accent,
                          view._logo(club))


# =====================================================================
#  STANDINGS
# =====================================================================

class LeagueTable(ScrollCanvas):
    HEADER = 34
    MAX_WIDTH = 980
    ROW = 36

    def __init__(self, master, app, view, result):
        self.master_view = view
        self.result = result
        self.form = self._form(result)
        self._rows_y = []
        super().__init__(master, app)
        self._hover_item = None

    @staticmethod
    def _form(result):
        """{club: ['W', 'D', 'L', ...]} in matchday order."""
        form = {}
        for day in result.league:
            for m in day:
                if m.home_goals > m.away_goals:
                    h, a = "W", "L"
                elif m.home_goals < m.away_goals:
                    h, a = "L", "W"
                else:
                    h = a = "D"
                form.setdefault(m.home, []).append(h)
                form.setdefault(m.away, []).append(a)
        return form

    def _columns(self, x0, usable):
        """[(key, title, right_x, width, anchor)]: the club takes the rest."""
        t = self.app.t
        fixed = [("P", "P", 34), ("W", "W", 34), ("D", "D", 34), ("L", "L", 34),
                 ("GF", "GF", 42), ("GA", "GA", 42), ("GD", "GD", 50),
                 ("Pts", "Pts", 50), ("form", t("col_form"), 150)]
        widths = [self.px(w) for _, _, w in fixed]
        rank_w, crest_w = self.px(44), self.px(34)
        club_w = max(self.px(140), usable - rank_w - crest_w - sum(widths) - self.px(12))
        cols = [("rank", "#", x0 + rank_w - self.px(10), rank_w, "e"),
                ("club", t("col_club"), x0 + rank_w + crest_w, club_w, "w")]
        x = x0 + rank_w + crest_w + club_w
        for (key, title, _), w in zip(fixed, widths):
            x += w
            anchor = "center" if key == "form" else "e"
            cols.append((key, title, x - (w // 2 if key == "form" else self.px(8)), w, anchor))
        return cols, x - x0

    def draw(self, width):
        cv, head = self.canvas, self.head
        x0, usable = self.content_box(width)
        cols, used = self._columns(x0, usable)
        bold = self.font(12, "bold")
        body = self.font(13)
        body_b = self.font(13, "bold")
        small = self.font(11, "bold")

        # Header
        head.create_rectangle(x0, 0, x0 + usable, self.px(self.HEADER),
                              fill=C(SURFACE_2), width=0)
        for key, title, x, w, anchor in cols:
            head.create_text(x, self.px(self.HEADER) // 2, text=title,
                             anchor=anchor, fill=C(TEXT_MUTED), font=small)

        row_h = self.px(self.ROW)
        card, card_alt = C(CARD), _mix(self, CARD, SURFACE_2, 0.45)
        self._rows_y = []
        self._x0, self._usable = x0, usable
        y = 0
        zones = [(8, ZONE_R16), (24, ZONE_PO), (36, ZONE_OUT)]
        for i, r in enumerate(self.result.table):
            zone = next(c for limit, c in zones if r.rank <= limit)
            cv.create_rectangle(x0, y, x0 + usable, y + row_h,
                                fill=card if i % 2 == 0 else card_alt, width=0)
            cv.create_rectangle(x0, y, x0 + self.px(4), y + row_h,
                                fill=C(zone), width=0)
            mid = y + row_h // 2
            for key, title, x, w, anchor in cols:
                if key == "rank":
                    cv.create_text(x, mid, text=str(r.rank), anchor="e",
                                   fill=C(zone), font=bold)
                elif key == "club":
                    photo = self.photo(r.club, 22)
                    if photo is not None:
                        cv.create_image(x - self.px(17), mid, image=photo)
                    cv.create_text(x, mid, anchor="w", fill=C(TEXT), font=body,
                                   text=_fit(body, r.club, w - self.px(8)))
                elif key == "form":
                    self._draw_form(cv, x, mid, self.form.get(r.club, [])[-6:])
                else:
                    value = {"P": r.played, "W": r.wins, "D": r.draws, "L": r.losses,
                             "GF": r.gf, "GA": r.ga, "GD": r.gd, "Pts": r.points}[key]
                    text = f"{value:+d}" if key == "GD" else str(value)
                    colour = TEXT_MUTED
                    if key == "Pts":
                        colour = TEXT
                    elif key == "GD":
                        colour = WIN if value > 0 else LOSS if value < 0 else TEXT_MUTED
                    cv.create_text(x, mid, text=text, anchor="e", fill=C(colour),
                                   font=body_b if key == "Pts" else body)
            # Zone lines: below 8th place and below 24th place.
            if r.rank in (8, 24):
                cv.create_line(x0, y + row_h - 1, x0 + usable, y + row_h - 1,
                               fill=C(zone), dash=(4, 3))
            self._rows_y.append(y)
            y += row_h
        self._hover_item = cv.create_rectangle(0, 0, 0, 0, outline=self.app.accent,
                                               width=self.px(1), state="hidden")
        return x0 + used, y + self.px(8)

    def _draw_form(self, cv, cx, mid, results):
        """W/D/L badges, the most recent on the right."""
        size, gap = self.px(18), self.px(4)
        n = len(results)
        x = cx - (n * size + (n - 1) * gap) / 2
        letters = self.app.t("form_letters")          # "WDL" / "VND"
        font = self.font(10, "bold")
        for res in results:
            colour = {"W": WIN, "D": DRAW_C, "L": LOSS}[res]
            cv.create_rectangle(x, mid - size / 2, x + size, mid + size / 2,
                                fill=C(colour), width=0)
            cv.create_text(x + size / 2, mid, text=letters["WDL".index(res)],
                           fill="#FFFFFF", font=font)
            x += size + gap

    def on_hover(self, pos):
        if self._hover_item is None:
            return
        if pos is None:
            self.canvas.itemconfigure(self._hover_item, state="hidden")
            return
        x, y = pos
        i = int(y // self.px(self.ROW))
        if 0 <= i < len(self._rows_y) and self._x0 <= x <= self._x0 + self._usable:
            top = self._rows_y[i]
            self.canvas.coords(self._hover_item, self._x0 + 1, top + 1,
                               self._x0 + self._usable - 1, top + self.px(self.ROW) - 1)
            self.canvas.itemconfigure(self._hover_item, state="normal")
        else:
            self.canvas.itemconfigure(self._hover_item, state="hidden")


# =====================================================================
#  PROBABILITIES
# =====================================================================

class ProbTable(ScrollCanvas):
    HEADER = 34
    MAX_WIDTH = 980
    ROW = 34

    def __init__(self, master, app, view, mc, stages):
        self.master_view = view
        self.mc = mc
        self.stages = stages
        self.sort_key = "winner"
        self.rows = mc.rows()
        self._cols = []
        super().__init__(master, app)
        self._hover_item = None

    def _columns(self, x0, usable):
        t = self.app.t
        cell = self.px(74)
        pts_w = self.px(56)
        club_w = max(self.px(160), usable - pts_w - cell * len(self.stages) - self.px(40))
        cols = [("club", t("col_club"), x0 + self.px(40), club_w, "w"),
                ("pts", t("probs_pts"), x0 + self.px(40) + club_w + pts_w - self.px(8), pts_w, "e")]
        x = x0 + self.px(40) + club_w + pts_w
        for s in self.stages:
            cols.append((s, t("p_" + s), x + cell // 2, cell, "center"))
            x += cell
        return cols, x - x0

    def sorted_rows(self):
        key = self.sort_key
        if key == "club":
            return sorted(self.rows, key=lambda r: r[0])
        if key == "pts":
            return sorted(self.rows, key=lambda r: -r[1])
        order = list(self.stages)
        # Tie on the chosen column: break it with the furthest stage first
        # (the title, then the final...), then with points.
        return sorted(self.rows, key=lambda r: (-r[2][key],)
                      + tuple(-r[2][s] for s in reversed(order)) + (-r[1],))

    def draw(self, width):
        cv, head = self.canvas, self.head
        x0, usable = self.content_box(width)
        cols, used = self._columns(x0, usable)
        self._cols, self._x0, self._usable = cols, x0, usable
        small = self.font(11, "bold")
        body = self.font(13)
        cell_font = self.font(12, "bold")

        hh = self.px(self.HEADER)
        head.create_rectangle(x0, 0, x0 + usable, hh, fill=C(SURFACE_2), width=0)
        for key, title, x, w, anchor in cols:
            active = key == self.sort_key
            label = title + ("  ▾" if active else "")
            head.create_text(x, hh // 2, text=label, anchor=anchor,
                             fill=self.app.accent if active else C(TEXT_MUTED), font=small)

        row_h = self.px(self.ROW)
        card = C(CARD)
        accent = self.app.accent
        y = 0
        for i, (club, pts, probs) in enumerate(self.sorted_rows()):
            cv.create_rectangle(x0, y, x0 + usable, y + row_h, fill=card, width=0)
            mid = y + row_h // 2
            cv.create_text(x0 + self.px(20), mid, text=str(i + 1), anchor="e",
                           fill=C(TEXT_FAINT), font=small)
            for key, title, x, w, anchor in cols:
                if key == "club":
                    photo = self.photo(club, 22)
                    if photo is not None:
                        cv.create_image(x + self.px(10), mid, image=photo)
                    cv.create_text(x + self.px(28), mid, anchor="w", fill=C(TEXT),
                                   font=body, text=_fit(body, club, w - self.px(36)))
                elif key == "pts":
                    cv.create_text(x, mid, text=f"{pts:.1f}", anchor="e",
                                   fill=C(TEXT_MUTED), font=body)
                else:
                    p = probs[key]
                    pad = self.px(3)
                    left, right = x - w // 2 + pad, x + w // 2 - pad
                    colour = C(TEXT if p >= 0.05 else TEXT_MUTED)
                    if p > 0:
                        # Heat map: 0 % = the card colour, 100 % = the accent.
                        fill = _mix(self, CARD, accent, 0.08 + 0.80 * p)
                        cv.create_rectangle(left, y + pad, right, y + row_h - pad,
                                            fill=fill, width=0)
                        if p >= 0.05:
                            colour = _ink_on(fill)
                    text = "–" if p == 0 else "<1%" if p < 0.005 else f"{100 * p:.0f}%"
                    cv.create_text(x, mid, text=text, fill=colour, font=cell_font)
            cv.create_line(x0, y + row_h - 1, x0 + usable, y + row_h - 1,
                           fill=C(SURFACE))
            y += row_h
        self._n = len(self.rows)
        self._hover_item = cv.create_rectangle(0, 0, 0, 0, outline=accent,
                                               width=self.px(1), state="hidden")
        return x0 + used, y + self.px(8)

    def on_head_click(self, x):
        for key, title, cx, w, anchor in self._cols:
            left = cx if anchor == "w" else cx - w if anchor == "e" else cx - w // 2
            if left <= x <= left + w:
                self.sort_key = key
                self.redraw()
                return

    def on_hover(self, pos):
        if self._hover_item is None:
            return
        if pos is None:
            self.canvas.itemconfigure(self._hover_item, state="hidden")
            return
        x, y = pos
        i = int(y // self.px(self.ROW))
        if 0 <= i < self._n and self._x0 <= x <= self._x0 + self._usable:
            top = i * self.px(self.ROW)
            self.canvas.coords(self._hover_item, self._x0 + 1, top + 1,
                               self._x0 + self._usable - 1, top + self.px(self.ROW) - 2)
            self.canvas.itemconfigure(self._hover_item, state="normal")
        else:
            self.canvas.itemconfigure(self._hover_item, state="hidden")


# =====================================================================
#  KNOCKOUT BRACKET
# =====================================================================

class BracketView(ScrollCanvas):
    """Play-offs -> round of 16 -> quarter-finals -> semi-finals -> final, left to right.

    Each round-of-16 tie pits a top-8 club against the winner of ONE
    play-off: the two left-hand columns therefore line up row by row.
    After that, each round brings together two boxes of the previous
    round, in the fixed order of the bracket (QF_BRACKET), and sits midway
    between its two sources.
    """

    HEADER = 30
    XSCROLL = True
    BOX_H = 52
    PITCH = 62
    MIN_COL = 176
    GAP = 34

    def __init__(self, master, app, view, result, on_select):
        self.master_view = view
        self.result = result
        self.on_select = on_select
        self.boxes = []            # [(x0, y0, x1, y1, tie)]
        self.selected = result.rounds["final"][0]
        super().__init__(master, app)
        self._hover_item = None
        self._hover_tie = None

    # ---------- box order ----------
    def _layout(self):
        from model.knockout import QF_BRACKET
        rounds = self.result.rounds
        r16_by_tag = {tie.tag: tie for tie in rounds["r16"]}
        r16 = [r16_by_tag[tag] for pair in QF_BRACKET for tag in pair]
        feeder = {}
        for po in rounds["playoff"]:
            for tie in r16:
                if po.winner in (tie.a, tie.b):
                    feeder[id(tie)] = po
        playoffs = [feeder.get(id(tie)) for tie in r16]
        qf = sorted(rounds["qf"], key=lambda t: t.tag)
        sf = sorted(rounds["sf"], key=lambda t: t.tag)
        return [("playoff", playoffs), ("r16", r16), ("qf", qf), ("sf", sf),
                ("final", rounds["final"])]

    def draw(self, width):
        cv, head = self.canvas, self.head
        columns = self._layout()
        pad = self.px(8)
        gap = self.px(self.GAP)
        col_w = max(self.px(self.MIN_COL), (width - 2 * pad - gap * 4) // 5)
        total_w = 2 * pad + col_w * 5 + gap * 4
        box_h, pitch = self.px(self.BOX_H), self.px(self.PITCH)
        top = self.px(10)
        hh = self.px(self.HEADER)
        small = self.font(11, "bold")

        centres = []                      # vertical centres, per column
        self.boxes = []
        for c, (stage, ties) in enumerate(columns):
            x = pad + c * (col_w + gap)
            head.create_text(x + col_w // 2, hh // 2, fill=C(TEXT_MUTED), font=small,
                             text=self.app.t("ko_" + stage).upper())
            if c <= 1:
                ys = [top + i * pitch + box_h // 2 for i in range(len(ties))]
            else:
                prev = centres[-1]
                ys = [(prev[2 * i] + prev[2 * i + 1]) / 2 for i in range(len(ties))]
            centres.append(ys)
            for tie, cy in zip(ties, ys):
                if tie is None:
                    continue
                self._box(cv, x, cy - box_h / 2, col_w, box_h, tie,
                          final=stage == "final")
            # Connectors to the previous column.
            if c == 1:
                for cy in ys:
                    cv.create_line(x - gap, cy, x, cy, fill=C(BORDER), width=self.px(2))
            elif c >= 2:
                prev = centres[-2]
                xm = x - gap / 2
                for i, cy in enumerate(ys):
                    y1, y2 = prev[2 * i], prev[2 * i + 1]
                    cv.create_line(x - gap, y1, xm, y1, xm, y2, x - gap, y2,
                                   fill=C(BORDER), width=self.px(2))
                    cv.create_line(xm, cy, x, cy, fill=C(BORDER), width=self.px(2))
        height = top + len(columns[1][1]) * pitch + self.px(10)
        self._hover_item = cv.create_rectangle(0, 0, 0, 0, outline=self.app.accent,
                                               width=self.px(2), state="hidden")
        return total_w, height

    def _scores(self, tie, club):
        """The numbers to the right of the name: goals per leg, or something else depending on the method."""
        if tie.method == "oneshot":
            p = tie.p_advance if club == tie.a else 1 - tie.p_advance
            return [f"{100 * p:.0f}%"]
        cells = []
        for i, m in enumerate(tie.legs):
            goals = m.home_goals if m.home == club else m.away_goals
            last = i == len(tie.legs) - 1
            if last and tie.extra_time:
                goals += tie.extra_time[0] if club == tie.a else tie.extra_time[1]
            cells.append(str(goals))
        if tie.pens:
            mine = tie.pens[0] if club == tie.a else tie.pens[1]
            cells.append(f"({mine})")
        return cells

    def _box(self, cv, x, y, w, h, tie, final=False):
        winner_border = C(GOLD) if final else C(BORDER)
        fill = C(CARD)
        if tie is self.selected:
            fill = _mix(self, CARD, self.app.accent, 0.16)
        cv.create_rectangle(x, y, x + w, y + h, fill=fill, outline=winner_border,
                            width=self.px(2 if final else 1))
        name_f = self.font(12)
        name_b = self.font(12, "bold")
        num_f = self.font(12, "bold")
        row_h = h / 2
        cell_w = self.px(22)
        # a played the second leg at home: show it at the bottom, like the
        # official brackets (the club hosting last).
        for i, club in enumerate((tie.b, tie.a)):
            cy = y + row_h * i + row_h / 2
            won = club == tie.winner
            photo = self.photo(club, 18)
            if photo is not None:
                cv.create_image(x + self.px(15), cy, image=photo)
            cells = self._scores(tie, club)
            cells_w = sum(max(cell_w, name_f.measure(c) + self.px(6)) for c in cells)
            font = name_b if won else name_f
            cv.create_text(x + self.px(30), cy, anchor="w",
                           fill=C(TEXT if won else TEXT_MUTED), font=font,
                           text=_fit(font, club, w - self.px(38) - cells_w))
            cx = x + w - self.px(8)
            for cell in reversed(cells):
                cw = max(cell_w, name_f.measure(cell) + self.px(6))
                cv.create_text(cx - cw / 2, cy, text=cell, font=num_f if won else name_f,
                               fill=C(TEXT if won else TEXT_MUTED))
                cx -= cw
            if won:
                cv.create_rectangle(x, cy - row_h / 2 + self.px(6), x + self.px(3),
                                    cy + row_h / 2 - self.px(6),
                                    fill=C(GOLD) if final else self.app.accent, width=0)
        cv.create_line(x + self.px(8), y + row_h, x + w - self.px(8), y + row_h,
                       fill=C(SURFACE_2))
        self.boxes.append((x, y, x + w, y + h, tie))

    def focus_final(self):
        """Scrolls so that the final is in the middle of the view."""
        final = self.result.rounds["final"][0]
        for x0, y0, x1, y1, tie in self.boxes:
            if tie is final:
                region = self.canvas.cget("scrollregion").split()
                if len(region) != 4:
                    return
                height = float(region[3])
                view = self.canvas.winfo_height()
                if height > view:
                    self.canvas.yview_moveto(max(0.0, ((y0 + y1) / 2 - view / 2) / height))
                return

    def _tie_at(self, x, y):
        for x0, y0, x1, y1, tie in self.boxes:
            if x0 <= x <= x1 and y0 <= y <= y1:
                return (x0, y0, x1, y1, tie)
        return None

    def on_hover(self, pos):
        if self._hover_item is None:
            return
        hit = self._tie_at(*pos) if pos else None
        if hit is None:
            self.canvas.itemconfigure(self._hover_item, state="hidden")
            self.canvas.configure(cursor="")
            return
        x0, y0, x1, y1, _ = hit
        self.canvas.coords(self._hover_item, x0, y0, x1, y1)
        self.canvas.itemconfigure(self._hover_item, state="normal")
        self.canvas.tag_raise(self._hover_item)
        self.canvas.configure(cursor="hand2")

    def on_click(self, x, y):
        hit = self._tie_at(x, y)
        if hit is None:
            return
        self.selected = hit[4]
        self.redraw()
        self.on_select(hit[4])


# =====================================================================
#  THE PENALTY SHOOTOUT SHEET
# =====================================================================

def draw_shootout(canvas, x, y, so, first_label, second_label, font, scale,
                  max_width=None):
    """Two rows of dots: green = scored, red = missed, hollow = not taken.

    A ten-round sudden death must not overflow: beyond `max_width`, the
    dots shrink (down to 6 px).
    """
    size, gap = int(14 * scale), int(5 * scale)
    label_w = max(font.measure(first_label), font.measure(second_label)) + int(12 * scale)
    rounds = max(len(so.kicks_first), len(so.kicks_second))
    if max_width and rounds:
        room = (max_width - label_w) / rounds
        if room < size + gap:
            size = max(int(6 * scale), int(room * 0.75))
            gap = max(1, int(room - size))
    for row, (label, kicks) in enumerate(((first_label, so.kicks_first),
                                          (second_label, so.kicks_second))):
        cy = y + row * (size + gap) + size / 2
        canvas.create_text(x, cy, text=label, anchor="w", fill=C(TEXT_MUTED), font=font)
        cx = x + label_w
        for i in range(rounds):
            if i < len(kicks):
                canvas.create_oval(cx, cy - size / 2, cx + size, cy + size / 2,
                                   fill=C(WIN if kicks[i] else LOSS), width=0)
            else:
                canvas.create_oval(cx + 1, cy - size / 2 + 1, cx + size - 1,
                                   cy + size / 2 - 1, outline=C(TEXT_FAINT), width=1)
            cx += size + gap
    return label_w, 2 * size + gap

