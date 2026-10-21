"""Build the (league, round) -> (category, comp_mult, stage_mult) table.

Run once to bootstrap data/reference/coef_table.csv, then hand-correct the
CSV. The CSV is the source of truth; this script is only the generator.
Re-running it will not overwrite an existing CSV unless --force is given.

Usage:
    python model/categorising.py            # report only
    python model/categorising.py --write    # write the CSV
    python model/categorising.py --write --force
"""

import csv
import json
import re
import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
CSV_LINK = BASE_DIR / "data" / "processed" / "fixtures_25.csv"
JSON_LINK_COEFS = BASE_DIR / "data" / "reference" / "coefs.json"
OUT_CSV = BASE_DIR / "data" / "reference" / "coef_table.csv"


# ---------------------------------------------------------------------------
# 1. The eleven leagues that cannot be inferred from their rounds
# ---------------------------------------------------------------------------

NAME_OVERRIDES = {
    # Identical round sets, three different weights.
    "UEFA Champions League":          "UCL",
    "UEFA Europa League":             "UEL",
    "UEFA Europa Conference League":  "UECL",

    # One 'Final' each, but not a domestic super cup.
    "UEFA Super Cup":                 "UEFA Super Cup",
    "FIFA Intercontinental Cup":      "Intercontinental",

    # Has semi-finals, so inference would call it a cup. It is the
    # Supercoppa Italiana in its four-team format.
    "Super Cup":                      "Domestic Super Cup",

    # Pre-season and exhibition tournaments wearing competitive clothes.
    "Friendlies Clubs":               "Friendly",
    "Emirates Cup":                   "Friendly",
    "The Atlantic Cup":               "Friendly",
    "Reykjavik Cup":                  "Friendly",
    "Premier League - Summer Series": "Friendly",
}


# ---------------------------------------------------------------------------
# 2. Inference rules, tested in order. First hit wins.
# ---------------------------------------------------------------------------

# A league season: any of these round families means the competition is a
# round-robin, whatever else it also contains. Tested FIRST, which is what
# saves Bundesliga and Eredivisie from their 'Conference League Play-offs -
# Final' rounds being read as a European final.
_LEAGUE_MARKERS = re.compile(
    r"regular season"
    r"|championship round"
    r"|relegation round"
    r"|\d+(?:st|nd|rd|th) phase",
    re.I,
)

# A UEFA league phase. Only reachable if the name override missed, which
# means an unknown UEFA competition: worth a loud report, not a guess.
_UEFA_MARKER = re.compile(r"league stage", re.I)

# Knockout structure: this is a cup.
_CUP_MARKERS = re.compile(
    r"round of \d+"
    r"|quarter-?finals?"
    r"|semi-?finals?"
    r"|^group stage"
    r"|^\d+(?:st|nd|rd|th) round$",
    re.I,
)

_FINAL_ONLY = re.compile(r"^finals?$", re.I)


def infer_category(league, rounds):
    """Guess the category of `league` from its set of round strings.

    rounds: an iterable of the distinct round strings seen for this league.
    Returns a category name, or None if no rule fires.
    """
    if league in NAME_OVERRIDES:
        return NAME_OVERRIDES[league]

    rounds = list(rounds)

    if any(_LEAGUE_MARKERS.search(r) for r in rounds):
        return "Domestic League"

    if any(_UEFA_MARKER.search(r) for r in rounds):
        return None  # unknown UEFA competition, refuse to guess the weight

    # A single round, and that round is 'Final': one match, so a super cup.
    # Checked BEFORE the cup markers, because '^finals?$' is also a cup marker
    # in spirit and a one-match competition is not a cup.
    if len(rounds) == 1 and _FINAL_ONLY.search(rounds[0]):
        return "Domestic Super Cup"

    if any(_CUP_MARKERS.search(r) for r in rounds):
        return "Domestic Cup"

    return None


# ---------------------------------------------------------------------------
# 3. Round string -> stage name, scoped by category
# ---------------------------------------------------------------------------

_UEFA_STAGES = [
    (r"knockout round play-?offs?", "Playoff"),      # Feb tie: MUST be first
    (r"qualifying round",           "Qualifying"),
    (r"^play-?offs?$",              "Qualifying"),   # the August qualifier
    (r"league stage",               "League"),
    (r"^group stage",               "League"),       # pre-2024 format
    (r"round of 16",                "Round of 16"),
    (r"quarter-?finals?",           "Quarter Final"),
    (r"semi-?finals?",              "Semi Final"),
    (r"^finals?$",                  "Final"),
]

_CUP_STAGES = [
    (r"round of 64",                "Early Rounds"),  # Coupe de France
    (r"round of 32",                "Round of 32"),
    (r"round of 16",                "Round of 16"),
    (r"quarter-?finals?",           "Quarter Final"),
    (r"semi-?finals?",              "Semi Final"),
    (r"^finals?$",                  "Final"),         # 'Finals' too: Svenska
    (r"^group stage",               "Early Rounds"),
    (r"^\d+(?:st|nd|rd|th) round$", "Early Rounds"),
]

_FLAT = [(r".", "Default")]  # one stage only; any non-empty round matches

_RAW_STAGE_PATTERNS = {
    "UCL":                _UEFA_STAGES,
    "UEL":                _UEFA_STAGES,
    "UECL":               _UEFA_STAGES,
    "Domestic Cup":       _CUP_STAGES,
    "League":             _FLAT,
    "Domestic Super Cup": _FLAT,
    "UEFA Super Cup":     _FLAT,
    "Intercontinental":   _FLAT,
    "Friendly":           _FLAT,
}

# Compile once. Compiling inside the loop would recompile ~1400 times.
STAGE_PATTERNS = {
    cat: [(re.compile(p, re.I), stage) for p, stage in rules]
    for cat, rules in _RAW_STAGE_PATTERNS.items()
}


def resolve_stage(category, round_str):
    """Return the stage name, or None if no rule matches."""
    for pattern, stage in STAGE_PATTERNS[category]:
        if pattern.search(round_str):
            return stage
    return None


# ---------------------------------------------------------------------------
# 4. Coefficient lookup
# ---------------------------------------------------------------------------
def load_coefs(path):

    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)

    out = {}
    for cat, cfg in raw["competitions"].items():
        out[cat] = {
            stage: {"comp_mult": cfg["comp_mult"], "stage_mult": stage_mult}
            for stage, stage_mult in cfg["stages"].items()
        }
    return out, raw["k_base"], raw["k_max"]

# ---------------------------------------------------------------------------
# 5. Main
# ---------------------------------------------------------------------------

def main(write=False, force=False):
    df = pd.read_csv(CSV_LINK)
    coefs = load_coefs(JSON_LINK_COEFS)

    pairs = df[["league", "round"]].drop_duplicates()

    # --- categorise every league -------------------------------------------
    categories = {}
    for league, group in pairs.groupby("league"):
        categories[league] = infer_category(league, group["round"].tolist())

    print(f"{len(categories)} leagues, "
          f"{len(pairs)} distinct (league, round) pairs\n")

    print("=== CATEGORIES ===")
    by_cat = {}
    for league, cat in sorted(categories.items()):
        by_cat.setdefault(cat, []).append(league)
    for cat in sorted(by_cat, key=lambda c: (c is None, str(c))):
        tag = "*** UNRESOLVED ***" if cat is None else cat
        print(f"\n{tag}  ({len(by_cat[cat])})")
        for league in by_cat[cat]:
            mark = "  [override]" if league in NAME_OVERRIDES else ""
            print(f"    {league}{mark}")

    # --- resolve every pair ------------------------------------------------
    rows = []
    bad_category, bad_stage, bad_coef = [], [], []

    for league, round_str in pairs.itertuples(index=False):
        cat = categories[league]
        if cat is None:
            bad_category.append((league, round_str))
            continue

        stage = resolve_stage(cat, round_str)
        if stage is None:
            bad_stage.append((league, round_str, cat))
            continue

        entry = coefs.get(cat, {}).get(stage)
        if entry is None:
            bad_coef.append((cat, stage))
            continue

        rows.append({
            "league":     league,
            "category":   cat,
            "round":      round_str,
            "stage":      stage,
            "comp_mult":  entry["comp_mult"],
            "stage_mult": entry["stage_mult"],
        })

    # --- report ------------------------------------------------------------
    print("\n=== PROBLEMS ===")

    if bad_category:
        print(f"\nNo category ({len(bad_category)} pairs):")
        for league, rnd in bad_category[:30]:
            print(f"    {league!r:40} {rnd!r}")

    if bad_stage:
        print(f"\nNo stage ({len(bad_stage)} pairs):")
        for league, rnd, cat in bad_stage[:30]:
            print(f"    [{cat}] {league!r:35} {rnd!r}")

    if bad_coef:
        print(f"\nMissing from coefs.json ({len(set(bad_coef))} entries):")
        for cat, stage in sorted(set(bad_coef)):
            print(f"    coefs[{cat!r}][{stage!r}]")

    if not (bad_category or bad_stage or bad_coef):
        print("    none")

    print(f"\n{len(rows)} / {len(pairs)} pairs resolved")

    # --- write -------------------------------------------------------------
    if not write:
        print("\n(report only; pass --write to build the CSV)")
        return

    if bad_category or bad_stage or bad_coef:
        print("\nREFUSING TO WRITE: fix the problems above first.")
        print("A partial table merges to NaN and hides the gap.")
        return

    if OUT_CSV.exists() and not force:
        print(f"\nREFUSING TO WRITE: {OUT_CSV} already exists.")
        print("It is the source of truth and may hold hand corrections.")
        print("Pass --force to overwrite it.")
        return

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    rows.sort(key=lambda r: (r["league"], r["round"]))
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=[
            "league", "category", "round", "stage", "comp_mult", "stage_mult",
        ])
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nWrote {len(rows)} rows to {OUT_CSV}")


if __name__ == "__main__":
    main(write="--write" in sys.argv, force="--force" in sys.argv)