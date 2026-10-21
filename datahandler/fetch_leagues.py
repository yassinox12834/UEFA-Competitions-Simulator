from uefa.config import REFERENCE_DIR
import requests
import dotenv
import os
import json
import pathlib
dotenv.load_dotenv()


API_KEY = os.getenv('API_KEY')

params = {"id" : 848, "season" : 2024}

URL = "https://v3.football.api-sports.io/leagues"
headers = {"x-apisports-key": API_KEY}

response = requests.get(URL, headers=headers, params=params)
data = response.json()

if data.get("errors"):
    print(f"warning: {data['errors']}")
else:
    out_path = REFERENCE_DIR / "confr.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"saved -> {out_path}")

    for item in data["response"]:
        league = item["league"]
        country = item["country"]
        print(f"{league['id']} - {league['name']} ({league['type']})")
        print(f"  country: {country['name']}")
        print(f"  logo:    {league['logo']}")

        for season in item["seasons"]:
            cov = season["coverage"]
            print(f"  season {season['year']}: {season['start']} -> {season['end']}"
                  f"{' [current]' if season['current'] else ''}")
            print(f"    fixtures events:  {cov['fixtures']['events']}")
            print(f"    fixtures lineups: {cov['fixtures']['lineups']}")
            print(f"    standings:        {cov['standings']}")
            print(f"    top scorers:      {cov['top_scorers']}")
