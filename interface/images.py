"""
images.py - everything that makes an image for the app.

No other file may open a PNG or draw with Pillow: everything goes through
here. Two reasons:

  1. The cache. One CTkImage per key, so the same logo is decoded only
     once, even if it appears on three screens.
  2. The safety net. A missing file returns a grey dot (_placeholder)
     instead of crashing the app.

Sharp rendering: we draw at SCALE times the requested size, then CTkImage
shrinks it. On a HiDPI screen the result stays clean.
"""

from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageColor, ImageDraw, ImageFont, ImageOps

from config import (BALL_BODY, BALL_EDGE, BALL_TEXT, CLUB_LOGOS_DIR,
                    COMP_FILES, FLAG_FILES, LOGO_SUFFIX)

SCALE = 2
_IMG_CACHE = {}


# ---------------------------------------------------------------------
#  LOW-LEVEL TOOLS
# ---------------------------------------------------------------------

def _rounded_mask(size, radius):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, size[0] - 1, size[1] - 1), radius, fill=255)
    return mask


def _rgba(color, alpha=255):
    return ImageColor.getrgb(color) + (alpha,)


_PIL_FONTS = {}
_BOLD_FILES = ("segoeuib.ttf", "seguisb.ttf", "arialbd.ttf", "Inter-Bold.ttf",
               "Roboto-Bold.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf")


def _bold_font(px):
    """A bold TrueType font at `px` pixels, or Pillow's default font.

    Pillow looks for the name in the system font folders
    (C:\\Windows\\Fonts on Windows). Roboto ships with CustomTkinter, so
    we also look in its folder, which guarantees clean rendering even on a
    machine with neither Segoe UI nor Arial.
    """
    px = max(6, int(px))
    font = _PIL_FONTS.get(px)
    if font is not None:
        return font
    candidates = list(_BOLD_FILES)
    try:
        ctk_fonts = Path(ctk.__file__).parent / "assets" / "fonts" / "Roboto"
        candidates.insert(0, str(ctk_fonts / "Roboto-Medium.ttf"))
    except Exception:
        pass
    for name in candidates:
        try:
            font = ImageFont.truetype(name, px)
            break
        except OSError:
            continue
    else:
        try:
            font = ImageFont.load_default(size=px)
        except TypeError:                  # older Pillow: fixed size
            font = ImageFont.load_default()
    _PIL_FONTS[px] = font
    return font


def _placeholder(size, label, color):
    """Safety net: a missing file must not kill the app."""
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, size[0] - 1, size[1] - 1),
                        size[1] // 5, fill=_rgba(color))
    try:
        font = ImageFont.load_default(size=size[1] // 3)
    except TypeError:                      # older Pillow: fixed size
        font = ImageFont.load_default()
    d.text((size[0] / 2, size[1] / 2), label, anchor="mm",
           fill=(255, 255, 255, 255), font=font)
    return img


# ---------------------------------------------------------------------
#  PILLOW FACTORIES
# ---------------------------------------------------------------------

def _flag_pil(path, size, radius, label):
    if not path.exists():
        return _placeholder(size, label, "#5B6270")
    flag = ImageOps.fit(Image.open(path).convert("RGBA"), size,
                        method=Image.LANCZOS)
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    out.paste(flag, (0, 0), _rounded_mask(size, radius))
    return out


def _logo_pil(path, size, radius, pad, plate, label):
    if not path.exists():
        return _placeholder(size, label, "#5B6270")
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    out.paste(Image.new("RGBA", size, _rgba(plate)),
              (0, 0), _rounded_mask(size, radius))
    logo = Image.open(path).convert("RGBA")
    logo.thumbnail((size[0] - 2 * pad, size[1] - 2 * pad), Image.LANCZOS)
    out.alpha_composite(logo, ((size[0] - logo.width) // 2,
                               (size[1] - logo.height) // 2))
    return out


def _bracket_pil(size, accent):
    """'Draw' icon: a mini bracket of fixtures."""
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    u = size[0] / 88.0                     # drawn on an 88-unit grid
    c, w = _rgba(accent), max(2, int(3 * u))
    d.rounded_rectangle((0, 0, size[0] - 1, size[1] - 1),
                        22 * u, fill=_rgba(accent, 30))
    d.rounded_rectangle((18 * u, 24 * u, 40 * u, 32 * u), 4 * u, fill=c)
    d.rounded_rectangle((18 * u, 52 * u, 40 * u, 60 * u), 4 * u, fill=c)
    d.line((40 * u, 28 * u, 46 * u, 28 * u), fill=c, width=w)
    d.line((40 * u, 56 * u, 46 * u, 56 * u), fill=c, width=w)
    d.line((46 * u, 28 * u, 46 * u, 56 * u), fill=c, width=w)
    d.line((46 * u, 42 * u, 52 * u, 42 * u), fill=c, width=w)
    d.rounded_rectangle((52 * u, 38 * u, 72 * u, 46 * u), 4 * u, fill=c)
    return img


def _curve_pil(size, accent):
    """'Simulation' icon: a prediction curve."""
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    u = size[0] / 88.0
    c, w = _rgba(accent), max(2, int(4 * u))
    d.rounded_rectangle((0, 0, size[0] - 1, size[1] - 1),
                        22 * u, fill=_rgba(accent, 30))
    d.line((18 * u, 66 * u, 72 * u, 66 * u), fill=_rgba(accent, 110),
           width=max(2, int(2 * u)))
    points = [(22 * u, 58 * u), (36 * u, 46 * u),
              (50 * u, 52 * u), (66 * u, 24 * u)]
    d.line(points, fill=c, width=w, joint="curve")
    r = 4 * u
    for x, y in points:
        d.ellipse((x - r, y - r, x + r, y + r), fill=c)
    return img


# ---------------------------------------------------------------------
#  PUBLIC API: what the views call
# ---------------------------------------------------------------------

def _cached(key, builder, box):
    """One CTkImage per key: the same PNG is never loaded twice."""
    img = _IMG_CACHE.get(key)
    if img is None:
        pil = builder((box[0] * SCALE, box[1] * SCALE))
        img = ctk.CTkImage(light_image=pil, dark_image=pil, size=box)
        _IMG_CACHE[key] = img
    return img


def flag_image(lang, box=(104, 68)):
    return _cached(
        ("flag", lang, box),
        lambda s: _flag_pil(FLAG_FILES[lang], s, int(14 * SCALE), lang.upper()),
        box)


def comp_image(comp, box=(96, 96), plate="#FFFFFF"):
    # Radius and margin as a percentage: the same dot stays right at
    # 96 px on a card and at 32 px in the top bar.
    return _cached(
        ("comp", comp, box, plate),
        lambda s: _logo_pil(COMP_FILES[comp], s, int(s[0] * 0.20),
                            int(s[0] * 0.11), plate, comp),
        box)


def mode_image(mode, accent, box=(88, 88)):
    builder = _bracket_pil if mode == "draw" else _curve_pil
    return _cached(("mode", mode, accent, box),
                   lambda s: builder(s, accent), box)


def window_icon(comp, size=64):
    """
    Window icon = the competition's logo, as a Tk PhotoImage.

    Returns None if the file is missing or Tk does not like it: App then
    keeps the default icon, which has never stopped an app from running.
    The caller MUST keep a reference to the returned object, otherwise the
    garbage collector erases the icon.
    """
    try:
        from PIL import ImageTk
        path = COMP_FILES[comp]
        if not path.exists():
            return None
        pil = Image.open(path).convert("RGBA").resize(
            (size, size), Image.LANCZOS)
        return ImageTk.PhotoImage(pil)
    except Exception:
        return None


# ---------------------------------------------------------------------
#  CLUB BADGES
# ---------------------------------------------------------------------
# Rule of the file: the club's name IS the file name, plus the suffix.
# Nothing is cleaned up here: if a club is called "Bodo/Glimt", pathlib
# reads clubs/UEL/Bodo/Glimt_logo.png, which really does exist in that
# form (a "Bodo" folder). This works by accident, not by design: the day
# fetch_club_logos.py sanitises the names, it will have to be done here
# too.

def _initials(name, limit=3):
    """A club's initials when the badge is missing: 'Red Star Belgrade' -> 'RSB'."""
    words = [w for w in name.replace('.', ' ').replace('/', ' ').split() if w]
    if not words:
        return "?"
    if len(words) == 1:
        return words[0][:2].upper()
    return ''.join(w[0] for w in words[:limit]).upper()


# (background, stripe) pairs for the replacement badges. Chosen to stay
# readable under white initials, in both light and dark mode.
CREST_PALETTE = (
    ("#1D4ED8", "#60A5FA"), ("#B91C1C", "#F87171"), ("#047857", "#34D399"),
    ("#7C3AED", "#C4B5FD"), ("#B45309", "#FBBF24"), ("#0F766E", "#5EEAD4"),
    ("#BE185D", "#F9A8D4"), ("#334155", "#94A3B8"), ("#1E3A8A", "#FACC15"),
    ("#991B1B", "#FDE68A"), ("#065F46", "#F1F5F9"), ("#6D28D9", "#FDE047"),
)


def crest_colours(name):
    """Two stable colours for a club: the same name always gives the same ones.

    hashlib and not hash(): Python's hash() changes on every launch
    (PYTHONHASHSEED), so Liverpool's badge would change colour.
    """
    import hashlib
    digest = hashlib.md5(name.encode("utf-8")).digest()
    return CREST_PALETTE[digest[0] % len(CREST_PALETTE)], digest[1] % 3


def _shield_points(w, h, pad):
    """Outline of a shield: straight shoulders, sides, rounded point."""
    import math
    left, right, top = pad, w - pad, pad
    mid = w / 2
    shoulder = h * 0.42
    bottom = h - pad
    pts = [(left, top + h * 0.06), (mid, top), (right, top + h * 0.06),
           (right, shoulder)]
    # Right side, then left: two quarter-ellipses down to the point.
    steps = 14
    for i in range(1, steps + 1):
        a = (math.pi / 2) * i / steps
        pts.append((mid + (right - mid) * math.cos(a),
                    shoulder + (bottom - shoulder) * math.sin(a)))
    for i in range(steps - 1, -1, -1):
        a = (math.pi / 2) * i / steps
        pts.append((mid - (mid - left) * math.cos(a),
                    shoulder + (bottom - shoulder) * math.sin(a)))
    return pts


def _club_placeholder_pil(size, name, accent=None):
    """A replacement shield: colours specific to the club, with initials.

    `accent` is no longer used for the colour (all the clubs in a
    competition were blue, so they could not be told apart); it stays in
    the signature so as not to break existing calls.
    """
    w, h = size
    (base, band), pattern = crest_colours(name)
    pts = _shield_points(w, h, max(1, w * 0.04))

    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)

    art = Image.new("RGBA", size, _rgba(base))
    # The patterns are translucent: we draw them on a separate layer, then
    # alpha_composite BLENDS them into the background. Drawing directly on
    # `art` would REPLACE the pixels with semi-transparent ones.
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    if pattern == 0:                               # diagonal band
        d.polygon([(w * 0.55, 0), (w, 0), (w, h * 0.45), (0, h), (0, h * 0.55)],
                  fill=_rgba(band, 150))
    elif pattern == 1:                             # chief (band across the top)
        d.rectangle((0, 0, w, h * 0.30), fill=_rgba(band, 170))
    else:                                          # pale (vertical band)
        d.rectangle((w * 0.40, 0, w * 0.60, h), fill=_rgba(band, 120))
    # Highlight at the top left: gives volume without a real gradient.
    d.ellipse((-w * 0.3, -h * 0.5, w * 0.7, h * 0.35), fill=(255, 255, 255, 34))
    art.alpha_composite(layer)

    out = Image.new("RGBA", size, (0, 0, 0, 0))
    out.paste(art, (0, 0), mask)
    ImageDraw.Draw(out).polygon(pts, outline=(255, 255, 255, 90),
                                width=max(1, w // 28))

    text = _initials(name, limit=3 if w >= 40 else 2)
    font = _bold_font(h * (0.34 if len(text) <= 2 else 0.27))
    cx, cy = w / 2, h * 0.47
    shadow = max(1, w // 40)
    od = ImageDraw.Draw(out)
    od.text((cx, cy + shadow), text, anchor="mm", fill=(0, 0, 0, 90), font=font)
    od.text((cx, cy), text, anchor="mm", fill=(255, 255, 255, 255), font=font)
    return out


def _club_logo_pil(path, size, name, accent, plate):
    """The badge placed on a round dot, or the initials if it is missing."""
    if path is None or not path.exists() or not path.is_file():
        return _club_placeholder_pil(size, name, accent)
    try:
        logo = Image.open(path).convert("RGBA")
    except Exception:
        # Corrupt file, unknown format, truncated image: same safety net
        # as for a missing file. A badge is not worth bringing the window
        # down.
        return _club_placeholder_pil(size, name, accent)

    out = Image.new("RGBA", size, (0, 0, 0, 0))
    if plate is not None:
        d = ImageDraw.Draw(out)
        d.ellipse((0, 0, size[0] - 1, size[1] - 1), fill=_rgba(plate))
    pad = max(1, int(size[0] * 0.10))
    logo.thumbnail((size[0] - 2 * pad, size[1] - 2 * pad), Image.LANCZOS)
    out.alpha_composite(logo, ((size[0] - logo.width) // 2,
                               (size[1] - logo.height) // 2))
    return out



_LOGO_INDEX = {}


def _logo_key(name):
    """Neutral form for comparing a club name with a file name."""
    flat = "".join(" " if c in '/\\_-.:*?"<>|' else c for c in name.lower())
    return " ".join(flat.split())          # multiple spaces reduced to one


def _comp_index(comp):
    """{neutral form: path} for a competition. Read only once.

    A consequence worth knowing: a badge dropped into the folder while the
    app is running will not be seen before the next launch.
    """
    index = _LOGO_INDEX.get(comp)
    if index is not None:
        return index
    index = {}
    folder = CLUB_LOGOS_DIR / comp
    try:
        entries = list(folder.iterdir())
    except OSError:
        entries = []                       # folder missing: initials only
    for entry in entries:
        if not entry.is_file() or not entry.name.endswith(LOGO_SUFFIX):
            continue
        stem = entry.name[:-len(LOGO_SUFFIX)]
        index.setdefault(_logo_key(stem), entry)
    _LOGO_INDEX[comp] = index
    return index


def club_logo_path(comp, club):
    """assets/images/clubs/UCL/Real Madrid_logo.png, or None if it is missing."""
    return _comp_index(comp).get(_logo_key(club))


def club_image(comp, club, box=(28, 28), accent="#5B6270", custom_path=None,
               plate="#FFFFFF"):
    """
    A club's badge, as a CTkImage, cached by key.

    custom_path is for club replacement: the user supplies their own file,
    which is not in assets/. It goes into the cache key so that two
    replaced clubs do not step on each other.
    """
    path = Path(custom_path) if custom_path else club_logo_path(comp, club)
    key = ("club", comp, club, str(path), box, accent, plate)
    return _cached(
        key,
        lambda s: _club_logo_pil(path, s, club, accent, plate),
        box)


# ---------------------------------------------------------------------
#  CEREMONY: THE BALL
# ---------------------------------------------------------------------

def _ball_pil(size, accent, label=None):
    """The draw ball: a light sphere, a band in the competition's colour,
    and a spot of light at the top left to give it volume without needing
    a real gradient."""
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    w = size[0]
    edge = max(2, int(w * 0.045))

    d.ellipse((0, 0, w - 1, size[1] - 1), fill=_rgba(BALL_BODY),
              outline=_rgba(accent), width=edge)
    # Highlight: a translucent white oval, shifted to the top left.
    d.ellipse((w * 0.20, size[1] * 0.14, w * 0.52, size[1] * 0.36),
              fill=(255, 255, 255, 190))
    # The seam line of the ball, like on real ones.
    d.arc((w * 0.06, size[1] * 0.06, w * 0.94, size[1] * 0.94),
          start=200, end=340, fill=_rgba(BALL_EDGE), width=max(1, int(w * 0.02)))

    if label:
        try:
            font = ImageFont.load_default(size=int(size[1] * 0.30))
        except TypeError:
            font = ImageFont.load_default()
        d.text((w / 2, size[1] * 0.60), label, anchor="mm",
               fill=_rgba(BALL_TEXT), font=font)
    return img


def ball_image(accent, box=(96, 96), label=None):
    return _cached(("ball", accent, box, label),
                   lambda s: _ball_pil(s, accent, label), box)


# ---------------------------------------------------------------------
#  ICONS FOR THE "INSTANT / CEREMONY" CHOICE
# ---------------------------------------------------------------------

def _bolt_pil(size, accent):
    """'All at once' icon: a lightning bolt."""
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    u = size[0] / 88.0
    d.rounded_rectangle((0, 0, size[0] - 1, size[1] - 1),
                        22 * u, fill=_rgba(accent, 30))
    d.polygon([(50 * u, 16 * u), (30 * u, 48 * u), (43 * u, 48 * u),
               (38 * u, 72 * u), (60 * u, 39 * u), (46 * u, 39 * u)],
              fill=_rgba(accent))
    return img


def _ceremony_pil(size, accent):
    """'Ceremony' icon: a ball coming out of a bowl."""
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    u = size[0] / 88.0
    d.rounded_rectangle((0, 0, size[0] - 1, size[1] - 1),
                        22 * u, fill=_rgba(accent, 30))
    # The bowl: the LOWER half of a disc. In Pillow the y axis points
    # down, so start=0 end=180 does draw the underside, not the top.
    d.pieslice((22 * u, 34 * u, 66 * u, 74 * u), start=0, end=180,
               fill=_rgba(accent, 110))
    d.line((20 * u, 54 * u, 68 * u, 54 * u), fill=_rgba(accent),
           width=max(2, int(3 * u)))
    # The ball, already out, placed above the rim so that it can be seen
    # escaping from it rather than floating inside.
    d.ellipse((34 * u, 12 * u, 58 * u, 36 * u), fill=_rgba(BALL_BODY),
              outline=_rgba(accent), width=max(2, int(3 * u)))
    return img


def _tile(size, accent):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), size[0] * 0.25,
                        fill=_rgba(accent, 32))
    return img, d, size[0] / 88.0


def _legs_pil(size, accent):
    """'legs' method: two legs, two tokens, 1 and 1/2."""
    img, d, u = _tile(size, accent)
    c = _rgba(accent)
    for i, (x, h) in enumerate(((24, 34), (48, 22))):
        d.rounded_rectangle((x * u, (64 - h) * u, (x + 16) * u, 64 * u), 4 * u,
                            fill=c if i == 0 else _rgba(accent, 140))
    d.line((18 * u, 68 * u, 70 * u, 68 * u), fill=_rgba(accent, 120),
           width=max(1, int(2 * u)))
    return img


def _aggregate_pil(size, accent):
    """'aggregate' method: 2 + 1 = 3."""
    img, d, u = _tile(size, accent)
    c = _rgba(accent)
    d.rounded_rectangle((16 * u, 28 * u, 38 * u, 50 * u), 6 * u, fill=_rgba(accent, 140))
    d.rounded_rectangle((50 * u, 28 * u, 72 * u, 50 * u), 6 * u, fill=_rgba(accent, 140))
    w = max(2, int(3 * u))
    d.line((40 * u, 39 * u, 48 * u, 39 * u), fill=c, width=w)
    d.line((44 * u, 35 * u, 44 * u, 43 * u), fill=c, width=w)
    d.rounded_rectangle((28 * u, 58 * u, 60 * u, 66 * u), 4 * u, fill=c)
    return img


def _oneshot_pil(size, accent):
    """'oneshot' method: one die, a single draw."""
    img, d, u = _tile(size, accent)
    c = _rgba(accent)
    d.rounded_rectangle((24 * u, 24 * u, 64 * u, 64 * u), 10 * u, fill=c)
    r = 4 * u
    for x, y in ((34, 34), (44, 44), (54, 54)):
        d.ellipse(((x * u) - r, (y * u) - r, (x * u) + r, (y * u) + r),
                  fill=(255, 255, 255, 235))
    return img


def _brand_pil(size, accent):
    """The app's mark: a rounded square in the accent colour, an 8-pointed star."""
    import math
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    w = size[0]
    d.rounded_rectangle((0, 0, w - 1, size[1] - 1), w * 0.28, fill=_rgba(accent))
    cx, cy, ro, ri = w / 2, size[1] / 2, w * 0.30, w * 0.13
    pts = []
    for i in range(16):
        r = ro if i % 2 == 0 else ri
        a = math.pi / 8 * i - math.pi / 2
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=(255, 255, 255, 255))
    return img


def _trophy_pil(size, colour):
    """A big-eared cup, for the winner's header."""
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    u = size[0] / 88.0
    c = _rgba(colour)
    w = max(2, int(6 * u))
    d.pieslice((22 * u, -6 * u, 66 * u, 52 * u), 0, 180, fill=c)
    d.arc((8 * u, 12 * u, 32 * u, 40 * u), 90, 270, fill=c, width=w)
    d.arc((56 * u, 12 * u, 80 * u, 40 * u), 270, 90, fill=c, width=w)
    d.rectangle((40 * u, 50 * u, 48 * u, 66 * u), fill=c)
    d.rounded_rectangle((28 * u, 66 * u, 60 * u, 76 * u), 3 * u, fill=c)
    return img


_PICTOS = {"legs": _legs_pil, "aggregate": _aggregate_pil,
           "oneshot": _oneshot_pil}


def method_image(method, accent, box=(56, 56)):
    return _cached(("method", method, accent, box),
                   lambda s: _PICTOS[method](s, accent), box)


def brand_image(accent, box=(30, 30)):
    return _cached(("brand", accent, box), lambda s: _brand_pil(s, accent), box)


def trophy_image(colour, box=(40, 40)):
    return _cached(("trophy", colour, box), lambda s: _trophy_pil(s, colour), box)


def run_image(kind, accent, box=(88, 88)):
    """kind = 'instant' | 'live'."""
    builder = _bolt_pil if kind == "instant" else _ceremony_pil
    return _cached(("run", kind, accent, box),
                   lambda s: builder(s, accent), box)


# ---------------------------------------------------------------------
#  BADGES FOR ORDINARY TK WIDGETS
# ---------------------------------------------------------------------
# A CTkImage can only be placed on a CustomTkinter widget. But the dense
# lists (a matchday's fixtures, the by-club standings) are drawn in plain
# Tk, because a CustomTkinter widget costs 60 to 120 times more to build.
# They therefore need real PhotoImages.
#
# What we lose: CTkImage resizes by itself when the screen is HiDPI,
# PhotoImage does not. At 20 px, in a list, it cannot be seen; elsewhere,
# keep using club_image().

_PHOTO_CACHE = {}


def club_photo(comp, club, size=22, accent="#5B6270", custom_path=None,
               plate="#FFFFFF"):
    """The badge as a Tk PhotoImage. None if Tk does not want it.

    WARNING: Tk does not keep a reference to a PhotoImage. The cache below
    plays that role; without it, Python's garbage collector would erase
    the image and the label would go blank.
    """
    key = ("photo", comp, club, str(custom_path), size, accent, plate)
    photo = _PHOTO_CACHE.get(key)
    if photo is not None:
        return photo
    try:
        from PIL import ImageTk
        path = Path(custom_path) if custom_path else club_logo_path(comp, club)
        pil = _club_logo_pil(path, (size * SCALE, size * SCALE), club, accent,
                             plate).resize((size, size), Image.LANCZOS)
        photo = ImageTk.PhotoImage(pil)
    except Exception:
        return None
    _PHOTO_CACHE[key] = photo
    return photo
