"""
Single source of truth for every path and every constant of the project.

Nothing else in the code is allowed to write a path by hand. If a folder
moves, you change it here once and the whole project follows.

Run any module from the UEFA/ folder like this:
    python -m uefa.datahandler.fetch_fixtures
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# uefa/config.py  ->  .parent = uefa/  ->  .parent.parent = UEFA/
BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------- data
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"              # untouched API answers
PROCESSED_DIR = DATA_DIR / "processed"  # cleaned CSVs
REFERENCE_DIR = DATA_DIR / "reference"  # ids, seeds, coefficients
ARCHIVE_DIR = DATA_DIR / "archive"      # old versions, kept just in case

# ---------------------------------------------------------------- assets
ASSETS_DIR = BASE_DIR / "assets"
IMAGES_DIR = ASSETS_DIR / "images"
CLUB_LOGOS_DIR = IMAGES_DIR / "clubs"     # clubs/UCL/, clubs/UEL/, clubs/UECL/
COMPET_LOGOS_DIR = IMAGES_DIR / "compets"
FLAGS_DIR = IMAGES_DIR / "flags"

# ---------------------------------------------------------------- named files
FIXTURES_CSV = PROCESSED_DIR / "fixtures_25.csv"
COUNTRIES_CSV = PROCESSED_DIR / "countries_filled_25.csv"
CLEANED_CLUBS_CSV = PROCESSED_DIR / "cleaned_clubs_25.csv"
ALL_COMPETITIONS_CSV = PROCESSED_DIR / "all_competitions_25.csv"

COUNTRY_SEEDS_JSON = REFERENCE_DIR / "country_seeds.json"
TEAM_SEEDS_JSON = REFERENCE_DIR / "team_seed.json"
COEFS_JSON = REFERENCE_DIR / "coefs.json"

# ---------------------------------------------------------------- competitions
COMPETITIONS = ("UCL", "UEL", "UECL")
LEAGUE_IDS = {"UCL": 2, "UEL": 3, "UECL": 848}


def team_ids_path(competition: str) -> Path:
    """data/reference/UCL.json for competition='UCL'."""
    return REFERENCE_DIR / f"{competition}.json"


def raw_fixtures_dir(competition: str) -> Path:
    """data/raw/fixtures_UCL for competition='UCL'."""
    return RAW_DIR / f"fixtures_{competition}"


# ---------------------------------------------------------------- API
load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("API_KEY")
API_BASE = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}
MEDIA_BASE = "https://media.api-sports.io/football"
