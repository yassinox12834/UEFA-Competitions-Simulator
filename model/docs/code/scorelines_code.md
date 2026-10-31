# `scorelines.py`, line by line

> This page walks through the code of the score picker. For the idea (copy real football, the raffle), read [`../scorelines.md`](../scorelines.md) first. Extra time is explained in [`../extra_time.md`](../extra_time.md).

*Version française : [plus bas](#scorelinespy-ligne-par-ligne).*

## How to read this page

- Each function starts with its **arguments**.
- The code comes in groups of 2 to 4 lines, each followed by bullets: what, why, and which general idea.
- Each function ends with **In one line**.

---

## 1. The imports and settings

```python
import json
import random
from bisect import bisect
from itertools import accumulate
```

- `json` (comes with Python) reads and writes the table file.
- `random` (comes with Python) is only used by the demo at the bottom; the real picks use the random generator the match engine passes in.
- `bisect` (from `bisect`) finds where a number would fit in a sorted list, by halving the list again and again: a **binary search**.
- `accumulate` (from `itertools`) turns `[225, 458, 237]` into the running totals `[225, 683, 920]`.

| Code | Does | Example value |
|---|---|---|
| `OUTCOMES = ("home", "draw", "away")` | the three results, same names as the match model | |
| `MAX_GOALS = 6` | any number of goals above 6 is counted as 6 | 16-0 counted as 6-0 |
| `ET_KEEP = 1.0 / 3.0` | share of each goal kept for extra time (30 of 90 minutes) | 0.333 |
| `FALLBACK` | a small hand-made table used if `scorelines.json` is missing | `"draw": {"0-0": 30, "1-1": 45, ...}` |

---

## 2. `outcome_of(home_goals, away_goals)`

**Arguments:** `home_goals`, `away_goals`: `int`.

```python
def outcome_of(home_goals, away_goals):
    if home_goals > away_goals:
        return "home"
    if home_goals < away_goals:
        return "away"
    return "draw"
```

- `outcome_of(2, 1) -> "home"`, `outcome_of(1, 1) -> "draw"`.
- Used in three places: to file each real score under its result, to check the table, and by the match engine to check that a picked score fits.

**In one line:** turns a score into its result.

---

## 3. `build_table(fixtures_csv)`: count the real scores

**Arguments:** `fixtures_csv`: `Path`, the file of real matches.

```python
    import pandas as pd
    df = pd.read_csv(fixtures_csv)
    df = df[df["league"] != "Friendlies Clubs"]
```

- pandas is imported **inside** the function: only this function needs it, and it runs once, when the table is rebuilt. The app itself never imports pandas through this file.
- Keeps every row whose league is not "Friendlies Clubs" (**boolean filtering**): 684 friendlies are removed.

```python
    home_col, away_col = ("ft_home", "ft_away") if "ft_home" in df else ("home_goals", "away_goals")
    df = df.dropna(subset=[home_col, away_col])
```

- Prefers the `ft_` columns, the score after 90 minutes ("full time"). The other columns include extra-time goals, which would file a cup match won in extra time as a win instead of a draw.
- `dropna` removes matches without a score (not played yet, cancelled).

```python
    table = {o: {} for o in OUTCOMES}
    for h, a in zip(df[home_col].astype(int), df[away_col].astype(int)):
        h, a = min(h, MAX_GOALS), min(a, MAX_GOALS)
```

- Starts with three empty dictionaries, one per result, built with a **dictionary comprehension**.
- `zip` walks the two goal columns side by side; `.astype(int)` turns `2.0` into `2`.
- `min(h, 6)` caps each side at 6: `(16, 0) -> (6, 0)`. **Known bug:** the cap happens before the result is decided, so an 8-7 would become 6-6, a draw.

```python
        key = f"{h}-{a}"
        bucket = table[outcome_of(h, a)]
        bucket[key] = bucket.get(key, 0) + 1
    return table
```

- The score becomes text like `"2-1"`, because JSON keys must be text.
- `bucket.get(key, 0) + 1` adds one to the count, starting at 0 for a score seen for the first time: a **counting pattern**.
- `table["draw"]: {} -> {"1-1": 1} -> ... -> {"0-0": 225, "1-1": 458, ...}`.

**In one line:** reads the real matches and returns, for each result, how many times each score happened.

`save_table(table, path)` simply writes that dictionary to `scorelines.json`, with a comment and the total number of matches.

---

## 4. `ScorelineSampler.__init__(table, source)`: prepare the raffle

**Arguments:** `table`: `dict`, result to `{"h-a": count}`. `source`: `str`, a label for the log (`"scorelines.json"` or `"fallback"`).

```python
        for outcome in OUTCOMES:
            items = sorted(table[outcome].items())
            keys = [tuple(int(v) for v in k.split("-")) for k, _ in items]
            weights = [float(w) for _, w in items]
```

- For each result, sorts the scores so the order never depends on how the file was written: the same seed always gives the same score, even after the table is rebuilt.
- `"2-1".split("-")` gives `["2", "1"]`, and the inner loop turns it into the tuple `(2, 1)`. This parsing happens once here, never during a simulation.
- `weights` holds the counts as decimal numbers: `[225.0, 458.0, 237.0, 50.0, 5.0]` for draws.

```python
            if not keys or sum(weights) <= 0:
                raise ValueError(f"scoreline table has no entry for {outcome!r}")
            for (h, a) in keys:
                if outcome_of(h, a) != outcome:
```

- Two safety checks on the table: every result must have at least one score, and every score must really belong to its result (a "2-1" filed under "draw" is refused with an error).

```python
            self._keys[outcome] = keys
            self._cum[outcome] = list(accumulate(weights))
```

- Stores the scores and their running totals side by side: `_keys["draw"] = [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)]`, `_cum["draw"] = [225.0, 683.0, 920.0, 970.0, 975.0]`.
- The running totals are the "ticket numbers" of the raffle in [`../scorelines.md`](../scorelines.md), section 2.

**In one line:** turns the counts into sorted scores and running totals, ready for fast picks.

---

## 5. `ScorelineSampler.load(path)`

```python
    @classmethod
    def load(cls, path=TABLE_JSON):
        path = Path(path)
        if path.is_file():
            raw = json.loads(path.read_text(encoding="utf-8"))
            return cls(raw["table"], source=path.name)
        return cls(FALLBACK, source="fallback")
```

- An **alternative constructor**: builds a sampler from the file.
- If the file is missing, it uses the small built-in table instead of crashing, and the log shows `fallback`. A missing file is a setup mistake, not a reason to refuse to simulate.

---

## 6. `ScorelineSampler.sample(outcome, rng)`: pick one score

**Arguments:** `outcome`: `str`, `"home"`, `"draw"` or `"away"`. `rng`: `random.Random`, the season's generator.

```python
    def sample(self, outcome, rng):
        cum = self._cum[outcome]
        u = rng.random() * cum[-1]
        return self._keys[outcome][bisect(cum, u)]
```

- `cum[-1]` is the last running total, the number of tickets: 975 for draws. `u` becomes a ticket number between 0 and 975.
- `bisect(cum, u)` returns the position of the first running total **above** `u`: with `u = 360.75`, the totals `[225, 683, ...]` give position 1, and `_keys["draw"][1]` is `(1, 1)`.
- It uses **exactly one** random number per pick. The fast and full ways of playing a match rely on this to stay identical.
- Binary search needs about 5 comparisons for 19 scores, instead of up to 19 when reading the list from the top.

**In one line:** takes a result and a random generator, and returns a score that fits, as often as in real football.

---

## 7. `ScorelineSampler.sample_extra_time(rng, keep)`

**Arguments:** `rng`: `random.Random`. `keep`: `float`, the chance of keeping each goal, 1/3 by default.

```python
        outcome = OUTCOMES[int(rng.random() * 3)]
        h, a = self.sample(outcome, rng)
```

- Picks a result with one third each: `int(0.10 × 3) = 0`, "home". It does **not** use the ratings (a known limit).
- Then a full-match score for that result, for example 3-0.

```python
        return (sum(1 for _ in range(h) if rng.random() < keep),
                sum(1 for _ in range(a) if rng.random() < keep))
```

- For each goal, one random number: below 1/3, the goal is kept. With 3 home goals and the numbers 0.12, 0.81, 0.47, only the first is kept: 1-0.
- `sum(1 for ... if ...)` counts the kept goals without building a list (a **generator expression**).

**In one line:** returns the score of 30 minutes of extra time by keeping about a third of the goals of a full-match score.

---

## 8. `ScorelineSampler.probability(outcome, home_goals, away_goals)`

```python
        keys, cum = self._keys[outcome], self._cum[outcome]
        i = keys.index((home_goals, away_goals))
        weight = cum[i] - (cum[i - 1] if i else 0.0)
        return weight / cum[-1]
```

- Finds the score's position, gets its own count back from the running totals (this total minus the previous one), and divides by the total.
- `probability("draw", 0, 0) = 225 / 975 = 0.231`, the number shown in the expert log.
- A score never seen returns 0.0 (the real code catches the `ValueError` of `index`).

---
---

# `scorelines.py`, ligne par ligne

> Cette page explique le code du tireur de scores. Pour l'idée (copier le vrai football, la tombola), lisez d'abord [`../scorelines.md`](../scorelines.md#le-tireur-de-scores--dun-résultat-à-un-score). La prolongation est expliquée dans [`../extra_time.md`](../extra_time.md).

## Comment lire cette page

- Chaque fonction commence par ses **arguments**.
- Le code vient en groupes de 2 à 4 lignes, chacun suivi de points : quoi, pourquoi, et quelle idée générale.
- Chaque fonction se termine par **En une ligne**.

---

## 1. Les imports et les réglages

```python
import json
import random
from bisect import bisect
from itertools import accumulate
```

- `json` (fourni avec Python) lit et écrit le fichier de la table.
- `random` (fourni avec Python) ne sert qu'à la démo en bas du fichier ; les vrais tirages utilisent le générateur de hasard que le moteur de match fournit.
- `bisect` (de `bisect`) trouve où un nombre se placerait dans une liste triée, en coupant la liste en deux encore et encore : une **recherche dichotomique**.
- `accumulate` (de `itertools`) transforme `[225, 458, 237]` en totaux cumulés `[225, 683, 920]`.

| Code | Fait | Exemple |
|---|---|---|
| `OUTCOMES = ("home", "draw", "away")` | les trois résultats, mêmes noms que le modèle de match | |
| `MAX_GOALS = 6` | tout nombre de buts au-dessus de 6 compte comme 6 | 16-0 compté 6-0 |
| `ET_KEEP = 1.0 / 3.0` | part de chaque but gardée pour la prolongation (30 minutes sur 90) | 0.333 |
| `FALLBACK` | une petite table faite à la main, utilisée si `scorelines.json` manque | `"draw": {"0-0": 30, "1-1": 45, ...}` |

---

## 2. `outcome_of(home_goals, away_goals)`

**Arguments :** `home_goals`, `away_goals` : `int`.

```python
def outcome_of(home_goals, away_goals):
    if home_goals > away_goals:
        return "home"
    if home_goals < away_goals:
        return "away"
    return "draw"
```

- `outcome_of(2, 1) -> "home"`, `outcome_of(1, 1) -> "draw"`.
- Utilisée à trois endroits : pour ranger chaque vrai score sous son résultat, pour vérifier la table, et par le moteur de match pour vérifier qu'un score tiré correspond.

**En une ligne :** transforme un score en son résultat.

---

## 3. `build_table(fixtures_csv)` : compter les vrais scores

**Arguments :** `fixtures_csv` : `Path`, le fichier des vrais matchs.

```python
    import pandas as pd
    df = pd.read_csv(fixtures_csv)
    df = df[df["league"] != "Friendlies Clubs"]
```

- pandas est importé **dans** la fonction : seule cette fonction en a besoin, et elle ne tourne qu'une fois, quand la table est reconstruite. L'appli elle-même n'importe jamais pandas par ce fichier.
- Garde chaque ligne dont le championnat n'est pas « Friendlies Clubs » (**filtrage booléen**) : 684 amicaux sont retirés.

```python
    home_col, away_col = ("ft_home", "ft_away") if "ft_home" in df else ("home_goals", "away_goals")
    df = df.dropna(subset=[home_col, away_col])
```

- Préfère les colonnes `ft_`, le score après 90 minutes (*full time*). Les autres colonnes incluent les buts de prolongation, ce qui rangerait un match de coupe gagné en prolongation comme une victoire au lieu d'un nul.
- `dropna` retire les matchs sans score (pas encore joués, annulés).

```python
    table = {o: {} for o in OUTCOMES}
    for h, a in zip(df[home_col].astype(int), df[away_col].astype(int)):
        h, a = min(h, MAX_GOALS), min(a, MAX_GOALS)
```

- Commence avec trois dictionnaires vides, un par résultat, construits par un **dictionnaire en compréhension**.
- `zip` parcourt les deux colonnes de buts côte à côte ; `.astype(int)` transforme `2.0` en `2`.
- `min(h, 6)` plafonne chaque camp à 6 : `(16, 0) -> (6, 0)`. **Bug connu :** le plafond est appliqué avant de décider du résultat, donc un 8-7 deviendrait 6-6, un nul.

```python
        key = f"{h}-{a}"
        bucket = table[outcome_of(h, a)]
        bucket[key] = bucket.get(key, 0) + 1
    return table
```

- Le score devient un texte comme `"2-1"`, car les clés JSON doivent être du texte.
- `bucket.get(key, 0) + 1` ajoute un au compte, en partant de 0 pour un score vu pour la première fois : un **schéma de comptage**.
- `table["draw"] : {} -> {"1-1": 1} -> ... -> {"0-0": 225, "1-1": 458, ...}`.

**En une ligne :** lit les vrais matchs et renvoie, pour chaque résultat, combien de fois chaque score est arrivé.

`save_table(table, path)` écrit simplement ce dictionnaire dans `scorelines.json`, avec un commentaire et le nombre total de matchs.

---

## 4. `ScorelineSampler.__init__(table, source)` : préparer la tombola

**Arguments :** `table` : `dict`, résultat vers `{"h-a": nombre}`. `source` : `str`, une étiquette pour le journal (`"scorelines.json"` ou `"fallback"`).

```python
        for outcome in OUTCOMES:
            items = sorted(table[outcome].items())
            keys = [tuple(int(v) for v in k.split("-")) for k, _ in items]
            weights = [float(w) for _, w in items]
```

- Pour chaque résultat, trie les scores pour que l'ordre ne dépende jamais de la façon dont le fichier a été écrit : la même graine donne toujours le même score, même après une reconstruction de la table.
- `"2-1".split("-")` donne `["2", "1"]`, et la boucle intérieure en fait le tuple `(2, 1)`. Cette lecture n'a lieu qu'ici, jamais pendant une simulation.
- `weights` garde les nombres en décimaux : `[225.0, 458.0, 237.0, 50.0, 5.0]` pour les nuls.

```python
            if not keys or sum(weights) <= 0:
                raise ValueError(f"scoreline table has no entry for {outcome!r}")
            for (h, a) in keys:
                if outcome_of(h, a) != outcome:
```

- Deux vérifications de sécurité sur la table : chaque résultat doit avoir au moins un score, et chaque score doit vraiment appartenir à son résultat (un « 2-1 » rangé sous « nul » est refusé avec une erreur).

```python
            self._keys[outcome] = keys
            self._cum[outcome] = list(accumulate(weights))
```

- Range les scores et leurs totaux cumulés côte à côte : `_keys["draw"] = [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)]`, `_cum["draw"] = [225.0, 683.0, 920.0, 970.0, 975.0]`.
- Les totaux cumulés sont les « numéros de billets » de la tombola de [`../scorelines.md`](../scorelines.md), section 2.

**En une ligne :** transforme les comptes en scores triés et totaux cumulés, prêts pour des tirages rapides.

---

## 5. `ScorelineSampler.load(path)`

```python
    @classmethod
    def load(cls, path=TABLE_JSON):
        path = Path(path)
        if path.is_file():
            raw = json.loads(path.read_text(encoding="utf-8"))
            return cls(raw["table"], source=path.name)
        return cls(FALLBACK, source="fallback")
```

- Un **constructeur alternatif** : crée un tireur à partir du fichier.
- Si le fichier manque, il utilise la petite table intégrée au lieu de planter, et le journal affiche `fallback`. Un fichier manquant est une erreur d'installation, pas une raison de refuser de simuler.

---

## 6. `ScorelineSampler.sample(outcome, rng)` : tirer un score

**Arguments :** `outcome` : `str`, `"home"`, `"draw"` ou `"away"`. `rng` : `random.Random`, le générateur de la saison.

```python
    def sample(self, outcome, rng):
        cum = self._cum[outcome]
        u = rng.random() * cum[-1]
        return self._keys[outcome][bisect(cum, u)]
```

- `cum[-1]` est le dernier total cumulé, le nombre de billets : 975 pour les nuls. `u` devient un numéro de billet entre 0 et 975.
- `bisect(cum, u)` renvoie la position du premier total cumulé **au-dessus** de `u` : avec `u = 360.75`, les totaux `[225, 683, ...]` donnent la position 1, et `_keys["draw"][1]` vaut `(1, 1)`.
- Il utilise **exactement un** nombre au hasard par tirage. Les chemins rapide et complet du moteur de match en dépendent pour rester identiques.
- La recherche dichotomique demande environ 5 comparaisons pour 19 scores, au lieu de jusqu'à 19 en lisant la liste depuis le début.

**En une ligne :** prend un résultat et un générateur de hasard, et renvoie un score qui correspond, aussi souvent que dans le vrai football.

---

## 7. `ScorelineSampler.sample_extra_time(rng, keep)`

**Arguments :** `rng` : `random.Random`. `keep` : `float`, la chance de garder chaque but, 1/3 par défaut.

```python
        outcome = OUTCOMES[int(rng.random() * 3)]
        h, a = self.sample(outcome, rng)
```

- Choisit un résultat avec un tiers de chance chacun : `int(0.10 × 3) = 0`, « home ». Il n'utilise **pas** les notes (une limite connue).
- Puis un score de match complet pour ce résultat, par exemple 3-0.

```python
        return (sum(1 for _ in range(h) if rng.random() < keep),
                sum(1 for _ in range(a) if rng.random() < keep))
```

- Pour chaque but, un nombre au hasard : sous 1/3, le but est gardé. Avec 3 buts à domicile et les nombres 0.12, 0.81, 0.47, seul le premier est gardé : 1-0.
- `sum(1 for ... if ...)` compte les buts gardés sans construire de liste (une **expression génératrice**).

**En une ligne :** renvoie le score de 30 minutes de prolongation en gardant environ un tiers des buts d'un score de match complet.

---

## 8. `ScorelineSampler.probability(outcome, home_goals, away_goals)`

```python
        keys, cum = self._keys[outcome], self._cum[outcome]
        i = keys.index((home_goals, away_goals))
        weight = cum[i] - (cum[i - 1] if i else 0.0)
        return weight / cum[-1]
```

- Trouve la position du score, retrouve son propre compte à partir des totaux cumulés (ce total moins le précédent), et divise par le total.
- `probability("draw", 0, 0) = 225 / 975 = 0.231`, le nombre affiché dans le journal expert.
- Un score jamais vu renvoie 0.0 (le vrai code attrape la `ValueError` de `index`).
