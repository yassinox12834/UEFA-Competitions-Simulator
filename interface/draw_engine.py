"""
draw_engine.py - the bridge between the interface and model/.

The interface must never import draw_ucl or draw_uecl directly: it goes
through here. Three reasons.

  1. The path. interface/ is launched with its own folder in sys.path
     (see main.py), so "model.draw_ucl" cannot be found until the project
     root is there too. We fix that once, here, at import time.
  2. The routing. UCL and UEL share draw_ucl.py, UECL has draw_uecl.py,
     and the matchdays come from two other, different modules. The view
     does not need to know this map: it asks to "draw UECL".
  3. The thread. A draw takes 80 to 250 ms on a typical machine, and much
     more on a slow one. Done on Tk's thread, it freezes the window.
     DrawJob does it on the side and the view checks in for news.

Contents:
    PotsModel     the pots as displayed, replacements included
    load_template reads and checks a JSON file of pots
    save_template writes the current pots to a JSON file
    DrawJob       a draw launched in the background
    replay_order  the ceremony script, in Monaco order
"""

import json
import random
import re
import sys
import threading
from pathlib import Path

# interface/draw_engine.py -> interface/ -> UEFA/
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from model import draw_ucl, draw_uecl                       # noqa: E402
from model.matchdays_ucl import generate_matchdays          # noqa: E402
from model.matchdays_uecl import verify_matchdays           # noqa: E402
from uefa.paths import USER_DIR                             # noqa: E402

# Which competition runs on which engine. UCL and UEL have exactly the
# same format (4 pots of 9, 8 opponents), so they use the same module.
ENGINES = {"UCL": draw_ucl, "UEL": draw_ucl, "UECL": draw_uecl}


def base_pots(comp):
    """The original pots, as written in model/."""
    if comp == "UECL":
        return draw_uecl.POTS
    return draw_ucl.POTS_BY_COMP[comp]


def base_countries(comp):
    """{club: country} read from countries_filled_25.csv, cached by the engine."""
    if comp == "UECL":
        return draw_uecl._countries()
    return draw_ucl._countries(comp)


# =====================================================================
#  THE DISPLAYED POTS
# =====================================================================

class PotsModel:
    """
    What the view draws, and what the engine will receive.

    A replacement touches neither model/ nor the CSV files: it lives here,
    for the length of the session. The club keeps its place and its pot;
    only its name, association and badge change. This is the only way to
    guarantee that the draw stays feasible, since the shape of the problem
    (9 per pot, 2 at most per association) does not move.
    """

    def __init__(self, comp):
        self.comp = comp
        self.pots = [list(pot) for pot in base_pots(comp)]
        self.countries = dict(base_countries(comp))
        self.custom_logos = {}     # club -> path of an image supplied by the user
        self.origins = {}          # new name -> original name
        self.constraints = set()   # {(host, guest)}: "host does not receive guest"

    # ---------- reading ----------
    def club_at(self, pot_index, slot_index):
        return self.pots[pot_index][slot_index]

    def all_clubs(self):
        return [club for pot in self.pots for club in pot]

    def country_of(self, club):
        return self.countries.get(club, "")

    def logo_for(self, club):
        """Path of the image supplied by the user, or None."""
        return self.custom_logos.get(club)

    def is_replaced(self, club):
        return club in self.origins

    def origin_of(self, club):
        return self.origins.get(club)

    def swap_count(self):
        return len(self.origins)

    def constraint_list(self):
        """The constraints, sorted. A set has no order, a list does.

        The display needs a stable order, otherwise two openings of the
        box would show the same constraints arranged differently.
        """
        return sorted(self.constraints)

    def add_constraint(self, host, guest):
        """Adds "host does not receive guest". Returns an error key or None."""
        host = (host or "").strip()
        guest = (guest or "").strip()
        clubs = set(self.all_clubs())
        if host not in clubs or guest not in clubs:
            return "err_cst_unknown"
        if host == guest:
            return "err_cst_self"
        if (host, guest) in self.constraints:
            return "err_cst_dupe"
        self.constraints.add((host, guest))
        return None

    def remove_constraint(self, host, guest):
        # discard and not remove: removing the same row twice, by double
        # click, must not raise KeyError.
        self.constraints.discard((host, guest))

    def _rename_in_constraints(self, old, new):
        """Follows a club that changes name, so that no constraint dies.

        A constraint that names a club absent from the pots never triggers
        anything and says nothing: exactly the silent state that
        ConstraintError exists to prevent. So we rename rather than leave
        it lying around.
        """
        if old == new:
            return
        self.constraints = {(new if host == old else host,
                             new if guest == old else guest)
                            for host, guest in self.constraints}

    # ---------- writing ----------
    def validate(self, pot_index, slot_index, name):
        """Returns an error key, or None if the name passes.

        The duplicate is checked against ALL clubs except the one being
        replaced: two clubs with the same name would give a single key in
        the teams dictionary, and the draw would silently lose a team.
        """
        name = name.strip()
        if not name:
            return "err_name"
        current = self.pots[pot_index][slot_index]
        for other in self.all_clubs():
            if other != current and other == name:
                return "err_dupe"
        return None

    def replace(self, pot_index, slot_index, name, country, image_path=None):
        """Swaps a club for another, in the same place."""
        name = name.strip()
        country = (country or "").strip()
        old = self.pots[pot_index][slot_index]

        # A replacement on top of a replacement keeps track of the
        # original club, otherwise "Undo" would no longer know what to put
        # back.
        origin = self.origins.pop(old, old)
        self.custom_logos.pop(old, None)

        self.pots[pot_index][slot_index] = name
        self._rename_in_constraints(old, name)
        self.countries[name] = country
        if image_path:
            self.custom_logos[name] = str(image_path)
        if name != origin:
            self.origins[name] = origin
        return name

    def restore(self, pot_index, slot_index):
        """Puts the original club back in this place."""
        current = self.pots[pot_index][slot_index]
        origin = self.origins.pop(current, None)
        if origin is None:
            return current
        self.custom_logos.pop(current, None)
        self._rename_in_constraints(current, origin)
        self.pots[pot_index][slot_index] = origin
        self.countries.setdefault(origin, base_countries(self.comp).get(origin, ""))
        return origin

    def apply_template(self, template, constraints=()):
        """Replaces ALL the pots at once, from a template.

        `template` is what load_template() returns: a list of pots, each
        pot being a list of dicts {'club', 'country', 'image'}. It has
        already been checked, so nothing is revalidated here: that would
        be checking the same thing twice in two places, and the day the two
        no longer agreed, nobody would know which one was right.

        Previous replacements are forgotten: a template describes all of
        the pots, it does not stack on top of whatever was there. The
        original club of a place remains the one from the CSV, not the one
        the user had put there by hand.
        """
        base = base_pots(self.comp)
        self.origins = {}
        self.custom_logos = {}
        # The earlier constraints leave with the earlier clubs: they were
        # about clubs that are no longer there.
        self.constraints = set(constraints)
        self.pots = []
        for pot_index, entries in enumerate(template):
            row = []
            for slot_index, entry in enumerate(entries):
                club = entry["club"]
                row.append(club)
                self.countries[club] = entry["country"]
                if entry.get("image"):
                    self.custom_logos[club] = str(entry["image"])
                origin = base[pot_index][slot_index]
                if club != origin:
                    self.origins[club] = origin
            self.pots.append(row)
        return sum(len(pot) for pot in self.pots)


# =====================================================================
#  THE DRAW, IN THE BACKGROUND
# =====================================================================

class DrawJob:
    """
    A complete draw (fixtures + matchdays) on a separate thread.

    Tk is not safe for multithreading: so NO widget is touched from the
    worker thread. It only puts its result in self._result; the view
    fetches it with poll(), called by an ordinary after(), and so on Tk's
    thread.
    """

    def __init__(self, comp, pots_model, seed=None):
        self.comp = comp
        self.model = pots_model
        self.seed = random.random() if seed is None else seed
        # Snapshot of the constraints NOW, on Tk's thread. The worker
        # thread will read this copy: if the user opened the constraints
        # box during the calculation, mutating the set while it was being
        # iterated would raise "Set changed size during iteration" in a
        # thread nobody is watching.
        self.constraints = frozenset(pots_model.constraints)
        self._result = None
        self._error = None
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def _run(self):
        try:
            engine = ENGINES[self.comp]
            teams = engine.generate_draw(
                comp=self.comp, seed=self.seed,
                pots=self.model.pots, countries=self.model.countries,
                constraints=self.constraints)
            matchdays = generate_matchdays(teams, seed=self.seed)
            if self.comp == "UECL":
                verify_matchdays(teams, matchdays)
            self._result = (teams, matchdays)
        except BaseException as exc:        # noqa: BLE001 - passed up to the view as it is
            self._error = exc

    def poll(self):
        """None while it is running, otherwise ('ok', ...) or ('error', exc)."""
        if self._error is not None:
            return ("error", self._error)
        if self._result is not None:
            return ("ok", *self._result)
        return None


# =====================================================================
#  THE CEREMONY SCRIPT
# =====================================================================

def replay_order(teams, pots, seed=None):
    """
    Replays an already resolved draw in the order of the real ceremony.

    In Monaco, a ball comes out of pot 1, the club appears, then the
    software displays its opponents. This is repeated for the 9 balls of
    pot 1, then we move on to pot 2, and so on. When the ball of a pot 2
    club comes out, its pot 1 opponents are already known: they are
    displayed, but they are not news. That is what the 'fresh' field
    below says.

    The draw itself has already been resolved in one go: a draw with
    constraints cannot be resolved club by club without risking a dead
    end. So we replay a valid result, which is also what UEFA's software
    does.

    Returns a list of dicts:
        {'pot': 1, 'club': 'Real Madrid', 'country': 'Spain',
         'opponents': [{'club', 'pot', 'home', 'fresh'}, ...]}
    """
    rng = random.Random(seed)
    revealed = set()
    script = []

    for pot_number, pot in enumerate(pots, start=1):
        balls = list(pot)
        rng.shuffle(balls)                  # the order in which the balls come out
        for club in balls:
            team = teams[club]
            rows = []
            for other in team["home"]:
                rows.append({"club": other, "pot": teams[other]["pot"],
                             "home": True})
            for other in team["away"]:
                rows.append({"club": other, "pot": teams[other]["pot"],
                             "home": False})
            rows.sort(key=lambda r: (r["pot"], not r["home"]))

            for row in rows:
                pair = frozenset((club, row["club"]))
                row["fresh"] = pair not in revealed
                revealed.add(pair)

            script.append({"pot": pot_number, "club": club,
                           "country": team["country"], "opponents": rows})
    return script


def fixtures_by_club(teams, pots):
    """For the 'by club' tab: [(pot, club, [(opponent, pot, home)])]."""
    out = []
    for pot_number, pot in enumerate(pots, start=1):
        for club in pot:
            team = teams[club]
            rows = [(o, teams[o]["pot"], True) for o in team["home"]]
            rows += [(o, teams[o]["pot"], False) for o in team["away"]]
            rows.sort(key=lambda r: (r[1], not r[2]))
            out.append((pot_number, club, rows))
    return out


# =====================================================================
#  THE JSON TEMPLATE
# =====================================================================
# Expected shape, here for a competition with 4 pots of 9:
#
#     {
#       "Pot 1": {
#         "Arsenal": {"Image": "badges/arsenal.png", "Country": "England"},
#         ... 9 clubs ...
#       },
#       "Pot 2": { ... }, "Pot 3": { ... }, "Pot 4": { ... }
#     }
#
# A relative image path is resolved against the folder of the JSON file
# itself, not against the folder the app was launched from. This is the
# only rule that makes a template movable: zip the JSON and its badges
# together, and it works on another machine.

# "Pot 1", "pot 1", "POT_1", "Pot1": the same thing. Only the number is
# kept. Being fussy about the space or the capital letter protects against
# nothing and wastes ten minutes for whoever writes the file by hand.
_POT_KEY = re.compile(r"^\s*pot\s*[_\-]?\s*(\d+)\s*$", re.IGNORECASE)

# Extensions that Pillow opens without a plugin. They are only used to
# give a clear message BEFORE trying to open the file.
_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}


class TemplateError(Exception):
    """The template is refused. `problems` carries the detail, line by line.

    Each problem is a pair (translation key, arguments), not a ready-made
    sentence: draw_engine speaks no language, the view does the
    translating. ALL the problems are collected before raising, so that a
    file can be fixed in one pass and not in twelve round trips.
    """

    def __init__(self, problems):
        self.problems = problems
        super().__init__("%d problem(s) in the template" % len(problems))


class ConstraintError(TemplateError):
    """An inconsistent constraint: a named club that is not in the pots.

    A subclass of TemplateError, not a separate exception. The view
    already knows how to read .problems and translate each key, so an
    existing `except TemplateError` catches it without another line. It
    still keeps its own name, which allows catching it alone, provided it
    is written BEFORE TemplateError in the except chain; otherwise the
    parent swallows it and the child branch never runs.
    """


def _kind(value):
    """The type of a JSON value, in words, for an error message."""
    return {dict: "an object", list: "a list", str: "a string",
            bool: "a boolean", int: "a number", float: "a number",
            type(None): "null"}.get(type(value), type(value).__name__)


def _read_constraints(raw, clubs):
    """Turns the JSON value "constraints" into a set of (host, guest) pairs.

    A constraint is an ORDERED pair: ["Liverpool", "Real Madrid"] means
    "Liverpool does not host Real Madrid". The reverse remains allowed; to
    forbid both directions, both pairs must be written.

    Returns (constraints, problems). The problems are collected, never
    raised here: the caller decides what to do with them, as for the rest
    of the template.

    A set of tuples, and not the JSON's list of lists, for two reasons.
    First, speed: options() is called up to 200,000 times per draw, and
    `in` on a set costs O(1) against O(n) on a list. Second, correctness:
    ('a','b') == ['a','b'] is False in Python, so a list of lists passed
    to the engine would never trigger anything, with no error or message.
    A list is not hashable anyway, so it cannot go into a set: converting
    to a tuple is compulsory, which is lucky.
    """
    problems = []
    pairs = set()
    if raw is None:
        return pairs, problems
    if not isinstance(raw, list):
        problems.append(("tpl_cst_not_list", {"kind": _kind(raw)}))
        return pairs, problems

    # Case-insensitive comparison, as for the "Pot n" keys: the file is
    # written by hand, and refusing "liverpool" teaches nobody anything.
    known = {club.casefold(): club for club in clubs}

    for number, entry in enumerate(raw, start=1):
        if not isinstance(entry, list) or len(entry) != 2:
            problems.append(("tpl_cst_pair", {"n": number,
                                              "kind": _kind(entry)}))
            continue

        names = []
        for value in entry:
            if not isinstance(value, str) or not value.strip():
                problems.append(("tpl_cst_name", {"n": number,
                                                  "kind": _kind(value)}))
                names = None
                break
            names.append(value.strip())
        if names is None:
            continue

        resolved = [known.get(name.casefold()) for name in names]
        for name, club in zip(names, resolved):
            if club is None:
                problems.append(("tpl_cst_unknown", {"n": number,
                                                     "club": name}))
        if all(resolved):
            pairs.add((resolved[0], resolved[1]))

    return pairs, problems


def load_template(path, comp, per_pot, pot_count, known_countries=()):
    """Reads a JSON template and makes it ready for PotsModel.apply_template().

    Returns (pots, constraints, warnings):
        pots         [[{'club','country','image'}, ...], ...]
        constraints  {(host, guest), ...}  -- set of tuples, already checked
        warnings     [(key, kwargs), ...]  -- non-blocking

    Raises TemplateError if anything is wrong. Nothing is applied until
    EVERYTHING has been checked: a half-loaded template would leave
    inconsistent pots, harder to diagnose than a clean refusal.

    The checks, in order:
        1.  the file opens and reads as JSON
        2.  the top level is an object
        3.  every key looks like "Pot <n>"
        4.  there are exactly `pot_count` pots, numbered 1..n
        5.  every pot is an object
        6.  every pot contains exactly `per_pot` clubs
        7.  the total is indeed pot_count x per_pot clubs
        8.  no empty club name
        9.  no duplicate club name, all pots combined
        10. every club is an object carrying Country and Image
        11. Country is not empty
        12. Image is present; "" or null means "no badge"
        13. the badge file exists and opens with Pillow
        14. "constraints", if present, is a list of pairs of names
        15. both clubs of every pair exist in the pots
    """
    path = Path(path)
    problems = []
    warnings = []

    # --- 1. the file -------------------------------------------------
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        # The json message already carries the line and the column: by far
        # the most useful information for fixing a hand-written file, so we
        # let it through as it is.
        raise TemplateError([("tpl_not_json", {"detail": str(exc)})]) from exc
    except OSError as exc:
        raise TemplateError([("tpl_not_json", {"detail": str(exc)})]) from exc

    # --- 2. the top level --------------------------------------------
    if not isinstance(raw, dict):
        raise TemplateError([("tpl_not_object", {"kind": _kind(raw)})])

    # --- 3 and 4. the pots -------------------------------------------
    by_number = {}
    raw_constraints = None
    for key, value in raw.items():
        # "constraints" is not a pot. We set it aside here and check it at
        # the very end: a constraint is judged against the list of clubs,
        # so that list has to be reliable first.
        if str(key).strip().casefold() == "constraints":
            raw_constraints = value
            continue
        match = _POT_KEY.match(str(key))
        if match is None:
            problems.append(("tpl_pot_unknown",
                             {"name": key, "want": pot_count}))
            continue
        by_number[int(match.group(1))] = (key, value)

    if len(by_number) != pot_count:
        problems.append(("tpl_pot_count", {"want": pot_count, "comp": comp,
                                           "got": len(by_number)}))
    for number in range(1, pot_count + 1):
        if number not in by_number:
            problems.append(("tpl_pot_missing", {"n": number}))

    # A file whose pots are not right will not be read any further:
    # looking for clubs in a structure we already know to be wrong only
    # produces noise on top of the real cause.
    if problems:
        raise TemplateError(problems)

    # --- 5 to 13. the clubs ------------------------------------------
    known = {str(name).casefold() for name in known_countries}
    seen = {}
    pots = []

    for number in range(1, pot_count + 1):
        _, entries = by_number[number]
        if not isinstance(entries, dict):
            problems.append(("tpl_pot_not_object",
                             {"n": number, "kind": _kind(entries)}))
            continue
        if len(entries) != per_pot:
            problems.append(("tpl_pot_size", {"n": number, "got": len(entries),
                                              "want": per_pot}))

        row = []
        for name, body in entries.items():
            club = str(name).strip()
            if not club:
                problems.append(("tpl_club_blank", {"n": number}))
                continue
            if club.casefold() in seen:
                problems.append(("tpl_club_dupe", {"club": club}))
                continue
            seen[club.casefold()] = number

            if not isinstance(body, dict):
                problems.append(("tpl_club_not_object", {"club": club}))
                continue

            # --- the association ---
            country = str(body.get("Country") or "").strip()
            if not country:
                problems.append(("tpl_no_country", {"club": club}))
            elif known and country.casefold() not in known:
                # Not an error: the engine only compares strings with each
                # other. An unexpected name therefore works perfectly well;
                # it just deserves to be shown, in case it is a typo that
                # would break the rule of at most two opponents per
                # association.
                warnings.append(("tpl_w_country",
                                 {"club": club, "country": country}))

            # --- the badge ---
            image = None
            if "Image" not in body:
                problems.append(("tpl_no_image_key", {"club": club}))
            else:
                image = _check_image(body["Image"], club, path.parent,
                                     problems, warnings)

            row.append({"club": club, "country": country, "image": image})

        pots.append(row)

    # --- 7. the final count ------------------------------------------
    # Last safeguard, and only if everything else passed: a club already
    # refused above is necessarily missing from the total, and repeating
    # "one is missing" after saying why teaches nobody anything.
    total = sum(len(row) for row in pots)
    want = pot_count * per_pot
    if not problems and total != want:
        problems.append(("tpl_total", {"got": total, "want": want}))

    if problems:
        raise TemplateError(problems)

    # The constraints last, and only if the pots are right: saying
    # "Newcastle is not in the pots" when pot 2 is unreadable is noise on
    # top of the real cause.
    constraints, cst_problems = _read_constraints(
        raw_constraints, [entry["club"] for row in pots for entry in row])
    if cst_problems:
        raise ConstraintError(cst_problems)

    return pots, constraints, warnings


def _check_image(value, club, base_dir, problems, warnings):
    """Resolves a badge path, or files a problem in `problems`."""
    if value is None or (isinstance(value, str) and not value.strip()):
        # "" or null: the club accepts having no badge. It is an explicit
        # choice, not an oversight, so it is only a warning.
        warnings.append(("tpl_w_no_badge", {"club": club}))
        return None

    if not isinstance(value, str):
        # A number, a list, an object... Image is read as a path, so
        # anything that is not a string is refused as it is.
        problems.append(("tpl_image_bad", {"club": club, "path": repr(value)}))
        return None

    # Path() rather than os.path.join: it swallows Windows separators as
    # well as Unix ones, and expanduser() makes "~/badges/..." paths work.
    candidate = Path(value.strip()).expanduser()
    if not candidate.is_absolute():
        candidate = (base_dir / candidate).resolve()

    if not candidate.is_file():
        problems.append(("tpl_image_missing",
                         {"club": club, "path": str(candidate)}))
        return None
    if candidate.suffix.lower() not in _IMAGE_SUFFIXES:
        problems.append(("tpl_image_bad",
                         {"club": club, "path": str(candidate)}))
        return None

    # We really open it: a .png extension proves nothing, and an
    # unreadable file must be refused here, not three screens later in the
    # middle of the ceremony.
    try:
        from PIL import Image
        with Image.open(candidate) as img:
            img.verify()
    except Exception:
        problems.append(("tpl_image_bad",
                         {"club": club, "path": str(candidate)}))
        return None
    return candidate


# =====================================================================
#  SAVING THE CURRENT POTS
# =====================================================================
# The exact inverse of load_template: whatever comes out of here must be
# able to go back in through there, without editing. That is the only
# rule that matters in this section, and the end-to-end test checks it.

SAVED_DIR = USER_DIR / "templates" / "saved"

# Characters that a club name may contain but that a Windows file name
# refuses. We replace them instead of removing them: "1899 Hoffenheim /
# TSG" and "1899 Hoffenheim TSG" would otherwise give two different clubs
# with the same file.
_BAD_NAME_CHARS = '<>:"/\\|?*'


class SaveError(Exception):
    """Saving failed. Nothing was left on the disk.

    Carries `problems` like TemplateError, and for the same reason: the
    view displays both with the same code, and draw_engine continues to
    speak no language.
    """

    def __init__(self, problems):
        self.problems = problems
        super().__init__("%d problem(s) while saving" % len(problems))

def _stamp():
    """20260826-143012: the date then the time, with no exotic separator.

    In this order the alphabetical sort of the folder is also the
    chronological sort, which is not true of 26-08-2026.
    """
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _safe_filename(name):
    """A club name made safe to put on a Windows disk."""
    cleaned = "".join("_" if c in _BAD_NAME_CHARS else c for c in name)
    cleaned = cleaned.strip().strip(".")          # Windows refuses both
    return cleaned or "club"


def _relative_to(target, start):
    """target seen from start, in POSIX style, or None if that is impossible.

    os.path.relpath rather than Path.relative_to: the latter refuses to
    climb up, so it cannot write "../../assets/...". On another volume
    (the template on C:, the badge on D:) there is no relative path at all,
    and relpath raises ValueError: we return None and the caller falls
    back on the absolute path.
    """
    import os
    try:
        return Path(os.path.relpath(target, start)).as_posix()
    except ValueError:
        return None


def save_template(model, logo_lookup=None, dest_dir=None, stamp=None):
    """Writes the current pots to templates/saved/<COMP>_<timestamp>.json.

    Returns (path, warnings):
        path      the Path of the file written
        warnings  [(key, kwargs), ...]  -- non-blocking

    `logo_lookup` is called with a club name and returns the path of its
    original badge, or None. The view passes images.club_logo_path: this is
    the only way for draw_engine to know about the badges in assets/
    without importing images.py, which drags customtkinter in behind it
    and would turn the engine into an interface module.

    Where each club's image comes from, in order:
        1. the one the user imported in the replacement box
        2. otherwise the one in assets/images/clubs/<COMP>/
        3. otherwise nothing: "Image" is "", the initials will be drawn

    An image already in the project is written as a relative path
    ("../../assets/..."); an image imported from elsewhere is COPIED into
    a badges/ folder next to the JSON. A saved template therefore stays
    readable after the original has been moved, and can be carried around
    by zipping the folder, which load_template's resolution of relative
    paths makes possible, since templates/saved/ is at the same depth as
    templates/<season>/.

    Raises SaveError if the disk refuses anything. The folder of copied
    badges is then deleted: a failed save must leave nothing behind,
    otherwise the next one hesitates between two sets of half-written
    files.
    """
    import shutil

    dest_dir = Path(dest_dir) if dest_dir else SAVED_DIR
    stamp = stamp or _stamp()
    base_name = "%s_%s" % (model.comp, stamp)
    json_path = dest_dir / (base_name + ".json")

    # The copies go into a folder named after the template, not into a
    # shared badges/: two saves of the same club with two different images
    # would overwrite each other, and the older of the two templates would
    # start showing the newer one's badge.
    badges_dir = dest_dir / "badges" / base_name

    warnings = []
    to_copy = []            # (source, name of the copied file, convert?)
    used_names = set()
    payload = {}
    # Clubs without a badge are counted, not listed: in the Conference
    # League two thirds of the field have none, and twenty-three identical
    # lines in the report bury the only warning worth reading.
    no_badge = 0

    for pot_index, pot in enumerate(model.pots):
        entries = {}
        for club in pot:
            source = model.logo_for(club)
            imported = source is not None
            if source is None and logo_lookup is not None:
                source = logo_lookup(club)

            if source is None:
                entries[club] = {"Image": "", "Country": model.country_of(club)}
                no_badge += 1
                continue

            source = Path(source)
            if not source.is_file():
                # The typical case: a file imported then deleted during
                # the session. Refusing the whole template for that would
                # be disproportionate; the club knows how to show its
                # initials.
                entries[club] = {"Image": "", "Country": model.country_of(club)}
                warnings.append(("sv_w_gone", {"club": club,
                                               "path": str(source)}))
                continue

            if imported:
                # The file picker lets "All files" through, so a .tiff
                # that Pillow opens perfectly well can get this far.
                # load_template, for its part, refuses extensions it does
                # not know: we convert to PNG when copying, otherwise the
                # app would produce a template that it could not read back.
                suffix = source.suffix.lower()
                convert = suffix not in _IMAGE_SUFFIXES
                if convert:
                    suffix = ".png"
                stem = _safe_filename(club)
                name = stem + suffix
                # Two clubs can end up with the same name once cleaned;
                # we number them rather than overwrite.
                n = 2
                while name.casefold() in used_names:
                    name = "%s_%d%s" % (stem, n, suffix)
                    n += 1
                used_names.add(name.casefold())
                to_copy.append((source, name, convert))
                image = "badges/%s/%s" % (base_name, name)
            else:
                image = _relative_to(source, dest_dir) or source.as_posix()

            entries[club] = {"Image": image,
                             "Country": model.country_of(club)}

        payload["Pot %d" % (pot_index + 1)] = entries

    # Whatever comes out of here must be able to go back in through
    # load_template without editing: the constraints are part of that.
    # They are written last and only if there are any, so that a template
    # without constraints keeps exactly the shape it always had.
    if model.constraints:
        payload["constraints"] = [[host, guest]
                                  for host, guest in sorted(model.constraints)]

    # --- the disk, at last -------------------------------------------
    made_badges = False
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        if to_copy:
            made_badges = not badges_dir.exists()
            badges_dir.mkdir(parents=True, exist_ok=True)
            for source, name, convert in to_copy:
                if convert:
                    from PIL import Image
                    with Image.open(source) as img:
                        img.convert("RGBA").save(badges_dir / name)
                else:
                    shutil.copyfile(source, badges_dir / name)
        text = json.dumps(payload, indent=2, ensure_ascii=False)
        json_path.write_text(text + "\n", encoding="utf-8")
    except (OSError, ValueError) as exc:
        # ValueError: Pillow refuses to save an image that it was
        # nonetheless able to open. Rare, but it is a write failure like
        # any other, and it must leave through the same clean-up.
        if made_badges:
            shutil.rmtree(badges_dir, ignore_errors=True)
        raise SaveError([("sv_failed", {"detail": str(exc)})]) from exc

    if to_copy:
        warnings.append(("sv_w_copied", {"n": len(to_copy),
                                         "folder": badges_dir.name}))
    if no_badge:
        warnings.append(("sv_w_no_badge", {"n": no_badge}))
    return json_path, warnings
