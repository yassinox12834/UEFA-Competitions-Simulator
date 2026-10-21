from uefa.config import COMPET_LOGOS_DIR
import pathlib
import requests
competitions = ("UCL", "UEL", "UECL")
IDs = (2, 3, 848)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

for ID, name in zip(IDs, competitions):
  


    image_URL = f"https://media.api-sports.io/football/leagues/{ID}.png"
    response = requests.get(image_URL, headers=headers)

    final_link = COMPET_LOGOS_DIR / f"{name}_logo.png"
    final_link.parent.mkdir(parents=True, exist_ok=True)
    if response.status_code == 200:
        with open(final_link, "wb") as file2:
            file2.write(response.content)
