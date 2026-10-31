"""Run the Elo ratings forward over a season of fixtures.

Reads
    data/reference/team_seed.json    starting ratings written by hand. A club
                                     absent from it starts from its country's
                                     seed (country_seeds.json), or DEFAULT_ELO.
    data/reference/coefs.json        k_base, k_max
    data/reference/coef_table.csv    (league, round) -> comp_mult, stage_mult
    data/processed/fixtures_25.csv   the matches, played and unplayed mixed

Writes
    data/processed/eeelo_final.json    final rating per club (only with --write)
    data/processed/match_features.csv  one row per non-friendly fixture:
                                        pre-match Elo for both sides, is_home,
                                        season, timestamp, and target, the
                                        90-minute result (NaN if not played).
                                        This is what the classifier trains on.

Usage
    python model/elo_score_updating.py            # run and report
    python model/elo_score_updating.py --write    # also write the final dict
"""

import csv
import json
import sys
from pathlib import Path
import math


BASE_DIR = Path(__file__).resolve().parents[1]
JSON_TEAMS_SEED   = BASE_DIR / "data" / "reference" / "team_seed.json"
JSON_COUNTRY_SEED = BASE_DIR / "data" / "reference" / "country_seeds.json"
JSON_COEFS        = BASE_DIR / "data" / "reference" / "coefs.json"
CSV_COEF_TABLE    = BASE_DIR / "data" / "reference" / "coef_table.csv"
FIXTURES_CSV      = BASE_DIR / "data" / "processed" / "fixtures_25.csv"
OUT_JSON          = BASE_DIR / "data" / "processed" / "eeelo_final.json"
OUT_FEATURES_CSV  = BASE_DIR / "data" / "processed" / "match_features.csv"

GOAL_COLUMN_CANDIDATES = [
    ("ft_home",        "ft_away"),      # 90 minutes: what the simulation models
    ("home_goals",     "away_goals"),
    ("goals_home",     "goals_away"),
    ("home_score",     "away_score"),
    ("score_home",     "score_away"),
    ("fulltime_home",  "fulltime_away"),
]

# Country names as they appear in fixtures_25.csv -> keys of
# country_seeds.json. Checked against every distinct non-"World" value in
# the current fixtures file. A name missing from this table silently falls
# back to DEFAULT_ELO below with no error, so re-check if you refresh the
# fixtures file.
COUNTRY_ALIASES = {
    "Turkey":           "Türkiye",
    "Czech-Republic":   "Czech Republic",
    "Bosnia":           "Bosnia and Herzegovina",
    "Ireland":          "Republic of Ireland",
    "Northern-Ireland": "Northern Ireland",
}

# fixtures_25.csv uses this literal for every UEFA tie and every friendly:
# anything that is not one country's own domestic competition.
NON_DOMESTIC_COUNTRY = "World"

# Starting rating for a club with no domestic fixture anywhere in the data,
# so no country can be read off it at all (23 such clubs currently play in
# UEFA qualifying). 1450 sits near the bottom of country_seeds.json,
# between Kosovo (1450.7) and Finland (1448.5).
DEFAULT_ELO = 1450.0


# ---------------------------------------------------------------------------
# 1. The maths
# ---------------------------------------------------------------------------

def expected_score(R_A, R_B):
    """Probability that A takes the point, from the rating gap alone."""
    return 1 / (1 + 10 ** ((R_B - R_A) / 400))


def update_rating(R_A, K, S_A, E_A):
    """One Elo step. K is the most points this match can move R_A."""
    return R_A + K * (S_A - E_A)


def result_scores(home_goals, away_goals):
    """Goals -> (S_home, S_away). Win 1, draw 0.5, loss 0."""
    if home_goals > away_goals:
        return 1.0, 0.0
    if home_goals < away_goals:
        return 0.0, 1.0
    return 0.5, 0.5


# Share of the point the WINNER takes, by the way the match was decided.
# The loser takes 1 - share, so every pair sums to 1 and Elo stays zero-sum.
SHARE_90  = 1.0     # won in 90 minutes
SHARE_ET  = 0.8     # level after 90mins, won in extra time
SHARE_PEN = 0.7     # level after 120mins, won on penalties 


def rating_scores(ft_home, ft_away, final_home, final_away, status, winner_home):
    """(S_home, S_away) for the rating update, first rule that fits wins.

    1. 90 minutes not level            -> winner takes SHARE_90
    2. level after 90, 120 not level   -> winner takes SHARE_ET
    3. level after 120, status "PEN"   -> shoot-out winner takes SHARE_PEN
    4. anything else                   -> draw, 0.5 each

    ft_* is the 90-minute score, final_* includes extra time.
    winner_home is the API flag; it is only read in rule 3, where the match
    itself was level, so it can only mean the shoot-out winner. (In a second
    leg won on goals but lost on penalties it names the TIE winner, which is
    why rule 1 comes first.)
    """
    if ft_home != ft_away:
        share, home_won = SHARE_90, ft_home > ft_away
    elif final_home != final_away:
        share, home_won = SHARE_ET, final_home > final_away
    elif status == "PEN" and winner_home in (True, False):
        share, home_won = SHARE_PEN, bool(winner_home)
    else:
        return 0.5, 0.5
    s_home = share if home_won else 1.0 - share
    return s_home, 1.0 - s_home


def season_from_date(date):
    """European season label. A match in Aug-Dec belongs to the season that
    started that year; a match in Jan-Jul belongs to the season that started
    the year before. ASSUMPTION: cutoff month is July. Check against a real
    date near a season boundary in your data before trusting this."""
    return date.year if date.month >= 7 else date.year - 1


# ---------------------------------------------------------------------------
# 2. Loading
# ---------------------------------------------------------------------------

def load_seed(path):
    with open(path, encoding="utf-8-sig") as fh:
        return {club: float(rating) for club, rating in json.load(fh).items()}


def load_k_settings(path):
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    return raw["k_base"], raw["k_max"]


def load_coef_table(path):
    table = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for line in csv.DictReader(fh):
            table[(line["league"], line["round"])] = (
                float(line["comp_mult"]),
                float(line["stage_mult"]),
            )
    return table

def load_country_seeds(path):
    """Country name -> starting rating. Already on the same scale as
    team_seed.json (1319 to 1669 in the current file), so no rescaling."""
    with open(path, encoding="utf-8-sig") as fh:
        return {country: float(rating) for country, rating in json.load(fh).items()}


def build_club_country(df):
    """Club name -> country, read off DOMESTIC fixtures only.

    A UEFA tie or a friendly has country == "World", which tells you
    nothing about either side, so those rows are dropped first. Only a
    domestic-league or domestic-cup row names a real country. First
    occurrence wins; a club changing country mid-season is not handled.
    """
    domestic = df[df["country"] != NON_DOMESTIC_COUNTRY]
    club_country = {}
    for home, away, country in zip(domestic["home_team"], domestic["away_team"],
                                   domestic["country"]):
        canonical = COUNTRY_ALIASES.get(country, country)
        club_country.setdefault(home, canonical)
        club_country.setdefault(away, canonical)
    return club_country


def load_clubs(df, country_seeds):
    """Starting rating for every club that appears in the fixtures.

    Returns (provisional, no_country): provisional maps club -> starting
    rating for every club NOT already in team_seed.json, no_country is the
    subset of those that had no domestic fixture at all and therefore
    fell back to DEFAULT_ELO. Report no_country: a club in it is being
    rated on a guess, not on data.
    """
    club_country = build_club_country(df)
    all_clubs = set(df["home_team"]) | set(df["away_team"])

    provisional, no_country = {}, set()
    for club in all_clubs:
        country = club_country.get(club)
        if country in country_seeds:
            provisional[club] = country_seeds[country]
        else:
            provisional[club] = DEFAULT_ELO
            no_country.add(club)
    return provisional, no_country


def find_goal_columns(df):
    for home_col, away_col in GOAL_COLUMN_CANDIDATES:
        if home_col in df.columns and away_col in df.columns:
            return home_col, away_col
    raise KeyError(
        "No goal columns found in the fixtures. Columns present: "
        f"{sorted(df.columns)}. Add the right pair to GOAL_COLUMN_CANDIDATES."
    )


# ---------------------------------------------------------------------------
# 3. The run
# ---------------------------------------------------------------------------

def run(write=True):

    import numpy as np
    import pandas as pd

    file = load_seed(JSON_TEAMS_SEED)

    k_base, k_max = load_k_settings(JSON_COEFS)
    coef_table = load_coef_table(CSV_COEF_TABLE)

    df = pd.read_csv(FIXTURES_CSV)
    home_goals_col, away_goals_col = find_goal_columns(df)

    df["date"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)
    df["season"] = df["date"].apply(season_from_date)

    has_neutral = "neutral_venue" in df.columns
    if not has_neutral:
        print("Warning: no 'neutral_venue' column, assuming every fixture has a real home side.")

    teams_games = df.sort_values("timestamp").reset_index(drop=True)

    country_seeds = load_country_seeds(JSON_COUNTRY_SEED)
    provisional, no_country_clubs = load_clubs(df, country_seeds)

    # file (real seeds) must come SECOND: dict merge keeps the later
    # value on a key clash, so this is what makes a genuine seed win over
    # a country guess for the same club, not the other way round.
    elos = {**provisional, **file}
    elos_at_start = dict(elos)   # snapshot; elos is mutated in the loop below

    counts = {
        "played":       0,
        "unknown_club": 0,
        "no_coef":      0,
        "not_played":   0,
        "zero_k":       0,
    }
    unknown_clubs, missing_coefs = set(), set()
    training_rows = []

    for _, row in teams_games.iterrows():

        home_elo = elos.get(row["home_team"])
        away_elo = elos.get(row["away_team"])

        if home_elo is None or away_elo is None:

            counts["unknown_club"] += 1
            unknown_clubs.update(
                c for c, e in ((row["home_team"], home_elo),
                               (row["away_team"], away_elo)) if e is None
            )
            continue
        if coef_table.get((row["league"], row["round"]), (1.0, 1.0))[0] == 0:
            counts["zero_k"] += 1
            continue
        # Without the column, every match has a home side: that is what
        # the warning above promises. Reading it unconditionally raised a
        # KeyError right after printing that warning.
        v = row["neutral_venue"] if has_neutral else None
        is_neutral = (not pd.isna(v)) and bool(v)
        home_goals, away_goals = row[home_goals_col], row[away_goals_col]
        played = not (pd.isna(home_goals) or pd.isna(away_goals))
        is_home = 0 if is_neutral else 1

        # Snapshot BEFORE any update, and before we know whether this match
        # even qualifies for a rating change. A future fixture has no target
        # but still needs a features row, or you cannot predict on it later.
        training_rows.append({
            "home_team":       row["home_team"],
            "away_team":       row["away_team"],
            "elo_home_before": home_elo,
            "elo_away_before": away_elo,
            "is_home":         is_home,
            "season":          row["season"],
            "timestamp":       row["timestamp"],
            "target":          (np.sign(home_goals - away_goals) if played else np.nan),
        })

        if not played:
            counts["not_played"] += 1
            continue

        key = (row["league"], row["round"])
        if key not in coef_table:
            counts["no_coef"] += 1
            missing_coefs.add(key)
            continue

        comp_mult, stage_mult = coef_table[key]
        K = min(k_base * comp_mult * stage_mult, k_max)

        if K == 0:
            counts["zero_k"] += 1
            continue

        e_home = expected_score(home_elo, away_elo)
        e_away = expected_score(away_elo, home_elo)
        s_home, s_away = rating_scores(home_goals, away_goals,
                                       row["home_goals"], row["away_goals"],
                                       row["status"], row["winner_home"])

        elos[row["home_team"]] = update_rating(home_elo, K, s_home, e_home)
        elos[row["away_team"]] = update_rating(away_elo, K, s_away, e_away)
        counts["played"] += 1

    report(teams_games, elos, elos_at_start, counts, unknown_clubs,
           missing_coefs, no_country_clubs)

    features_df = pd.DataFrame(training_rows)
    # "Report only" used to overwrite match_features.csv anyway: running the
    # script to LOOK at the ratings silently replaced the model's training
    # data. Both outputs are now written with --write, and only then.
    if write:
        features_df.to_csv(OUT_FEATURES_CSV, index=False)
        print(f"\nWrote {len(features_df)} rows to {OUT_FEATURES_CSV} "
              f"({features_df['target'].notna().sum()} with a known result)")

    if write:
        OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        with open(OUT_JSON, "w", encoding="utf-8") as fh:
            json.dump({c: round(r, 2) for c, r in sorted(elos.items())},
                      fh, indent=2, ensure_ascii=False)
        print(f"Wrote {len(elos)} ratings to {OUT_JSON}")
    else:
        print(f"\n(report only: {len(features_df)} training rows, nothing written; "
              f"pass --write to save eeelo_final.json and match_features.csv)")

    return elos


# ---------------------------------------------------------------------------
# 4. Report
# ---------------------------------------------------------------------------

def report(fixtures, elos, starting, counts, unknown_clubs, missing_coefs,
           no_country_clubs):
    total = len(fixtures)
    print(f"{total} fixtures, {len(starting)} clubs rated "
          f"({len(starting) - len(no_country_clubs)} with a known country, "
          f"{len(no_country_clubs)} on {DEFAULT_ELO} by default)\n")

    print("=== FIXTURES ===")
    print(f"  rated                {counts['played']:6}")
    print(f"  club not in seed     {counts['unknown_club']:6}")
    print(f"  no coefficient row   {counts['no_coef']:6}")
    print(f"  not played yet       {counts['not_played']:6}")
    print(f"  K = 0 (friendly)     {counts['zero_k']:6}")
    print(f"  {'-'*30}")
    print(f"  accounted for        {sum(counts.values()):6} / {total}")

    if missing_coefs:
        print(f"\n=== MISSING FROM coef_table.csv ({len(missing_coefs)}) ===")
        for league, rnd in sorted(missing_coefs)[:20]:
            print(f"    {league!r:40} {rnd!r}")

    if unknown_clubs:
        print(f"\n=== UNRATED CLUBS, SHOULD BE EMPTY ({len(unknown_clubs)}) ===")
        for club in sorted(unknown_clubs)[:20]:
            print(f"    {club}")

    if no_country_clubs:
        print(f"\n=== NO DOMESTIC FIXTURE, STARTED AT {DEFAULT_ELO} "
              f"({len(no_country_clubs)}) ===")
        for club in sorted(no_country_clubs)[:25]:
            print(f"    {club}")

    moved = {c: elos[c] - starting[c] for c in starting}
    print("\n=== BIGGEST RISERS ===")
    for club in sorted(moved, key=moved.get, reverse=True)[:10]:
        print(f"    {club:32} {starting[club]:7.0f} -> {elos[club]:7.1f}  "
              f"({moved[club]:+.1f})")

    print("\n=== BIGGEST FALLERS ===")
    for club in sorted(moved, key=moved.get)[:10]:
        print(f"    {club:32} {starting[club]:7.0f} -> {elos[club]:7.1f}  "
              f"({moved[club]:+.1f})")

    drift = sum(elos[c] - starting[c] for c in starting)
    print(f"\nTotal rating drift across all {len(starting)} rated clubs: {drift:+.2f}")
    print("(should be ~0: Elo is zero-sum when both clubs in a match are rated)")


if __name__ == "__main__":
    run(write="--write" in sys.argv)