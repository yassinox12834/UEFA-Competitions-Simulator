"""
base_view.py - the contract shared by every screen.

A screen does not inherit from CTkFrame directly: it inherits from
BaseView, which gives it a centred body (self.body) and a list of methods
that the router (App) knows how to call. Adding a screen later therefore
means writing a class that fills in these gaps, nothing more.
"""

import customtkinter as ctk

from config import SURFACE


class BaseView(ctk.CTkFrame):
    """
    build()        -> widgets, called once
    refresh_text() -> reapplies every translated text
    on_show()      -> on every display (calls refresh_text by default)
    on_hide()      -> just before leaving the screen
    blocks()       -> the large blocks, in order of appearance
    on_back()      -> Escape key
    on_enter()     -> Enter key
    """

    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color=SURFACE, corner_radius=0, **kwargs)
        self.app = app
        # All content lives in self.body, packed with expand=True: the
        # column stays vertically centred, even when the window is enlarged.
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(expand=True)
        self.build()

    def build(self):
        pass

    def refresh_text(self):
        pass

    def on_show(self):
        self.refresh_text()

    def on_hide(self):
        pass

    def blocks(self):
        return []

    def on_back(self):
        pass

    def on_enter(self):
        pass
