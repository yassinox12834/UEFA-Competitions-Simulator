# Data handler

> These scripts download football data from the internet and turn it into tables the model can read.

## Where the data comes from: API-Football

The data comes from **API-Football** (made by the company api-sports), on its **free plan**, which limits how much data can be downloaded.

| | |
|---|---|
| Website | <https://www.api-football.com> |
| Documentation | <https://www.api-football.com/documentation-v3> |
| Prices | <https://www.api-football.com/pricing> |
| Account and API key | <https://dashboard.api-football.com> |

The limits of the free plan (October 2026):

- **100 requests per day.** One season needs 321 requests, so about 4 days.
- **A limit per minute too.** If you go over it, you can be blocked. So the scripts wait between requests.
- **Recent seasons only.** Older seasons need a paid plan (from 19 USD per month, 7 500 requests per day).

So the project has one season, 2024-25: 5 251 played matches. For rare events there are few cases: 92 extra times and 41 penalty shoot-outs.

## Run the scripts

1. **API key.** Copy `.env.example` to `.env` and write your key after `API_KEY=`. Never share it. `.env` is in `.gitignore`.
2. **Run from the `UEFA/` folder, as a module:** `python -m datahandler.fetch_team_ids`. Not `python datahandler/fetch_team_ids.py`: that fails with `ModuleNotFoundError`.
3. **The daily limit.** `fetch_fixtures.py` skips clubs already downloaded. On the free plan it stops at club 100: run it again the next day.

Order:

```bash
python -m datahandler.fetch_team_ids
python -m datahandler.fetch_fixtures
python -m datahandler.build_fixtures_csv
python -m datahandler.fetch_club_logos
python -m datahandler.fetch_competition_logos
python -m datahandler.build_team_seeds
```

Since version 1.1.0, step 3 also keeps one row per match and marks the finals as neutral, so `add_neutral_venue` and `drop_duplicate_fixtures` are no longer needed. They still work, in place, on an older `fixtures_25.csv`. Rebuilt from the raw files, step 3 gives back exactly the current `fixtures_25.csv` (5 328 rows).

## What each script does

| Script | What it does | Uses the API |
|---|---|---|
| `fetch_team_ids.py` | Gets the id of every club in the 3 competitions (Arsenal = 42). Writes `data/reference/UCL.json`, `UEL.json`, `UECL.json`. | yes |
| `fetch_fixtures.py` | Downloads all matches of each club, one file per club, in `data/raw/`. | yes |
| `build_fixtures_csv.py` | Puts all the raw files (season sub-folders included) in one table, one row per match, finals marked neutral: `fixtures_25.csv`. Writes nothing if it finds no match. | no |
| `add_neutral_venue.py` | Optional: marks finals as neutral in `fixtures_25.csv` itself. | no |
| `drop_duplicate_fixtures.py` | Optional: keeps one row per match in `fixtures_25.csv` itself. | no |
| `fetch_club_logos.py`, `fetch_competition_logos.py` | Download the badges and the competition logos. | no (images only) |
| `fetch_leagues.py` | Checks what the API covers for the Conference League. Not part of the steps above. | yes |
| `build_team_seeds.py` | Gives each club the starting Elo of its country. | no |

All paths are in `uefa/config.py`.

## The data

| Folder | What is inside | Rule |
|---|---|---|
| `data/raw/` | The API answers, as they came (JSON) | Never edit |
| `data/processed/` | Tables built from raw, like `fixtures_25.csv` | Can be rebuilt |
| `data/reference/` | Small lists checked by hand (`UCL.json`, `country_seeds.json`) | Back up first |

`fixtures_25.csv` has one row per match and 30 columns. Example: Atalanta 0-0 Arsenal (19 September 2024) is one row with `home_team` Atalanta, `away_team` Arsenal, `home_goals` 0, `away_goals` 0, `status` FT.

Three things to know:

- **Each match appears twice** in the raw files, once in each club's file. `build_fixtures_csv.py` keeps one row per `fixture_id`: 6 523 rows become 5 328.
- **`status`** tells how the match ended: `FT` = 90 minutes, `AET` = after extra time, `PEN` = after penalties, `CANC` = cancelled. Empty cells for extra time and penalties are normal.
- **After a shoot-out**, `home_goals` is the score before the penalties. Read `status` and `winner_home` / `winner_away` to find the winner.

## Known problems

- **The neutral rule is simple.** Every match called "Final" is marked neutral. That is wrong for the Emirates Cup final, and friendlies abroad are not marked.
- **The season (`2024`) is typed by hand** in 3 scripts.
- **No timeout** on the requests, and failed badge downloads say nothing.
- **Do not import the `fetch_` scripts.** Except `fetch_fixtures.py`, they run as soon as they are imported. The three `build`/`add`/`drop` scripts are safe to import since 1.1.0.

---
---

# Gestionnaire de données (version française)

> Ces scripts téléchargent des données de football sur internet et les transforment en tableaux que le modèle peut lire.

## D'où viennent les données : API-Football

Les données viennent d'**API-Football** (créé par l'entreprise api-sports), avec son **plan gratuit**, qui limite la quantité de données qu'on peut télécharger.

| | |
|---|---|
| Site web | <https://www.api-football.com> |
| Documentation | <https://www.api-football.com/documentation-v3> |
| Prix | <https://www.api-football.com/pricing> |
| Compte et clé d'API | <https://dashboard.api-football.com> |

Les limites du plan gratuit (octobre 2026) :

- **100 requêtes par jour.** Une saison demande 321 requêtes, donc environ 4 jours.
- **Une limite par minute aussi.** Si on la dépasse, on peut être bloqué. Les scripts attendent donc entre deux requêtes.
- **Seulement les saisons récentes.** Les saisons plus anciennes demandent un plan payant (à partir de 19 USD par mois, 7 500 requêtes par jour).

Le projet a donc une seule saison, 2024-25 : 5 251 matchs joués. Pour les événements rares, il y a peu de cas : 92 prolongations et 41 séances de tirs au but.

## Lancer les scripts

1. **Clé d'API.** Copiez `.env.example` en `.env` et écrivez votre clé après `API_KEY=`. Ne la partagez jamais. `.env` est dans `.gitignore`.
2. **Lancez depuis le dossier `UEFA/`, comme un module :** `python -m datahandler.fetch_team_ids`. Pas `python datahandler/fetch_team_ids.py` : ça échoue avec `ModuleNotFoundError`.
3. **La limite par jour.** `fetch_fixtures.py` saute les clubs déjà téléchargés. Avec le plan gratuit, il s'arrête au club 100 : relance-le le lendemain.

Ordre :

```bash
python -m datahandler.fetch_team_ids
python -m datahandler.fetch_fixtures
python -m datahandler.build_fixtures_csv
python -m datahandler.fetch_club_logos
python -m datahandler.fetch_competition_logos
python -m datahandler.build_team_seeds
```

Depuis la version 1.1.0, l'étape 3 garde aussi une seule ligne par match et marque les finales comme neutres : `add_neutral_venue` et `drop_duplicate_fixtures` ne sont plus nécessaires. Ils fonctionnent toujours, sur place, sur un ancien `fixtures_25.csv`. Reconstruit à partir des fichiers bruts, l'étape 3 redonne exactement le `fixtures_25.csv` actuel (5 328 lignes).

## Ce que fait chaque script

| Script | Ce qu'il fait | Utilise l'API |
|---|---|---|
| `fetch_team_ids.py` | Récupère l'identifiant de chaque club des 3 compétitions (Arsenal = 42). Écrit `data/reference/UCL.json`, `UEL.json`, `UECL.json`. | oui |
| `fetch_fixtures.py` | Télécharge tous les matchs de chaque club, un fichier par club, dans `data/raw/`. | oui |
| `build_fixtures_csv.py` | Met tous les fichiers bruts (sous-dossiers de saison compris) dans un seul tableau, une ligne par match, finales marquées neutres : `fixtures_25.csv`. N'écrit rien s'il ne trouve aucun match. | non |
| `add_neutral_venue.py` | Facultatif : marque les finales comme neutres dans `fixtures_25.csv` lui-même. | non |
| `drop_duplicate_fixtures.py` | Facultatif : garde une seule ligne par match dans `fixtures_25.csv` lui-même. | non |
| `fetch_club_logos.py`, `fetch_competition_logos.py` | Téléchargent les écussons et les logos des compétitions. | non (images seulement) |
| `fetch_leagues.py` | Vérifie ce que l'API couvre pour la Ligue Conférence. Ne fait pas partie des étapes ci-dessus. | oui |
| `build_team_seeds.py` | Donne à chaque club l'Elo de départ de son pays. | non |

Tous les chemins sont dans `uefa/config.py`.

## Les données

| Dossier | Ce qu'il contient | Règle |
|---|---|---|
| `data/raw/` | Les réponses de l'API, telles qu'elles sont arrivées (JSON) | Ne jamais modifier |
| `data/processed/` | Des tableaux construits à partir du brut, comme `fixtures_25.csv` | Peut être refait |
| `data/reference/` | De petites listes vérifiées à la main (`UCL.json`, `country_seeds.json`) | Sauvegarder d'abord |

`fixtures_25.csv` a une ligne par match et 30 colonnes. Exemple : Atalanta 0-0 Arsenal (19 septembre 2024) est une ligne avec `home_team` Atalanta, `away_team` Arsenal, `home_goals` 0, `away_goals` 0, `status` FT.

Trois choses à savoir :

- **Chaque match apparaît deux fois** dans les fichiers bruts, une fois dans le fichier de chaque club. `build_fixtures_csv.py` garde une ligne par `fixture_id` : 6 523 lignes deviennent 5 328.
- **`status`** dit comment le match s'est fini : `FT` = 90 minutes, `AET` = après prolongation, `PEN` = après tirs au but, `CANC` = annulé. Les cases vides pour la prolongation et les tirs au but sont normales.
- **Après une séance de tirs au but**, `home_goals` est le score avant les tirs au but. Lisez `status` et `winner_home` / `winner_away` pour trouver le vainqueur.

## Problèmes connus

- **La règle du terrain neutre est simple.** Tout match appelé « Final » est marqué neutre. C'est faux pour la finale de l'Emirates Cup, et les amicaux à l'étranger ne sont pas marqués.
- **La saison (`2024`) est écrite à la main** dans 3 scripts.
- **Pas de délai maximum** sur les requêtes, et les téléchargements d'écussons qui échouent ne disent rien.
- **N'importez pas les scripts `fetch_`.** Sauf `fetch_fixtures.py`, ils s'exécutent dès qu'on les importe. Les trois scripts `build`/`add`/`drop` peuvent être importés sans risque depuis la 1.1.0.

---
