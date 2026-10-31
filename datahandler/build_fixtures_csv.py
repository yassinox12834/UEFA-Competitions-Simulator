"""Build data/processed/fixtures_25.csv from the raw API answers.

    python -m datahandler.build_fixtures_csv

What it does, in order:

    1. reads every data/raw/fixtures_<COMP>/**/*.json, season sub-folders
       included (the old glob("*.json") only looked at the top folder,
       found nothing, and wrote an EMPTY table over the real one);
    2. keeps one row per fixture_id: a match between two clubs of the
       lists is in both clubs' files (this was drop_duplicate_fixtures.py);
    3. marks every match whose round is "Final" as played on neutral
       ground (this was add_neutral_venue.py);
    4. refuses to write anything if no fixture was found.

The two older scripts still work on an existing fixtures_25.csv, but this
one already does their job.
"""

import json

import pandas as pd

from uefa.config import COMPETITIONS, FIXTURES_CSV, raw_fixtures_dir


def row_of(match):
    """One API fixture -> one flat row, columns in the order of the CSV."""
    fixture, league, teams = match["fixture"], match["league"], match["teams"]
    score = match["score"]
    return {
        "fixture_id": fixture["id"],
        "date": fixture["date"],
        "timestamp": fixture["timestamp"],
        "season": league["season"],
        "league_id": league["id"],
        "league": league["name"],
        "country": league["country"],
        "round": league["round"],
        "home_id": teams["home"]["id"],
        "home_team": teams["home"]["name"],
        "away_id": teams["away"]["id"],
        "away_team": teams["away"]["name"],
        # True for a final, empty otherwise: an empty cell reads back as
        # NaN, which elo_score_updating.py treats as "not neutral".
        "neutral_venue": True if league["round"] == "Final" else None,
        "home_goals": match["goals"]["home"],
        "away_goals": match["goals"]["away"],
        "winner_home": teams["home"]["winner"],
        "winner_away": teams["away"]["winner"],
        "referee": fixture["referee"],
        "stadium": fixture["venue"]["name"],
        "city": fixture["venue"]["city"],
        "status": fixture["status"]["short"],
        "elapsed": fixture["status"]["elapsed"],
        "ht_home": score["halftime"]["home"],
        "ht_away": score["halftime"]["away"],
        "ft_home": score["fulltime"]["home"],
        "ft_away": score["fulltime"]["away"],
        "et_home": score["extratime"]["home"],
        "et_away": score["extratime"]["away"],
        "pen_home": score["penalty"]["home"],
        "pen_away": score["penalty"]["away"],
    }


def build():
    """The fixtures as a DataFrame, one row per fixture_id. Writes nothing."""
    rows, files = [], 0
    for comp in COMPETITIONS:
        for path in sorted(raw_fixtures_dir(comp).rglob("*.json")):
            files += 1
            data = json.loads(path.read_text(encoding="utf-8"))
            rows.extend(row_of(match) for match in data.get("response", []))
    if not rows:
        folders = ", ".join(str(raw_fixtures_dir(c)) for c in COMPETITIONS)
        raise SystemExit(f"No fixture found in {files} file(s) under {folders}. "
                         f"Nothing written: {FIXTURES_CSV.name} is unchanged.")
    df = pd.DataFrame(rows)
    return df.drop_duplicates(subset="fixture_id", keep="first").reset_index(drop=True)


def main():
    df = build()
    df.to_csv(FIXTURES_CSV, index=False, encoding="utf-8")
    print(f"Wrote {len(df)} fixtures to {FIXTURES_CSV}")


if __name__ == "__main__":
    main()
