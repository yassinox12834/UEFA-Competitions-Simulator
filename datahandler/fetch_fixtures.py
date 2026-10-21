from uefa.config import raw_fixtures_dir, team_ids_path
# src/fetch.py
from pathlib import Path
import json, os, re, time, requests
from dotenv import load_dotenv

load_dotenv()
HEADERS  = {"x-apisports-key": os.getenv("API_KEY")}
URL = "https://v3.football.api-sports.io/fixtures"


def safe_filename(name: str) -> str:
    return re.sub(r"[^a-z0-9_]", "", name.lower().replace(" ", "_"))


def fetch_fixtures(competition: str, season: int) -> None:
    """competition is 'UCL', 'UEL' or 'UECL'. season 2024 means 2024-25."""
    ids_path = team_ids_path(competition)
    out_dir  = raw_fixtures_dir(competition)
    out_dir.mkdir(parents=True, exist_ok=True)

    team_ids = json.loads(ids_path.read_text(encoding="utf-8"))
    label = f"{season}_{str(season + 1)[-2:]}"          # 2024 -> "2024_25"

    for i, (team_name, team_id) in enumerate(team_ids.items(), start=1):
        path = out_dir / f"{safe_filename(team_name)}_{label}.json"
        if path.exists():
            print(f"skip {path.name}")
            continue

        data = requests.get(
            URL, headers=HEADERS,
            params={"season": season, "team": team_id},
        ).json()

        if data.get("errors"):
            print(f"warning, {team_name}: {data['errors']}")
            continue

        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"saved {path.name} ({data.get('results', 0)} fixtures)")

        time.sleep(1)
        if i % 10 == 0:
            time.sleep(61)


if __name__ == "__main__":
    for comp in ("UCL", "UEL", "UECL"):
        fetch_fixtures(comp, season=2024)