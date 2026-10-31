# `elo_score_updating.py`, line by line

> This page walks through the code that computes the Elo ratings. For the idea (expected score, surprise, $K$), read [`../elo.md`](../elo.md) first.

*Version française : [plus bas](#elo_score_updatingpy-ligne-par-ligne).*

## How to read this page

- Each function starts with its **arguments**: what comes in, and its type.
- The code comes in groups of 2 to 4 lines, each followed by bullets: what the lines do, why, and which general idea they are an example of.
- Each function ends with **In one line**.
- The small loading helpers (`load_seed`, `load_country_seeds`, `load_k_settings`) and the `report` function only read files or print text; they are summed up in a table instead of traced.

---

## The imports

```python
import csv
import json
import sys
from pathlib import Path
```

- `csv` (comes with Python) reads the table of competition weights, row by row, in `load_coef_table`.
- `json` (comes with Python) reads the starting ratings and settings, and writes the final ratings.
- `sys` (comes with Python) gives `sys.argv`, the words typed after the command, to check for `--write`.
- `Path` (from `pathlib`, comes with Python) builds file paths with `/`, which work on every operating system.

```python
import numpy as np
import pandas as pd
```

- `pandas` (installed with `pip`) holds the 5 328 matches as a table (a `DataFrame`), sorts them by date and writes the output CSV.
- `numpy` (installed with `pip`) gives `np.sign`, which turns a goal difference into +1, 0 or −1, and `np.nan`, the "no value" marker for matches not played yet.
- Because these two are imported at the top, any file that imports this one also needs pandas and numpy. That is a known problem for the simulation (see [`../match_engine.md`](../match_engine.md)).

---

## The settings

```python
BASE_DIR = Path(__file__).resolve().parents[1]
FIXTURES_CSV = BASE_DIR / "data" / "processed" / "fixtures_25.csv"
OUT_JSON     = BASE_DIR / "data" / "processed" / "eeelo_final.json"
```

- `Path(__file__)` is the path of this very file; `.resolve()` makes it complete, and `.parents[1]` goes up two folders, from `model/elo_score_updating.py` to the project folder.
- Every other path is built from `BASE_DIR`, so the script works wherever it is launched from. A plain `"data/..."` would only work when launched from the project folder.
- The same pattern defines all the input and output files (seven paths in total).

| Code | Does | Example value |
|---|---|---|
| `GOAL_COLUMN_CANDIDATES` | five possible names for the goal columns | `("home_goals", "away_goals")` |
| `COUNTRY_ALIASES` | fixes country names spelt differently in two files | `"Turkey": "Türkiye"` |
| `NON_DOMESTIC_COUNTRY = "World"` | what the data writes as the country of a European or friendly match | `"World"` |
| `DEFAULT_ELO = 1450.0` | starting rating of a club whose country is unknown | `1450.0` |

---

## `expected_score(R_A, R_B)`: the expected score

**Arguments:** `R_A`: `float`, the rating of the club we ask about. `R_B`: `float`, the rating of its opponent.

```python
def expected_score(R_A, R_B):
    return 1 / (1 + 10 ** ((R_B - R_A) / 400))
```

- Computes the formula of [`../elo.md`](../elo.md), section 3: `**` is "to the power of", so `10 ** 0.5` is about 3.16.
- `expected_score(1787.88, 1720.12)`: `(R_B - R_A) / 400 = -0.1694`, `10 ** -0.1694 = 0.677`, result `1 / 1.677 = 0.596`.
- It is a **pure function**: same inputs, same output, and it changes nothing outside itself. That makes it easy to test and safe to reuse; `match_engine.py` and `knockout.py` import it.

**In one line:** takes two ratings and returns the share of the point the first club should take, between 0 and 1.

---

## `update_rating(R_A, K, S_A, E_A)`: one Elo step

**Arguments:** `R_A`: `float`, rating before the match. `K`: `float`, the step size. `S_A`: `float`, the actual result (1, 0.5 or 0). `E_A`: `float`, the expected score.

```python
def update_rating(R_A, K, S_A, E_A):
    return R_A + K * (S_A - E_A)
```

- Adds `K` times the surprise to the old rating. `update_rating(1787.88, 24, 1.0, 0.596) = 1787.88 + 24 × 0.404 = 1797.57`.
- It takes the expected score as an argument instead of computing it. So the expected score is computed once and reused: the simulation writes it in its log, and gives the away side `1 - E` so the two changes cancel exactly.
- Also a pure function, so a test can give it any expected score and check the update on its own.

**In one line:** takes a rating, a step size, a result and an expected score, and returns the new rating.

---

## `result_scores(home_goals, away_goals)`: goals to results

**Arguments:** `home_goals`, `away_goals`: numbers, the goals of each side.

```python
    if home_goals > away_goals:
        return 1.0, 0.0
    if home_goals < away_goals:
        return 0.0, 1.0
    return 0.5, 0.5
```

- Returns a pair (a **tuple**) of results, home first: `(2, 0) -> (1.0, 0.0)`, `(1, 1) -> (0.5, 0.5)`.
- Always returns decimal numbers (`1.0`, not `1`), so every result has the same type.
- A trap: a missing score (`NaN`, "not a number") is neither bigger nor smaller than anything, so it would fall to the last line and count as a draw. It is safe only because `run` checks that a match was played before calling this function.

**In one line:** takes a score and returns the Elo result of each side.

---

## `season_from_date(date)`: which season?

**Arguments:** `date`: a date (`datetime` or pandas `Timestamp`).

```python
def season_from_date(date):
    return date.year if date.month >= 7 else date.year - 1
```

- A **conditional expression** (`a if test else b`) on one line. A match in July to December belongs to the season that started that year; January to June belongs to the season that started the year before.
- `2024-09-15 -> 2024`, `2025-03-02 -> 2024`.
- It assumes every league plays from August to May. Leagues that play from spring to autumn (Norway, Sweden, Finland, Ireland) get the wrong season.

**In one line:** takes a date and returns the year its season started.

---

## Small loading helpers

| Function | Does |
|---|---|
| `load_seed(path)` | reads a JSON file `{club: rating}` and makes every rating a `float` |
| `load_country_seeds(path)` | the same, for `{country: rating}` |
| `load_k_settings(path)` | reads `coefs.json` and returns `(k_base, k_max)`, here `(20, 30)` |

`load_seed` opens files with `encoding="utf-8-sig"`: files saved by Excel or some Windows tools start with three invisible bytes (a "BOM"), and `utf-8-sig` removes them so the first name is not broken.

---

## `load_coef_table(path)`: the competition weights

**Arguments:** `path`: `Path`, where `coef_table.csv` is.

```python
    table = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for line in csv.DictReader(fh):
```

- `with open(...) as fh` opens the file and closes it automatically at the end of the block, even after an error: this is a **context manager**.
- `csv.DictReader` reads each row as a dictionary whose keys are the column names, so the code can write `line["league"]` instead of remembering that the league is column 3.
- `newline=""` is what the `csv` module asks for, so line breaks inside cells are read correctly.

```python
            table[(line["league"], line["round"])] = (
                float(line["comp_mult"]),
                float(line["stage_mult"]),
            )
    return table
```

- The key is a **tuple** of two texts, `(league, round)`. A tuple can be a dictionary key (a list cannot), which allows a lookup on two values at once.
- `table[("UEFA Champions League", "Quarter-finals")] -> (1.2, 1.08)`.
- `float(...)` turns the text read from the file into a number; a CSV file only contains text.

**In one line:** turns the 1 370-row CSV into a dictionary from `(league, round)` to the two weights.

---

## `build_club_country(df)`: each club's country

**Arguments:** `df`: a pandas `DataFrame` of all the matches.

```python
    domestic = df[df["country"] != NON_DOMESTIC_COUNTRY]
    club_country = {}
```

- `df["country"] != "World"` gives a column of `True`/`False`; putting it inside `df[...]` keeps only the rows where it is `True`. This is called **boolean filtering**.
- European and friendly matches are removed because their country is "World", which says nothing about the clubs.

```python
    for home, away, country in zip(domestic["home_team"], domestic["away_team"],
                                   domestic["country"]):
        canonical = COUNTRY_ALIASES.get(country, country)
        club_country.setdefault(home, canonical)
        club_country.setdefault(away, canonical)
    return club_country
```

- `zip` walks through three columns side by side, giving one `(home, away, country)` triple per match. It is much faster than `df.iterrows()`.
- `COUNTRY_ALIASES.get(country, country)` fixes a spelling if it is in the list, and keeps the name as it is otherwise (the second argument is the default).
- `setdefault` writes a club's country only the first time the club is seen: the **first occurrence wins**. `club_country: {} -> {"Liverpool": "England", "Everton": "England", ...}`.

**In one line:** takes all matches and returns a dictionary from club to country, read from domestic matches only.

---

## `load_clubs(df, country_seeds)`: starting ratings for everyone

**Arguments:** `df`: `DataFrame` of the matches. `country_seeds`: `dict`, country to starting rating.

```python
    club_country = build_club_country(df)
    all_clubs = set(df["home_team"]) | set(df["away_team"])
    provisional, no_country = {}, set()
```

- `set(...) | set(...)` is the **union** of two sets: every club that appears at home or away, each once.
- Two accumulators are prepared at once: a dictionary of starting ratings and a set of clubs with no known country.

```python
    for club in all_clubs:
        country = club_country.get(club)
        if country in country_seeds:
            provisional[club] = country_seeds[country]
        else:
            provisional[club] = DEFAULT_ELO
            no_country.add(club)
    return provisional, no_country
```

- For each club, look up its country (or `None`), then that country's starting value. `"Liverpool" -> "England" -> 1669.46`.
- A club whose country is unknown (`None` is never in `country_seeds`) gets 1450 and is added to `no_country`, so the report can list the clubs rated on a guess.
- Returning two values at once (a tuple) lets the caller write `provisional, no_country = load_clubs(...)`.

**In one line:** takes the matches and the country values, and returns every club's starting rating plus the list of clubs that fell back to 1450.

---

## `run(write=True)`: the whole computation

**Arguments:** `write`: `bool`, also save `eeelo_final.json` if `True`.

```python
    file = load_seed(JSON_TEAMS_SEED)
    k_base, k_max = load_k_settings(JSON_COEFS)
    coef_table = load_coef_table(CSV_COEF_TABLE)
```

- Loads the three settings files. `file` holds the starting ratings written by hand for some clubs.
- `k_base, k_max = ...` unpacks the returned pair: `k_base = 20`, `k_max = 30`.

```python
    df = pd.read_csv(FIXTURES_CSV)
    home_goals_col, away_goals_col = find_goal_columns(df)
    df["date"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)
    df["season"] = df["date"].apply(season_from_date)
```

- `pd.read_csv` (pandas) loads the whole CSV into a `DataFrame` of 5 328 rows.
- `find_goal_columns` tries the five candidate column names and returns the first pair present (`"home_goals"`, `"away_goals"`), or raises a clear error listing the real columns.
- `pd.to_datetime(..., unit="s")` turns a timestamp (seconds since 1 January 1970) into a real date: `1726426800 -> 2024-09-15 19:00 UTC`.
- `.apply(season_from_date)` calls the function on every date of the column and stores the results in a new `season` column.

```python
    teams_games = df.sort_values("timestamp").reset_index(drop=True)
    country_seeds = load_country_seeds(JSON_COUNTRY_SEED)
    provisional, no_country_clubs = load_clubs(df, country_seeds)
```

- Sorts the matches by date: the update of each match must use the ratings left by the matches before it, and the saved "rating before" rows must not contain future results (see [`../elo.md`](../elo.md), section 7).
- `reset_index(drop=True)` renumbers the rows 0, 1, 2, ... after the sort and throws away the old numbers.
- Then every club gets its starting rating.

```python
    elos = {**provisional, **file}
    elos_at_start = dict(elos)
```

- `{**a, **b}` merges two dictionaries into a new one; when a club is in both, the value from `b` (the one written second) wins. So a hand-written starting rating beats the country guess.
- `dict(elos)` makes a **copy**. Without it, `elos_at_start` would just be a second name for the same dictionary, it would change during the loop, and the report's "biggest risers" would all show 0.

```python
    for _, row in teams_games.iterrows():
        home_elo = elos.get(row["home_team"])
        away_elo = elos.get(row["away_team"])
```

- `iterrows()` gives the matches one by one; `_` is the row number, which is not needed (the underscore says "ignored").
- `.get` returns the current rating, or `None` if the club is unknown. After `load_clubs`, every club is known, so the `None` branch that follows (it counts and skips the match) never runs today; it stays as a loud warning in case the data changes.
- `iterrows` is slow compared with other pandas tools, but here each match depends on the one before, so the loop cannot be replaced by one big table operation anyway.

```python
        home_goals, away_goals = row[home_goals_col], row[away_goals_col]
        played = not (pd.isna(home_goals) or pd.isna(away_goals))
        is_home = 0 if (has_neutral and bool(row["neutral_venue"])) else 1
```

- `pd.isna` is `True` for a missing value; a match is `played` only if both goal values exist.
- `is_home` is meant to be 1 for a normal match and 0 at a neutral ground. **Bug:** the `neutral_venue` column is empty (`NaN`) on most rows, and `bool(NaN)` is `True` in Python, so `is_home` ends up 0 on every row.

```python
        training_rows.append({
            "elo_home_before": home_elo,
            "elo_away_before": away_elo,
            "target": (np.sign(home_goals - away_goals) if played else np.nan),
            ...
        })
```

- Saves one row per match, with both ratings **before** the update, plus the result: `np.sign(2 - 0) = 1` (home win), `np.sign(1 - 1) = 0` (draw), `np.sign(0 - 3) = -1` (away win).
- It is saved before checking whether the match changes ratings, so unplayed matches get a row too (with `target = NaN`) and can be predicted later.
- Side effect: friendlies also get a row, so the match model is trained on them, although they do not change ratings (a known bug).

```python
        if not played:
            counts["not_played"] += 1
            continue
        key = (row["league"], row["round"])
        if key not in coef_table:
```

- `continue` jumps straight to the next match. Each reason to skip a match has its own counter, so the report can check that every match is counted somewhere.
- `key` is the `(league, round)` pair used to find the weights; a missing pair is counted and skipped.

```python
        comp_mult, stage_mult = coef_table[key]
        K = min(k_base * comp_mult * stage_mult, k_max)
        if K == 0:
            counts["zero_k"] += 1
            continue
```

- The $K$ of [`../elo.md`](../elo.md), section 5, with a ceiling: `min(20 × 1.2 × 1.08, 30) = min(25.92, 30) = 25.92`.
- Friendlies have a weight of 0, so $K = 0$ and they are skipped: they would not change anything anyway.

```python
        e_home = expected_score(home_elo, away_elo)
        e_away = expected_score(away_elo, home_elo)
        s_home, s_away = result_scores(home_goals, away_goals)
```

- The two expected scores (they add up to 1) and the two results.
- Arsenal 2-0 Atalanta: `e_home = 0.596`, `e_away = 0.404`, `s_home, s_away = 1.0, 0.0`.

```python
        elos[row["home_team"]] = update_rating(home_elo, K, s_home, e_home)
        elos[row["away_team"]] = update_rating(away_elo, K, s_away, e_away)
        counts["played"] += 1
```

- Both ratings are updated in place in `elos`: `elos["Arsenal"]: 1787.88 -> 1797.57`, `elos["Atalanta"]: 1720.12 -> 1710.43`.
- Both updates use the ratings from **before** the match (`home_elo`, `away_elo`), not the freshly updated one, so the order of the two lines does not matter.

```python
    features_df = pd.DataFrame(training_rows)
    features_df.to_csv(OUT_FEATURES_CSV, index=False)
    if write:
        with open(OUT_JSON, "w", encoding="utf-8") as fh:
            json.dump({c: round(r, 2) for c, r in sorted(elos.items())}, fh, indent=2, ensure_ascii=False)
```

- The list of row dictionaries becomes a table and is written as `match_features.csv`. This happens on every run, even without `--write` (a known bug).
- With `--write`, the final ratings are written as JSON: sorted by club name, rounded to 2 decimals, `indent=2` for a readable file, and `ensure_ascii=False` so "München" stays "München" instead of `"München"`.

**In one line:** reads the matches and settings, plays every real match in date order through the Elo update, and writes the final ratings and one feature row per match.

---

## The last lines

```python
if __name__ == "__main__":
    run(write="--write" in sys.argv)
```

- This block only runs when the file is started directly (`python -m model.elo_score_updating`), not when another file imports it.
- `"--write" in sys.argv` is `True` if the user typed `--write` after the command.

---
---

# `elo_score_updating.py`, ligne par ligne

> Cette page explique le code qui calcule les notes Elo. Pour l'idée (score attendu, surprise, $K$), lisez d'abord [`../elo.md`](../elo.md#les-notes-elo--un-nombre-pour-la-force-de-chaque-club).

## Comment lire cette page

- Chaque fonction commence par ses **arguments** : ce qui entre, et son type.
- Le code vient en groupes de 2 à 4 lignes, chacun suivi de points : ce que font les lignes, pourquoi, et de quelle idée générale elles sont un exemple.
- Chaque fonction se termine par **En une ligne**.
- Les petites fonctions de chargement (`load_seed`, `load_country_seeds`, `load_k_settings`) et la fonction `report` ne font que lire des fichiers ou afficher du texte ; elles sont résumées dans un tableau au lieu d'être détaillées.

---

## Les imports

```python
import csv
import json
import sys
from pathlib import Path
```

- `csv` (fourni avec Python) lit le tableau des poids des compétitions, ligne par ligne, dans `load_coef_table`.
- `json` (fourni avec Python) lit les notes de départ et les réglages, et écrit les notes finales.
- `sys` (fourni avec Python) donne `sys.argv`, les mots tapés après la commande, pour chercher `--write`.
- `Path` (de `pathlib`, fourni avec Python) construit des chemins de fichiers avec `/`, qui marchent sur tous les systèmes.

```python
import numpy as np
import pandas as pd
```

- `pandas` (installé avec `pip`) garde les 5 328 matchs sous forme de tableau (un `DataFrame`), les trie par date et écrit le CSV de sortie.
- `numpy` (installé avec `pip`) donne `np.sign`, qui transforme une différence de buts en +1, 0 ou −1, et `np.nan`, le marqueur « pas de valeur » des matchs pas encore joués.
- Comme ces deux modules sont importés en haut, tout fichier qui importe celui-ci a aussi besoin de pandas et numpy. C'est un problème connu pour la simulation (voir [`../match_engine.md`](../match_engine.md)).

---

## Les réglages

```python
BASE_DIR = Path(__file__).resolve().parents[1]
FIXTURES_CSV = BASE_DIR / "data" / "processed" / "fixtures_25.csv"
OUT_JSON     = BASE_DIR / "data" / "processed" / "eeelo_final.json"
```

- `Path(__file__)` est le chemin de ce fichier même ; `.resolve()` le rend complet, et `.parents[1]` remonte de deux dossiers, de `model/elo_score_updating.py` jusqu'au dossier du projet.
- Tous les autres chemins sont construits à partir de `BASE_DIR`, donc le script marche d'où qu'on le lance. Un simple `"data/..."` ne marcherait que lancé depuis le dossier du projet.
- Le même schéma définit tous les fichiers d'entrée et de sortie (sept chemins au total).

| Code | Fait | Exemple |
|---|---|---|
| `GOAL_COLUMN_CANDIDATES` | cinq noms possibles pour les colonnes de buts | `("home_goals", "away_goals")` |
| `COUNTRY_ALIASES` | corrige les noms de pays écrits différemment dans deux fichiers | `"Turkey": "Türkiye"` |
| `NON_DOMESTIC_COUNTRY = "World"` | ce que les données écrivent comme pays d'un match européen ou amical | `"World"` |
| `DEFAULT_ELO = 1450.0` | note de départ d'un club dont le pays est inconnu | `1450.0` |

---

## `expected_score(R_A, R_B)` : le score attendu

**Arguments :** `R_A` : `float`, la note du club dont on parle. `R_B` : `float`, la note de son adversaire.

```python
def expected_score(R_A, R_B):
    return 1 / (1 + 10 ** ((R_B - R_A) / 400))
```

- Calcule la formule de [`../elo.md`](../elo.md), section 3 : `**` veut dire « puissance », donc `10 ** 0.5` vaut environ 3.16.
- `expected_score(1787.88, 1720.12)` : `(R_B - R_A) / 400 = -0.1694`, `10 ** -0.1694 = 0.677`, résultat `1 / 1.677 = 0.596`.
- C'est une **fonction pure** : mêmes entrées, même sortie, et elle ne change rien en dehors d'elle. Elle est donc facile à tester et sûre à réutiliser ; `match_engine.py` et `knockout.py` l'importent.

**En une ligne :** prend deux notes et renvoie la part du point que le premier club devrait prendre, entre 0 et 1.

---

## `update_rating(R_A, K, S_A, E_A)` : un pas d'Elo

**Arguments :** `R_A` : `float`, la note avant le match. `K` : `float`, la taille du pas. `S_A` : `float`, le résultat réel (1, 0.5 ou 0). `E_A` : `float`, le score attendu.

```python
def update_rating(R_A, K, S_A, E_A):
    return R_A + K * (S_A - E_A)
```

- Ajoute `K` fois la surprise à l'ancienne note. `update_rating(1787.88, 24, 1.0, 0.596) = 1787.88 + 24 × 0.404 = 1797.57`.
- Elle reçoit le score attendu en argument au lieu de le calculer. Le score attendu est donc calculé une fois et réutilisé : la simulation l'écrit dans son journal, et donne `1 - E` à l'équipe à l'extérieur pour que les deux changements s'annulent exactement.
- C'est aussi une fonction pure, donc un test peut lui donner n'importe quel score attendu et vérifier la mise à jour seule.

**En une ligne :** prend une note, une taille de pas, un résultat et un score attendu, et renvoie la nouvelle note.

---

## `result_scores(home_goals, away_goals)` : des buts aux résultats

**Arguments :** `home_goals`, `away_goals` : des nombres, les buts de chaque camp.

```python
    if home_goals > away_goals:
        return 1.0, 0.0
    if home_goals < away_goals:
        return 0.0, 1.0
    return 0.5, 0.5
```

- Renvoie une paire (un **tuple**) de résultats, domicile d'abord : `(2, 0) -> (1.0, 0.0)`, `(1, 1) -> (0.5, 0.5)`.
- Renvoie toujours des nombres décimaux (`1.0`, pas `1`), pour que chaque résultat ait le même type.
- Un piège : un score manquant (`NaN`, « pas un nombre ») n'est ni plus grand ni plus petit que rien, donc il tomberait sur la dernière ligne et compterait comme un nul. C'est sans danger seulement parce que `run` vérifie qu'un match a été joué avant d'appeler cette fonction.

**En une ligne :** prend un score et renvoie le résultat Elo de chaque camp.

---

## `season_from_date(date)` : quelle saison ?

**Arguments :** `date` : une date (`datetime` ou `Timestamp` de pandas).

```python
def season_from_date(date):
    return date.year if date.month >= 7 else date.year - 1
```

- Une **expression conditionnelle** (`a if test else b`) sur une ligne. Un match de juillet à décembre appartient à la saison qui a commencé cette année-là ; de janvier à juin, à la saison qui a commencé l'année d'avant.
- `2024-09-15 -> 2024`, `2025-03-02 -> 2024`.
- Elle suppose que tous les championnats se jouent d'août à mai. Les championnats qui se jouent du printemps à l'automne (Norvège, Suède, Finlande, Irlande) reçoivent la mauvaise saison.

**En une ligne :** prend une date et renvoie l'année où sa saison a commencé.

---

## Petites fonctions de chargement

| Fonction | Fait |
|---|---|
| `load_seed(path)` | lit un fichier JSON `{club: note}` et transforme chaque note en `float` |
| `load_country_seeds(path)` | pareil, pour `{pays: note}` |
| `load_k_settings(path)` | lit `coefs.json` et renvoie `(k_base, k_max)`, ici `(20, 30)` |

`load_seed` ouvre les fichiers avec `encoding="utf-8-sig"` : les fichiers enregistrés par Excel ou certains outils Windows commencent par trois octets invisibles (un « BOM »), et `utf-8-sig` les enlève pour que le premier nom ne soit pas abîmé.

---

## `load_coef_table(path)` : les poids des compétitions

**Arguments :** `path` : `Path`, l'endroit où se trouve `coef_table.csv`.

```python
    table = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for line in csv.DictReader(fh):
```

- `with open(...) as fh` ouvre le fichier et le ferme tout seul à la fin du bloc, même après une erreur : c'est un **gestionnaire de contexte**.
- `csv.DictReader` lit chaque ligne comme un dictionnaire dont les clés sont les noms des colonnes, donc le code peut écrire `line["league"]` au lieu de se souvenir que le championnat est la colonne 3.
- `newline=""` est ce que demande le module `csv`, pour que les retours à la ligne dans les cellules soient bien lus.

```python
            table[(line["league"], line["round"])] = (
                float(line["comp_mult"]),
                float(line["stage_mult"]),
            )
    return table
```

- La clé est un **tuple** de deux textes, `(championnat, tour)`. Un tuple peut servir de clé de dictionnaire (une liste non), ce qui permet de chercher sur deux valeurs à la fois.
- `table[("UEFA Champions League", "Quarter-finals")] -> (1.2, 1.08)`.
- `float(...)` transforme le texte lu dans le fichier en nombre ; un fichier CSV ne contient que du texte.

**En une ligne :** transforme le CSV de 1 370 lignes en dictionnaire de `(championnat, tour)` vers les deux poids.

---

## `build_club_country(df)` : le pays de chaque club

**Arguments :** `df` : un `DataFrame` pandas de tous les matchs.

```python
    domestic = df[df["country"] != NON_DOMESTIC_COUNTRY]
    club_country = {}
```

- `df["country"] != "World"` donne une colonne de `True`/`False` ; la mettre dans `df[...]` ne garde que les lignes où elle vaut `True`. On appelle cela un **filtrage booléen**.
- Les matchs européens et amicaux sont retirés car leur pays est « World », ce qui ne dit rien des clubs.

```python
    for home, away, country in zip(domestic["home_team"], domestic["away_team"],
                                   domestic["country"]):
        canonical = COUNTRY_ALIASES.get(country, country)
        club_country.setdefault(home, canonical)
        club_country.setdefault(away, canonical)
    return club_country
```

- `zip` parcourt trois colonnes côte à côte, en donnant un trio `(domicile, extérieur, pays)` par match. C'est bien plus rapide que `df.iterrows()`.
- `COUNTRY_ALIASES.get(country, country)` corrige une orthographe si elle est dans la liste, et garde le nom tel quel sinon (le deuxième argument est la valeur par défaut).
- `setdefault` n'écrit le pays d'un club que la première fois qu'on voit ce club : **la première apparition gagne**. `club_country : {} -> {"Liverpool": "England", "Everton": "England", ...}`.

**En une ligne :** prend tous les matchs et renvoie un dictionnaire de club vers pays, lu seulement dans les matchs nationaux.

---

## `load_clubs(df, country_seeds)` : notes de départ pour tout le monde

**Arguments :** `df` : `DataFrame` des matchs. `country_seeds` : `dict`, pays vers note de départ.

```python
    club_country = build_club_country(df)
    all_clubs = set(df["home_team"]) | set(df["away_team"])
    provisional, no_country = {}, set()
```

- `set(...) | set(...)` est l'**union** de deux ensembles : chaque club qui apparaît à domicile ou à l'extérieur, une seule fois.
- Deux accumulateurs sont préparés d'un coup : un dictionnaire des notes de départ et un ensemble des clubs sans pays connu.

```python
    for club in all_clubs:
        country = club_country.get(club)
        if country in country_seeds:
            provisional[club] = country_seeds[country]
        else:
            provisional[club] = DEFAULT_ELO
            no_country.add(club)
    return provisional, no_country
```

- Pour chaque club, chercher son pays (ou `None`), puis la valeur de départ de ce pays. `"Liverpool" -> "England" -> 1669.46`.
- Un club dont le pays est inconnu (`None` n'est jamais dans `country_seeds`) reçoit 1450 et est ajouté à `no_country`, pour que le rapport puisse lister les clubs notés sur une supposition.
- Renvoyer deux valeurs d'un coup (un tuple) permet à l'appelant d'écrire `provisional, no_country = load_clubs(...)`.

**En une ligne :** prend les matchs et les valeurs des pays, et renvoie la note de départ de chaque club ainsi que la liste des clubs qui sont tombés à 1450.

---

## `run(write=True)` : tout le calcul

**Arguments :** `write` : `bool`, enregistrer aussi `eeelo_final.json` si `True`.

```python
    file = load_seed(JSON_TEAMS_SEED)
    k_base, k_max = load_k_settings(JSON_COEFS)
    coef_table = load_coef_table(CSV_COEF_TABLE)
```

- Charge les trois fichiers de réglages. `file` contient les notes de départ écrites à la main pour certains clubs.
- `k_base, k_max = ...` déballe la paire renvoyée : `k_base = 20`, `k_max = 30`.

```python
    df = pd.read_csv(FIXTURES_CSV)
    home_goals_col, away_goals_col = find_goal_columns(df)
    df["date"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)
    df["season"] = df["date"].apply(season_from_date)
```

- `pd.read_csv` (pandas) charge tout le CSV dans un `DataFrame` de 5 328 lignes.
- `find_goal_columns` essaie les cinq noms de colonnes possibles et renvoie la première paire présente (`"home_goals"`, `"away_goals"`), ou une erreur claire qui liste les vraies colonnes.
- `pd.to_datetime(..., unit="s")` transforme un horodatage (secondes depuis le 1er janvier 1970) en vraie date : `1726426800 -> 2024-09-15 19:00 UTC`.
- `.apply(season_from_date)` appelle la fonction sur chaque date de la colonne et range les résultats dans une nouvelle colonne `season`.

```python
    teams_games = df.sort_values("timestamp").reset_index(drop=True)
    country_seeds = load_country_seeds(JSON_COUNTRY_SEED)
    provisional, no_country_clubs = load_clubs(df, country_seeds)
```

- Trie les matchs par date : la mise à jour de chaque match doit utiliser les notes laissées par les matchs d'avant, et les lignes « note avant » enregistrées ne doivent pas contenir de résultats futurs (voir [`../elo.md`](../elo.md), section 7).
- `reset_index(drop=True)` renumérote les lignes 0, 1, 2, ... après le tri et jette les anciens numéros.
- Ensuite, chaque club reçoit sa note de départ.

```python
    elos = {**provisional, **file}
    elos_at_start = dict(elos)
```

- `{**a, **b}` fusionne deux dictionnaires en un nouveau ; quand un club est dans les deux, la valeur de `b` (écrit en second) gagne. Une note de départ écrite à la main l'emporte donc sur la supposition par pays.
- `dict(elos)` fait une **copie**. Sans elle, `elos_at_start` serait juste un deuxième nom pour le même dictionnaire, il changerait pendant la boucle, et les « plus fortes hausses » du rapport afficheraient toutes 0.

```python
    for _, row in teams_games.iterrows():
        home_elo = elos.get(row["home_team"])
        away_elo = elos.get(row["away_team"])
```

- `iterrows()` donne les matchs un par un ; `_` est le numéro de ligne, dont on n'a pas besoin (le tiret bas veut dire « ignoré »).
- `.get` renvoie la note actuelle, ou `None` si le club est inconnu. Après `load_clubs`, chaque club est connu, donc la branche `None` qui suit (elle compte le match et le saute) ne sert jamais aujourd'hui ; elle reste comme alerte au cas où les données changeraient.
- `iterrows` est lent comparé à d'autres outils de pandas, mais ici chaque match dépend du précédent, donc la boucle ne peut de toute façon pas être remplacée par une seule grosse opération sur le tableau.

```python
        home_goals, away_goals = row[home_goals_col], row[away_goals_col]
        played = not (pd.isna(home_goals) or pd.isna(away_goals))
        is_home = 0 if (has_neutral and bool(row["neutral_venue"])) else 1
```

- `pd.isna` vaut `True` pour une valeur manquante ; un match n'est `played` (joué) que si les deux valeurs de buts existent.
- `is_home` devrait valoir 1 pour un match normal et 0 sur terrain neutre. **Bug :** la colonne `neutral_venue` est vide (`NaN`) sur la plupart des lignes, et `bool(NaN)` vaut `True` en Python, donc `is_home` finit à 0 sur toutes les lignes.

```python
        training_rows.append({
            "elo_home_before": home_elo,
            "elo_away_before": away_elo,
            "target": (np.sign(home_goals - away_goals) if played else np.nan),
            ...
        })
```

- Enregistre une ligne par match, avec les deux notes **avant** la mise à jour, et le résultat : `np.sign(2 - 0) = 1` (victoire à domicile), `np.sign(1 - 1) = 0` (nul), `np.sign(0 - 3) = -1` (victoire à l'extérieur).
- Elle est enregistrée avant de vérifier si le match change les notes, donc les matchs pas encore joués ont aussi une ligne (avec `target = NaN`) et pourront être prédits plus tard.
- Effet secondaire : les amicaux ont aussi une ligne, donc le modèle de match apprend à partir d'eux, alors qu'ils ne changent pas les notes (un bug connu).

```python
        if not played:
            counts["not_played"] += 1
            continue
        key = (row["league"], row["round"])
        if key not in coef_table:
```

- `continue` passe directement au match suivant. Chaque raison de sauter un match a son propre compteur, pour que le rapport puisse vérifier que chaque match est compté quelque part.
- `key` est la paire `(championnat, tour)` qui sert à trouver les poids ; une paire absente est comptée et sautée.

```python
        comp_mult, stage_mult = coef_table[key]
        K = min(k_base * comp_mult * stage_mult, k_max)
        if K == 0:
            counts["zero_k"] += 1
            continue
```

- Le $K$ de [`../elo.md`](../elo.md), section 5, avec un plafond : `min(20 × 1.2 × 1.08, 30) = min(25.92, 30) = 25.92`.
- Les amicaux ont un poids de 0, donc $K = 0$ et ils sont sautés : ils ne changeraient rien de toute façon.

```python
        e_home = expected_score(home_elo, away_elo)
        e_away = expected_score(away_elo, home_elo)
        s_home, s_away = result_scores(home_goals, away_goals)
```

- Les deux scores attendus (ils font 1 au total) et les deux résultats.
- Arsenal 2-0 Atalanta : `e_home = 0.596`, `e_away = 0.404`, `s_home, s_away = 1.0, 0.0`.

```python
        elos[row["home_team"]] = update_rating(home_elo, K, s_home, e_home)
        elos[row["away_team"]] = update_rating(away_elo, K, s_away, e_away)
        counts["played"] += 1
```

- Les deux notes sont mises à jour directement dans `elos` : `elos["Arsenal"] : 1787.88 -> 1797.57`, `elos["Atalanta"] : 1720.12 -> 1710.43`.
- Les deux mises à jour utilisent les notes d'**avant** le match (`home_elo`, `away_elo`), pas celle qui vient d'être changée, donc l'ordre des deux lignes n'a pas d'importance.

```python
    features_df = pd.DataFrame(training_rows)
    features_df.to_csv(OUT_FEATURES_CSV, index=False)
    if write:
        with open(OUT_JSON, "w", encoding="utf-8") as fh:
            json.dump({c: round(r, 2) for c, r in sorted(elos.items())}, fh, indent=2, ensure_ascii=False)
```

- La liste de dictionnaires devient un tableau et est écrite dans `match_features.csv`. Cela arrive à chaque lancement, même sans `--write` (un bug connu).
- Avec `--write`, les notes finales sont écrites en JSON : triées par nom de club, arrondies à 2 décimales, `indent=2` pour un fichier lisible, et `ensure_ascii=False` pour que « München » reste « München » au lieu de `"München"`.

**En une ligne :** lit les matchs et les réglages, passe chaque vrai match dans la mise à jour Elo dans l'ordre des dates, et écrit les notes finales et une ligne de données par match.

---

## Les dernières lignes

```python
if __name__ == "__main__":
    run(write="--write" in sys.argv)
```

- Ce bloc ne s'exécute que quand le fichier est lancé directement (`python -m model.elo_score_updating`), pas quand un autre fichier l'importe.
- `"--write" in sys.argv` vaut `True` si l'utilisateur a tapé `--write` après la commande.
