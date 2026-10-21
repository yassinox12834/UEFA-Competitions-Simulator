from uefa.config import CLUB_LOGOS_DIR, REFERENCE_DIR
import pathlib
import json
import requests
competitions = ("UCL", "UEL", "UECL")
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

for compet in competitions:
    with open(REFERENCE_DIR / f"{compet}_updated.json", "r", encoding="utf-8") as file:
        dic = json.load(file)

    for team_name, ID in dic.items():
        image_URL = f"https://media.api-sports.io/football/teams/{ID}.png"
        response = requests.get(image_URL, headers=headers)

        final_link = CLUB_LOGOS_DIR / compet / f"{team_name}_logo.png"
        final_link.parent.mkdir(parents=True, exist_ok=True)
        if response.status_code == 200:
            with open(final_link, "wb") as file2:
                file2.write(response.content)




