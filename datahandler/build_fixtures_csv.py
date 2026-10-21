from uefa.config import COMPETITIONS, FIXTURES_CSV, raw_fixtures_dir
import json
import pandas as pd
from pathlib import Path

folders = tuple(raw_fixtures_dir(c) for c in COMPETITIONS)


rows = []


for folder in folders:
    for file in folder.glob("*.json"):

        with open(file, encoding="utf-8") as f:
            data = json.load(f)

        for match in data["response"]:

            row = {

                "fixture_id": match["fixture"]["id"],

                "date": match["fixture"]["date"],

                "timestamp": match["fixture"]["timestamp"],

                "season": match["league"]["season"],

                "league_id": match["league"]["id"],

                "league": match["league"]["name"],

                "country": match["league"]["country"],

                "round": match["league"]["round"],

                "home_id": match["teams"]["home"]["id"],

                "home_team": match["teams"]["home"]["name"],

                "away_id": match["teams"]["away"]["id"],

                "away_team": match["teams"]["away"]["name"],

                "home_goals": match["goals"]["home"],

                "away_goals": match["goals"]["away"],

                "winner_home": match["teams"]["home"]["winner"],

                "winner_away": match["teams"]["away"]["winner"],

                "referee": match["fixture"]["referee"],

                "stadium": match["fixture"]["venue"]["name"],

                "city": match["fixture"]["venue"]["city"],

                "status": match["fixture"]["status"]["short"],

                "elapsed": match["fixture"]["status"]["elapsed"],

                "ht_home": match["score"]["halftime"]["home"],

                "ht_away": match["score"]["halftime"]["away"],

                "ft_home": match["score"]["fulltime"]["home"],

                "ft_away": match["score"]["fulltime"]["away"],

                "et_home": match["score"]["extratime"]["home"],

                "et_away": match["score"]["extratime"]["away"],

                "pen_home": match["score"]["penalty"]["home"],

                "pen_away": match["score"]["penalty"]["away"]

            }

            rows.append(row)

df = pd.DataFrame(rows)

df.to_csv(FIXTURES_CSV, index=False, encoding="utf-8")

print(df.head())