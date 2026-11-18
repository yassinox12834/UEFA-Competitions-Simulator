"""
splash.py - the very first thing on screen.

Importing the interface (CustomTkinter, Pillow, the model) takes a moment
before any window exists. This splash is plain tkinter, so it can appear
BEFORE those imports, show a progress bar while they run, and be destroyed
before the real window is created.

It must be closed before App() is built: two Tk roots alive at once would
make Tk's "default root" ambiguous for images and variables.
"""

import tkinter

# Hard-coded dark palette: the theme module is not imported yet.
BG, TEXT, MUTED, TRACK, ACCENT = "#05141A", "#F2F9FB", "#8FB3BE", "#0E2830", "#0099B5"
UZ_BLUE, UZ_WHITE, UZ_GREEN = "#0099B5", "#FFFFFF", "#1EB53A"
WIDTH, HEIGHT, BAR_W, BAR_H = 420, 220, 260, 6


class Splash:

    def __init__(self, title="UEFA Predictor"):
        self.root = tkinter.Tk()
        self.root.overrideredirect(True)          # no title bar
        self.root.configure(bg=BG)
        self.root.attributes("-topmost", True)
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"{WIDTH}x{HEIGHT}+{(sw - WIDTH) // 2}+{(sh - HEIGHT) // 2}")

        self.canvas = tkinter.Canvas(self.root, width=WIDTH, height=HEIGHT,
                                     bg=BG, highlightthickness=0, bd=0)
        self.canvas.pack()
        self._draw_flag()
        self.canvas.create_text(WIDTH // 2, 80, text=title, fill=TEXT,
                                font=("Segoe UI", 22, "bold"))
        self._status = self.canvas.create_text(WIDTH // 2, 122, text="Starting…",
                                               fill=MUTED, font=("Segoe UI", 10))
        x0, y0 = (WIDTH - BAR_W) // 2, 150
        self.canvas.create_rectangle(x0, y0, x0 + BAR_W, y0 + BAR_H,
                                     fill=TRACK, outline="")
        self._fill = self.canvas.create_rectangle(x0, y0, x0, y0 + BAR_H,
                                                  fill=ACCENT, outline="")
        self._x0, self._y0 = x0, y0
        self.root.update()

    def _draw_flag(self):
        """The Uzbek flag as a header strip, with crescent and twelve stars,
        and its green band as a footer. Plain tkinter canvas shapes."""
        c, W = self.canvas, WIDTH
        c.create_rectangle(0, 0, W, 34, fill=UZ_BLUE, outline="")
        c.create_rectangle(0, 34, W, 42, fill=UZ_WHITE, outline="")
        c.create_rectangle(0, HEIGHT - 10, W, HEIGHT, fill=UZ_GREEN, outline="")
        # crescent
        c.create_oval(14, 5, 38, 29, fill=UZ_WHITE, outline="")
        c.create_oval(20, 6, 42, 28, fill=UZ_BLUE, outline="")
        # twelve stars, rows of 3, 4, 5
        import math
        for row, count in enumerate((3, 4, 5)):
            y = 8 + 9 * row
            for k in range(count):
                x = 92 - 10 * k
                pts = []
                for i in range(10):
                    r = 3.2 if i % 2 == 0 else 1.4
                    a = math.pi / 5 * i - math.pi / 2
                    pts += [x + r * math.cos(a), y + r * math.sin(a)]
                c.create_polygon(pts, fill=UZ_WHITE, outline="")

    def step(self, fraction, text=None):
        x1 = self._x0 + int(BAR_W * max(0.0, min(1.0, fraction)))
        self.canvas.coords(self._fill, self._x0, self._y0, x1, self._y0 + BAR_H)
        if text is not None:
            self.canvas.itemconfigure(self._status, text=text)
        self.root.update()

    def close(self):
        try:
            self.root.destroy()
        except tkinter.TclError:
            pass
