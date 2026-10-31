"""Mark finals as played on neutral ground, in fixtures_25.csv itself.

    python -m datahandler.add_neutral_venue

build_fixtures_csv.py already does this. The script is kept for a CSV
built before it did: it adds the column, or refreshes it, in place, and
running it twice changes nothing. (It used to read fixtures.csv and write
fixtures_updated.csv, neither of which the rest of the pipeline uses.)
"""

import pandas as pd

from uefa.config import FIXTURES_CSV


def main():
    df = pd.read_csv(FIXTURES_CSV)
    neutral = df["round"].eq("Final").map({True: True, False: None})
    if "neutral_venue" in df.columns:
        df["neutral_venue"] = neutral
    else:
        df.insert(loc=df.columns.get_loc("away_team") + 1,
                  column="neutral_venue", value=neutral)
    df.to_csv(FIXTURES_CSV, index=False)
    print(f"{int(neutral.notna().sum())} finals marked neutral in {FIXTURES_CSV}")


if __name__ == "__main__":
    main()
