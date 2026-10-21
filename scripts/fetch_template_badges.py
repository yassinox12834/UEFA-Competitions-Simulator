# -*- coding: utf-8 -*-
"""
fetch_template_badges.py - remplit les ecussons manquants d'un modele.

    python scripts/fetch_template_badges.py                     # les trois
    python scripts/fetch_template_badges.py UCL                 # un seul
    python scripts/fetch_template_badges.py --season 2026_2027  # autre saison
    python scripts/fetch_template_badges.py --dry-run           # sans rien ecrire
    python scripts/fetch_template_badges.py --yes               # sans confirmer

Un modele fraichement ecrit contient "Image": "" pour tout club dont
l'ecusson n'est pas encore sur le disque. Ce script, pour chacun d'eux :

    1. retrouve son identifiant API-Football en cherchant son nom
    2. telecharge l'ecusson depuis media.api-sports.io
    3. l'ecrit dans assets/images/clubs/<COMP>/<Club>_logo.png
    4. reecrit le champ "Image" du modele vers ce fichier

Pourquoi ce script et pas image_downloader_logos.py : celui-ci demande un
identifiant a la fois, tape a la main, et ne connait ni le modele ni le
nom du club. Ici on part du modele, on resout les identifiants tout seul
et on referme la boucle en reecrivant le fichier. La sortie est la meme
URL d'images, sans cle d'API -- seule la RECHERCHE de l'identifiant en
demande une.

Les identifiants trouves sont gardes dans data/reference/api_ids.json :
une deuxieme execution ne redepense pas de requetes pour les memes clubs.
Le quota du plan gratuit est de 100 requetes par jour, et il n'y a que
36 clubs par competition, mais un aller-retour rate reste un aller-retour
paye.
"""

import argparse
import json
import os
import sys
import time
import unicodedata
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = BASE_DIR / "templates"
CLUBS_DIR = BASE_DIR / "assets" / "images" / "clubs"
ID_CACHE = BASE_DIR / "data" / "reference" / "api_ids.json"

SEARCH_URL = "https://v3.football.api-sports.io/teams"
MEDIA_URL = "https://media.api-sports.io/football/teams/{id}.png"
PAUSE_S = 0.4                  # on ne martele pas l'API
DEFAULT_SEASON = "2025_2026"


# =====================================================================
#  LA CLE
# =====================================================================

def api_key():
    """Lit API_KEY dans .env, ou dans l'environnement.

    On ne depend pas de python-dotenv : trois lignes suffisent, et ce
    script doit pouvoir tourner sur une machine ou seuls requests et
    Pillow sont installes.
    """
    key = os.environ.get("API_KEY")
    if key:
        return key.strip()
    env = BASE_DIR / ".env"
    if env.is_file():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("API_KEY=") and not line.startswith("#"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


# =====================================================================
#  RETROUVER L'IDENTIFIANT
# =====================================================================

# Les lettres que NFKD ne casse PAS. Un "e accent aigu" est un "e" plus un
# accent, donc NFKD sait le separer ; un "o barre" danois est une lettre a
# part entiere, pas un "o" decore, et NFKD le laisse tel quel. Sans cette
# table, "Bodo Glimt" ne rencontrerait jamais "Bodo/Glimt" tel que l'API
# l'ecrit, et le club serait declare introuvable.
_LETTER_SWAPS = str.maketrans({
    "\u00f8": "o", "\u00d8": "o",      # o barre   Bodo/Glimt
    "\u00e6": "ae", "\u00c6": "ae",    # ae lie
    "\u00df": "ss",                     # eszett
    "\u0111": "d", "\u0110": "d",      # d barre   Zrinjski, Osijek
    "\u00f0": "d", "\u00d0": "d",      # eth       islandais
    "\u00fe": "th", "\u00de": "th",    # thorn     Breidablik
    "\u0142": "l", "\u0141": "l",      # l barre   Lodz, Bialystok
    "\u0131": "i", "\u0130": "i",      # i sans point / I avec point
    "\u0153": "oe", "\u0152": "oe",
})


def _flatten(text):
    """Minuscules, sans accents, sans ponctuation : pour comparer des noms.

    "Atletico Madrid" et "Atletico Madrid" doivent se rencontrer, sinon
    la moitie des clubs europeens ne se retrouvent jamais.

    La ponctuation devient une ESPACE, pas rien : "Bodo/Glimt" doit
    donner deux mots comme "Bodo Glimt", sinon les deux ecritures du meme
    club ne se ressemblent plus du tout.
    """
    text = str(text).translate(_LETTER_SWAPS)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = "".join(c if c.isalnum() else " " for c in text.lower())
    return " ".join(text.split())


def _score(candidate, wanted_name, wanted_country):
    """Note un candidat renvoye par l'API. Plus haut = meilleur.

    Le pays ne sert que de bonus, jamais de filtre : l'API ecrit
    "Turkey" la ou le modele ecrit "Türkiye", et "Czech-Republic" la ou
    il ecrit "Czechia". Filtrer la-dessus ecarterait de bons candidats
    pour une question d'orthographe.
    """
    name = _flatten(candidate.get("name"))
    want = _flatten(wanted_name)
    if name == want:
        points = 100
    elif name.startswith(want) or want.startswith(name):
        points = 70
    elif want in name or name in want:
        points = 45
    else:
        shared = set(want.split()) & set(name.split())
        points = 12 * len(shared)
    if _flatten(candidate.get("country")) == _flatten(wanted_country):
        points += 20
    return points


def resolve_id(session, club, country, auto):
    """Cherche le club et renvoie (id, nom_api) ou (None, raison)."""
    try:
        reply = session.get(SEARCH_URL, params={"search": club}, timeout=15)
    except requests.RequestException as exc:
        return None, f"network error: {exc}"
    if reply.status_code != 200:
        return None, f"HTTP {reply.status_code}"

    payload = reply.json()
    if payload.get("errors"):
        return None, f"api says: {payload['errors']}"
    teams = [row["team"] for row in payload.get("response", [])
             if row.get("team", {}).get("id")]
    if not teams:
        return None, "no match"

    ranked = sorted(teams, key=lambda t: _score(t, club, country), reverse=True)
    best = ranked[0]
    top = _score(best, club, country)

    # Un score franc, ou un ecart net avec le suivant : on prend. Sinon on
    # montre les candidats et on laisse choisir. Telecharger en silence
    # l'ecusson du mauvais club est la pire issue possible : le fichier a
    # le bon nom, il s'affiche sans erreur, et personne ne le remarque.
    runner_up = _score(ranked[1], club, country) if len(ranked) > 1 else 0
    if top >= 100 or (top >= 60 and top - runner_up >= 25) or auto:
        return best["id"], best["name"]

    print(f"    ambiguous, {len(ranked)} candidates:")
    for team in ranked[:5]:
        print(f"      [{team['id']:>6}] {team['name']} ({team.get('country')})"
              f"  score {_score(team, club, country)}")
    answer = input("    id to use (Enter to skip): ").strip()
    if answer.isdigit():
        chosen = next((t for t in ranked if str(t["id"]) == answer), None)
        return int(answer), chosen["name"] if chosen else "(typed by hand)"
    return None, "skipped"


# =====================================================================
#  TELECHARGER
# =====================================================================

def download(session, team_id, target):
    """Ecrit l'ecusson, ou rend une raison. Ne demande pas de cle."""
    try:
        reply = session.get(MEDIA_URL.format(id=team_id), timeout=20)
    except requests.RequestException as exc:
        return f"network error: {exc}"
    if reply.status_code != 200:
        return f"HTTP {reply.status_code}"
    if "image" not in reply.headers.get("Content-Type", ""):
        return "not an image"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(reply.content)
    return None


# =====================================================================
#  LE MODELE
# =====================================================================

def process(comp, season, session, cache, dry_run, auto):
    path = TEMPLATES_DIR / season / f"{comp}_{season}.json"
    if not path.is_file():
        print(f"{comp}: no {path.relative_to(BASE_DIR)}, skipped")
        return 0, 0

    doc = json.loads(path.read_text(encoding="utf-8"))
    todo = [(pot, club, body) for pot, clubs in doc.items()
            for club, body in clubs.items() if not body.get("Image")]
    if not todo:
        print(f"{comp}: every club already has a badge")
        return 0, 0

    print(f"\n{comp}: {len(todo)} badge(s) to fetch")
    done = failed = 0
    for _pot, club, body in todo:
        target = CLUBS_DIR / comp / f"{club}_logo.png"
        # Deux crans a remonter : le modele vit dans templates/<saison>/,
        # et un chemin relatif se resout depuis le dossier du fichier.
        relative = f"../../assets/images/clubs/{comp}/{club}_logo.png"

        # Deja sur le disque : on recoud juste le modele, sans requete.
        if target.is_file():
            print(f"  {club}: already on disk")
            if not dry_run:
                body["Image"] = relative
            done += 1
            continue

        key = f"{comp}|{club}"
        team_id = cache.get(key)
        if team_id is None:
            print(f"  {club}: searching...")
            team_id, label = resolve_id(session, club, body.get("Country", ""),
                                        auto)
            time.sleep(PAUSE_S)
            if team_id is None:
                print(f"    could not resolve ({label})")
                failed += 1
                continue
            print(f"    id {team_id} = {label}")
            cache[key] = team_id
        else:
            print(f"  {club}: id {team_id} (cached)")

        if dry_run:
            done += 1
            continue

        problem = download(session, team_id, target)
        time.sleep(PAUSE_S)
        if problem:
            print(f"    download failed: {problem}")
            failed += 1
            continue
        body["Image"] = relative
        print(f"    saved {target.relative_to(BASE_DIR)}")
        done += 1

    if not dry_run and done:
        path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
        print(f"  {path.name} rewritten")
    return done, failed


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("comps", nargs="*", default=None,
                        help="UCL, UEL, UECL. All three if omitted.")
    parser.add_argument("--dry-run", action="store_true",
                        help="resolve ids but write nothing")
    parser.add_argument("--season", default=DEFAULT_SEASON,
                        help=f"season folder under templates/ "
                             f"(default {DEFAULT_SEASON})")
    parser.add_argument("--yes", action="store_true",
                        help="take the best candidate without asking")
    args = parser.parse_args()

    comps = [c.upper() for c in args.comps] if args.comps else ["UCL", "UEL", "UECL"]

    key = api_key()
    if key is None:
        print("No API_KEY found. Put it in .env (see .env.example) or in the\n"
              "environment. The badge images themselves need no key, but\n"
              "looking up a club's id does.")
        return 1

    cache = {}
    if ID_CACHE.is_file():
        cache = json.loads(ID_CACHE.read_text(encoding="utf-8"))
    before = len(cache)

    session = requests.Session()
    session.headers.update({"x-apisports-key": key})

    total_done = total_failed = 0
    try:
        for comp in comps:
            done, failed = process(comp, args.season, session, cache,
                                   args.dry_run, args.yes)
            total_done += done
            total_failed += failed
    finally:
        # Meme si ca casse en route, les identifiants deja trouves sont
        # gardes : la reprise ne les repaiera pas.
        if len(cache) != before and not args.dry_run:
            ID_CACHE.parent.mkdir(parents=True, exist_ok=True)
            ID_CACHE.write_text(json.dumps(cache, indent=2, ensure_ascii=False),
                                encoding="utf-8")

    print(f"\n{total_done} done, {total_failed} failed.")
    if total_failed:
        print("For a club that would not resolve, download it by hand with\n"
              "image_downloader_logos.py and drop it in\n"
              "assets/images/clubs/<COMP>/<Club>_logo.png, then run this again.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
