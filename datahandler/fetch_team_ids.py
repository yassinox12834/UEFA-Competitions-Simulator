from uefa.config import REFERENCE_DIR
import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

URL = "https://v3.football.api-sports.io/teams"
HEADERS = {"x-apisports-key": os.getenv("API_KEY")}

LEAGUES = {2: "UCL", 3: "UEL", 848: "UECL"}
SEASON = 2024

OUT_DIR = REFERENCE_DIR
OUT_DIR.mkdir(parents=True, exist_ok=True)

for league_id, name in LEAGUES.items():
    resp = requests.get(URL, headers=HEADERS,
                         params={"league": league_id, "season": SEASON})
    data = resp.json()

    if data.get("errors"):
        print(f"warning, {name}: {data['errors']}")
        continue

    ids = {t["team"]["name"]: t["team"]["id"] for t in data["response"]}

    with open(OUT_DIR / f"{name}.json", "w", encoding="utf-8") as f:
        json.dump(ids, f, indent=2, ensure_ascii=False)

    print(f"{name}: saved {len(ids)} teams") # the end