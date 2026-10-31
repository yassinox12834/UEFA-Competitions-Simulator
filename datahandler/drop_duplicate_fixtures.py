"""Keep one row per fixture_id, in fixtures_25.csv itself.

    python -m datahandler.drop_duplicate_fixtures

build_fixtures_csv.py already does this. Kept for a CSV built before it
did; running it twice changes nothing. (It used to read
fixtures_updated.csv and write fixtures_without.csv.)
"""

import pandas as pd

from uefa.config import FIXTURES_CSV


def main():
    df = pd.read_csv(FIXTURES_CSV)
    before = len(df)
    df = df.drop_duplicates(subset=["fixture_id"], keep="first")
    df.to_csv(FIXTURES_CSV, index=False)
    print(f"{before} rows -> {len(df)} rows in {FIXTURES_CSV}")


if __name__ == "__main__":
    main()
