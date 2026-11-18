"""
loading.py - the start-up loading screen.

Building the app (fonts, images, every registered view) takes a moment
before the first screen can appear. LoadingScreen covers the window during
that time with the title and a progress bar, then removes itself.

It is not a view: it is not registered with the router and knows nothing
about languages, so its texts are fixed.
"""

import customtkinter as ctk

from config import (BG, COMP, DEFAULT_COMP, TEXT, TEXT_MUTED, SURFACE_2,
                    WINDOW_TITLE)


class LoadingScreen(ctk.CTkFrame):

    def __init__(self, master, status="Loading…"):
        super().__init__(master, fg_color=BG, corner_radius=0)
        self.place(x=0, y=0, relwidth=1, relheight=1)
        self.lift()

        box = ctk.CTkFrame(self, fg_color="transparent")
        box.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(box, text=WINDOW_TITLE, text_color=TEXT,
                     font=ctk.CTkFont(size=28, weight="bold")).pack()
        self._status = ctk.CTkLabel(box, text=status, text_color=TEXT_MUTED,
                                    font=ctk.CTkFont(size=13))
        self._status.pack(pady=(8, 16))
        self._bar = ctk.CTkProgressBar(
            box, width=260, height=6, fg_color=SURFACE_2,
            progress_color=COMP[DEFAULT_COMP]["accent"])
        self._bar.set(0)
        self._bar.pack()
        self._paint()

    def _paint(self):
        # Force a repaint: the main loop is not running yet.
        self.update_idletasks()
        self.update()

    def step(self, fraction, text=None):
        """Moves the bar to `fraction` (0..1) and optionally changes the text."""
        self._bar.set(max(0.0, min(1.0, fraction)))
        if text is not None:
            self._status.configure(text=text)
        self._paint()

    def close(self):
        self.step(1.0)
        self.destroy()
