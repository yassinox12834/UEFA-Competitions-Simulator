"""Resolve a club name written one way into the same club written another way.

The pots (draw_ucl.py, draw_uecl.py, the JSON templates) spell clubs the
way the badges are named: "Bayern Munich", "Inter Milan", "Brest". The
Elo file (data/processed/eeelo_final.json) spells them the way the
API-Football fixtures do: "Bayern München", "Inter", "Stade Brestois 29".
A name-string join between the two silently loses clubs, which is the
failure mode the roadmap already recorded for Bodo/Glimt.

This module is the single place where the two spellings meet. Three
layers, tried in order:

    1. ALIASES     hand-written, exact, wins over everything
    2. normalised  same letters once accents, case, punctuation and
                   filler words ("FC", "SC", "CF") are stripped
    3. fuzzy       difflib similarity on the normalised strings, only
                   above FUZZY_MIN, and only if the best match is clearly
                   ahead of the second best

Every resolution is reported, not hidden: resolve_all() returns the
table of what was matched to what and how, so the expert log can show it
and a bad match can be caught by eye instead of by a wrong table.
"""

import difflib
import re
import unicodedata

# pot spelling -> Elo spelling. Add a line here when the fuzzy layer
# picks the wrong club; it is checked first and never second-guessed.
ALIASES = {
    "Bayern Munich": "Bayern München",
    "Paris Saint-Germain": "Paris Saint Germain",
    "Inter Milan": "Inter",
    "Atlético Madrid": "Atletico Madrid",
    "Club Brugge": "Club Brugge KV",
    "Red Star Belgrade": "FK Crvena Zvezda",
    "Young Boys": "BSC Young Boys",
    "Sparta Prague": "Sparta Praha",
    "Brest": "Stade Brestois 29",
    "Gentoise": "Gent",
    "Başakşehir Istanbul": "Başakşehir",
    "Bodo/Glimt": "Bodo/Glimt",
}

# Words that carry no identity: "FC Porto" and "Porto" are one club.
_FILLER = {"fc", "cf", "sc", "ac", "as", "fk", "sk", "bk", "if", "kv",
           "club", "de", "the", "1", "1899", "cp", "afc"}

FUZZY_MIN = 0.80      # below this, no match is better than a wrong one
FUZZY_GAP = 0.05      # best must beat second best by at least this


def normalise(name):
    """'Atlético Madrid' -> 'atletico madrid', 'FC Porto' -> 'porto'."""
    text = unicodedata.normalize("NFKD", str(name))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9 ]+", " ", text.lower())
    words = [w for w in text.split() if w not in _FILLER]
    return " ".join(words) or text.strip()


class Resolution:
    """One club's match: how it was found, and against which key."""

    __slots__ = ("club", "key", "how", "score")

    def __init__(self, club, key, how, score=1.0):
        self.club = club        # name as written in the pots
        self.key = key          # name as written in the Elo file, or None
        self.how = how          # "exact" | "alias" | "normalised" | "fuzzy" | "missing"
        self.score = score      # 1.0 except for fuzzy matches

    def __repr__(self):
        return f"Resolution({self.club!r} -> {self.key!r}, {self.how}, {self.score:.2f})"


def resolve(club, keys, _norm_index=None):
    """Find `club` among `keys`. Returns a Resolution; key is None if not found."""
    if club in keys:
        return Resolution(club, club, "exact")
    alias = ALIASES.get(club)
    if alias is not None and alias in keys:
        return Resolution(club, alias, "alias")

    index = _norm_index if _norm_index is not None else build_index(keys)
    wanted = normalise(club)
    hit = index.get(wanted)
    if hit is not None:
        return Resolution(club, hit, "normalised")

    # difflib.get_close_matches would hide the runner-up; we need it to
    # apply the gap rule, so the ratios are computed by hand.
    scored = sorted(((difflib.SequenceMatcher(None, wanted, norm).ratio(), key)
                     for norm, key in index.items()), reverse=True)
    if scored and scored[0][0] >= FUZZY_MIN:
        best_score, best_key = scored[0]
        second = scored[1][0] if len(scored) > 1 else 0.0
        if best_score - second >= FUZZY_GAP:
            return Resolution(club, best_key, "fuzzy", best_score)
    return Resolution(club, None, "missing", 0.0)


def build_index(keys):
    """{normalised key: key}. Built once per lookup table, not per club."""
    index = {}
    for key in keys:
        index.setdefault(normalise(key), key)
    return index


def resolve_all(clubs, keys):
    """[Resolution, ...] in the order of `clubs`. One index for the whole batch."""
    index = build_index(keys)
    return [resolve(club, keys, index) for club in clubs]
