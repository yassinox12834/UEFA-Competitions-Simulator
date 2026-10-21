"""
theme.py - the default look of every CustomTkinter widget.

CustomTkinter reads its default colours from a global dictionary,
ThemeManager.theme, filled by set_default_color_theme(). A widget created
without fg_color= takes the value from that dictionary. Instead of
repeating fg_color=..., border_color=... on every button, field and
scrollbar, we fix the dictionary ONCE, before the window creates a single
widget.

Why start from "dark-blue" and modify it, rather than write a complete
JSON file: the theme contains about thirty sections and CustomTkinter adds
some from one version to the next. We only touch what the app uses; the
rest keeps its original value, so a new version of the library breaks
nothing.

apply_theme(accent) is called by App.__init__; the starting accent is that
of the default competition. Screens that change accent along the way (UEL
orange, UECL green) always pass their colour explicitly.
"""

import customtkinter as ctk

from config import (BORDER, CARD, CARD_HOVER, SURFACE, SURFACE_2, TEXT,
                    TEXT_FAINT)


def _pair(colour):
    return list(colour) if isinstance(colour, tuple) else colour


def apply_theme(accent, accent_hover, base="dark-blue"):
    ctk.set_default_color_theme(base)
    t = ctk.ThemeManager.theme
    accent2 = [accent, accent]
    hover2 = [accent_hover, accent_hover]

    t["CTkButton"].update(corner_radius=10, fg_color=accent2, hover_color=hover2,
                          border_color=_pair(BORDER),
                          text_color=["#FFFFFF", "#FFFFFF"],
                          text_color_disabled=_pair(TEXT_FAINT))

    # Tabs and multiple choice: a discreet track, the accent on the chosen
    # item, and the unchosen text in a readable grey.
    t["CTkSegmentedButton"].update(
        corner_radius=10, border_width=3,
        fg_color=_pair(SURFACE_2), unselected_color=_pair(SURFACE_2),
        unselected_hover_color=_pair(CARD_HOVER),
        selected_color=accent2, selected_hover_color=hover2,
        text_color=_pair(TEXT), text_color_disabled=_pair(TEXT_FAINT))

    t["CTkEntry"].update(corner_radius=10, border_width=1,
                         fg_color=_pair(CARD), border_color=_pair(BORDER),
                         text_color=_pair(TEXT),
                         placeholder_text_color=_pair(TEXT_FAINT))

    t["CTkScrollbar"].update(
        button_color=["#C9CFDA", "#2A303C"],
        button_hover_color=["#AEB6C4", "#3A4252"])
    t["CTkScrollableFrame"]["label_fg_color"] = _pair(SURFACE_2)

    t["CTkSwitch"].update(fg_color=_pair(BORDER), progress_color=accent2,
                          # Dark knob in light mode: a white circle on a
                          # white card would disappear.
                          button_color=["#3B4250", "#F2F4F8"],
                          button_hover_color=["#2A303C", "#FFFFFF"],
                          text_color=_pair(TEXT))

    t["CTkProgressBar"].update(fg_color=_pair(SURFACE_2), progress_color=accent2)

    t["CTkOptionMenu"].update(corner_radius=10, fg_color=_pair(CARD),
                              button_color=_pair(SURFACE_2),
                              button_hover_color=_pair(CARD_HOVER),
                              text_color=_pair(TEXT))
    t["CTkComboBox"].update(corner_radius=10, border_width=1,
                            fg_color=_pair(CARD), border_color=_pair(BORDER),
                            button_color=_pair(BORDER),
                            button_hover_color=_pair(TEXT_FAINT),
                            text_color=_pair(TEXT))
    t["CTkCheckBox"].update(corner_radius=6, border_width=2, fg_color=accent2,
                            hover_color=hover2, border_color=_pair(TEXT_FAINT),
                            text_color=_pair(TEXT))
    t["CTkFrame"].update(fg_color=_pair(SURFACE), top_fg_color=_pair(SURFACE_2),
                         border_color=_pair(BORDER))
    t["CTkToplevel"]["fg_color"] = _pair(SURFACE)
    t["CTkTextbox"].update(fg_color=_pair(CARD), border_color=_pair(BORDER),
                           text_color=_pair(TEXT),
                           scrollbar_button_color=t["CTkScrollbar"]["button_color"],
                           scrollbar_button_hover_color=t["CTkScrollbar"]["button_hover_color"])
    t["DropdownMenu"].update(fg_color=_pair(CARD), hover_color=_pair(CARD_HOVER),
                             text_color=_pair(TEXT))
    t["CTkLabel"]["text_color"] = _pair(TEXT)
    return t


def tint_segmented(seg, accent, accent_hover):
    """Recolours a CTkSegmentedButton that already exists (competition change)."""
    seg.configure(selected_color=accent, selected_hover_color=accent_hover)
