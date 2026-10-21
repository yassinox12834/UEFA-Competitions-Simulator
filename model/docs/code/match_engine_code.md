# `match_engine.py`, line by line

> This page walks through the code that plays one simulated match. For the idea (the five steps, the ruler from 0 to 1), read [`../match_engine.md`](../match_engine.md) first.

*Version française : [plus bas](#match_enginepy-ligne-par-ligne).*

## How to read this page

- Each function starts with its **arguments**.
- The code comes in groups of 2 to 4 lines, each followed by bullets: what, why, and which general idea.
- Each function ends with **In one line**.

---

## 1. The imports

```python
import json
import math
from functools import lru_cache
from pathlib import Path
```

- `json` (comes with Python) reads `coefs.json`; `math` gives `math.exp` for the fast softmax; `lru_cache` remembers the $K$ table after the first read; `Path` builds the file path.

```python
from model.elo_score_updating_copy import expected_score, update_rating
from model.predictor import format_trace
from model.scorelines import outcome_of
```

- Three imports from the project: the two Elo formulas, the function that writes the model's steps as text, and `outcome_of`, which turns a score into "home", "draw" or "away".
- The first line has a side effect: `elo_score_updating_copy.py` imports pandas and numpy at its top, so importing this file needs them too, although nothing here uses them. This is a known bug.

---

## 2. The settings

| Code | Does | Example value |
|---|---|---|
| `STAGE_KEYS` | maps the simulation's short round names to the spelling of `coefs.json` | `"qf" -> "Quarter Final"` |
| `STAGE_LABELS` | titles for the log | `"qf" -> "Quarter-finals"` |
| `DEFAULT_ELO = 1500.0` | the rating of a club that has none | 1500.0 |
| `_S_HOME` | the Elo result of the home side for each outcome | `{"home": 1.0, "draw": 0.5, "away": 0.0}` |

---

## 3. `load_k_table(comp, path)`: the $K$ of every round

**Arguments:** `comp`: `str`, `"UCL"`, `"UEL"` or `"UECL"`. `path`: `Path`, where `coefs.json` is.

```python
def load_k_table(comp, path=COEFS_JSON):
    table, settings = _load_k_table(comp, str(path))
    return dict(table), dict(settings)
```

- Calls the cached version below, then returns **copies** of its results with `dict(...)`. If a caller changed the table it received, the cached original stays untouched.
- `str(path)` is passed because `lru_cache` needs arguments it can use as keys, and a plain text path is the simplest.

```python
@lru_cache(maxsize=None)
def _load_k_table(comp, path):
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    k_base, k_max = float(raw["k_base"]), float(raw["k_max"])
```

- `@lru_cache(maxsize=None)` remembers the answer for each `(comp, path)` forever: a simulation of 1 000 seasons used to read and parse this file 1 000 times; now it is read once. This is **memoisation**.
- Reads the base speed 20 and the ceiling 30.

```python
    block = raw["competitions"][comp]
    comp_mult = float(block["comp_mult"])
    table = {}
    for stage, key in STAGE_KEYS.items():
```

- Picks the block of one competition, for example the Champions League with weight 1.20.
- Loops over the six simulated rounds.

```python
        stage_mult = float(block["stages"][key])
        table[stage] = min(k_base * comp_mult * stage_mult, k_max)
    return table, {...}
```

- $K$ = base × competition weight × round weight, capped at 30. Champions League quarter-final: `min(20 × 1.20 × 1.08, 30) = 25.92`.
- `table: {} -> {"league": 24.0, "playoff": 24.72, "r16": 25.44, "qf": 25.92, "sf": 26.4, "final": 26.88}`. The second returned dictionary keeps the raw settings for the log.

**In one line:** takes a competition and returns the $K$ of each of its six rounds.

---

## 4. `Match`: the record of one played match

**Arguments:** 17 values, from `home` and `away` to `elo_home_after`, `elo_away_after` and `label` (the text for the log, such as `"MD3"`).

```python
    __slots__ = ("home", "away", "stage", "neutral", "elo_home", "elo_away",
                 "probs", "u", "outcome", "home_goals", "away_goals", "k",
                 "e_home", "s_home", "elo_home_after", "elo_away_after", "label")
```

- Lists the 17 allowed attributes: everything that produced the match, so the interface and the log can show any of it.
- `__slots__` saves memory and turns a misspelt attribute into an error. A season builds about 189 of these.

```python
        self.home, self.away, self.stage, self.neutral = home, away, stage, neutral
        self.elo_home, self.elo_away, self.probs, self.u = elo_home, elo_away, probs, u
```

- Stores the arguments four at a time by **tuple assignment** (the next three lines do the same for the rest).
- The arguments are given by position, not by name. A version that looped over named arguments was slower than playing the match itself, so plain assignments were kept.

```python
    @property
    def winner(self):
        if self.outcome == "home":
            return self.home
```

- `@property` lets code write `match.winner` without brackets, as if it were a stored value, although it is computed each time.
- Returns the home club, the away club, or `None` for a draw. `score` is another property that returns `"2-1"`.

---

## 5. `MatchEngine.__init__(model, sampler, ratings, k_table, rng, expert, k_settings)`

**Arguments:** `model`: the match model (`MatchModel`). `sampler`: the score picker (`ScorelineSampler`). `ratings`: `dict`, club to rating. `k_table`: `dict`, round to $K$. `rng`: `random.Random`, the season's only random generator. `expert`: `bool`, write the log. `k_settings`: `dict` or `None`, raw settings for the log.

```python
        self.model = model
        self.sampler = sampler
        self.ratings = dict(ratings)
        self.k_table = k_table
```

- Keeps references to the tools it needs: this is **dependency injection**, the engine receives its tools instead of creating them, so a test can hand it a fake model or a fixed random generator.
- `dict(ratings)` makes a **copy**. Without it, the first simulated season would write into the original ratings, and every later season would start from the end of the previous one.

```python
        self.rng = rng
        self.expert = expert
        self.trace = []
        self.played = 0
```

- One random generator for the whole season: every random choice (results, scores, coins, penalties) comes from it in a fixed order, so the same seed replays the same season.
- `trace` is the log, a list of text lines; section titles start with `"== "` so the interface can split the log into tabs.

---

## 6. `MatchEngine.play(home, away, stage, neutral, label)`: choose the way

**Arguments:** `home`, `away`: `str`. `stage`: `str`, a key of `STAGE_KEYS`. `neutral`: `bool`, `True` only for the final. `label`: `str` or `None`, text for the log.

```python
    def play(self, home, away, stage, neutral=False, label=None):
        if not self.expert and not neutral:
            return self._play_fast(home, away, stage, label)
        return self._play_full(home, away, stage, neutral, label)
```

- Most matches take the fast way: no log is needed and the ground is not neutral.
- Expert mode needs every intermediate number, and the final needs the model to be asked twice (once per orientation), so those take the full way.

**In one line:** plays one match, the fast way when possible.

---

## 7. `MatchEngine._play_fast(home, away, stage, label)`

**Arguments:** as `play`, without `neutral` (always `False` here).

```python
        ratings = self.ratings
        r_home = ratings.get(home, DEFAULT_ELO)
        r_away = ratings.get(away, DEFAULT_ELO)
        m = self.model
```

- Step 1: the **current** ratings, or 1500 for an unknown club.
- `ratings = self.ratings` and `m = self.model` copy the references into local names. Reading a local name is a little faster than reading an attribute, and this function runs about 189 000 times in a 1 000-season simulation.

```python
        xs = (r_home - r_away - m.mean) / m.scale
        (ca, cd, ch), (ba, bd, bh) = m.coef, m.intercept
        za, zd, zh = ca * xs + ba, cd * xs + bd, ch * xs + bh
```

- Step 2 begins: the standardised gap, then the three scores (away, draw, home), written out by hand instead of with a loop.
- `(ca, cd, ch), (ba, bd, bh) = ...` unpacks two lists of three at once: `ca = -0.5384`, `cd = -0.0308`, `ch = 0.5692`, and the same for the starting values.
- Arsenal v Atalanta: `xs = 0.767`, `za, zd, zh = -0.423, -0.370, 0.793`.

```python
        top = za if za > zd else zd
        if zh > top:
            top = zh
        ea, ed, eh = math.exp(za - top), math.exp(zd - top), math.exp(zh - top)
```

- Finds the biggest score without calling `max` (a little faster), then subtracts it from each score before `exp`. Softmax does not change, and `exp` can never overflow: this is a **numerically stable softmax**.
- `top = 0.793`, `ea, ed, eh = 0.296, 0.313, 1.0`.

```python
        total = ea + ed + eh
        p_home, p_draw = eh / total, ed / total
```

- Divides by the total: `p_home = 0.622`, `p_draw = 0.194`. The away chance is never computed: "away" is simply whatever is left above `p_home + p_draw`.

```python
        rng = self.rng
        u = rng.random()
        if u < p_home:
            outcome, s_home = "home", 1.0
```

- Step 3: one random number, cut by the running totals 0.622 and 0.816 (the ruler of [`../match_engine.md`](../match_engine.md), section 2). This way of turning one uniform number into a result is called **inverse transform sampling**.
- Seed 42 gives `u = 0.6394`, which lands in the `elif u < p_home + p_draw` branch: `outcome, s_home = "draw", 0.5`.

```python
        hg, ag = self.sampler.sample(outcome, rng)
```

- Step 4: a score that fits the outcome. It uses exactly one more random number, which matters for the next point.

```python
        k = self.k_table[stage]
        e_home = 1.0 / (1.0 + 10.0 ** ((r_away - r_home) / 400.0))
        new_home = r_home + k * (s_home - e_home)
        new_away = r_away + k * ((1.0 - s_home) - (1.0 - e_home))
```

- Step 5: the Elo update, with the formulas of `expected_score` and `update_rating` written inline.
- The away side uses `1 - s_home` and `1 - e_home`, so its change is exactly minus the home change: **zero-sum by construction**.
- `k = 24`, `e_home = 0.596`, `new_home = 1787.88 + 24 × (0.5 − 0.596) = 1785.57`, `new_away = 1722.43`.

```python
        ratings[home] = new_home
        ratings[away] = new_away
        self.played += 1
        return Match(home, away, stage, False, r_home, r_away, None, u, outcome, ...)
```

- Writes the new ratings back, so the clubs' next matches use them.
- Returns the record. `probs` is `None` here: the chances were not kept, to save time.

**In one line:** plays one match in as few steps as possible and returns its record; the result is identical to `_play_full` for the same seed.

---

## 8. `MatchEngine._play_full(home, away, stage, neutral, label)`

**Arguments:** as `play`.

```python
        r_home = self.ratings.get(home, DEFAULT_ELO)
        r_away = self.ratings.get(away, DEFAULT_ELO)
        probs = self.model.probabilities(r_home, r_away, neutral=neutral,
                                         trace=self.expert)
```

- The same step 1, then step 2 through the model's own method, which can also average both orientations for a neutral ground and keep every number for the log.

```python
        u = self.rng.random()
        if u < probs.p_home:
            outcome = "home"
        elif u < probs.p_home + probs.p_draw:
```

- The same step 3 with the same single random number, so the fast and full ways stay in step.

```python
        hg, ag = self.sampler.sample(outcome, self.rng)
        assert outcome_of(hg, ag) == outcome
```

- Step 4, plus a check that the score really fits the outcome (a 2-1 must be a home win). `assert` is a development check: `python -O` removes it.

```python
        e_home = expected_score(r_home, r_away)
        s_home = _S_HOME[outcome]
        new_home = update_rating(r_home, k, s_home, e_home)
        new_away = update_rating(r_away, k, 1.0 - s_home, 1.0 - e_home)
```

- Step 5 through the named Elo functions. Same numbers as the fast way.

```python
        match = Match(...)
        if self.expert:
            self._log(match)
        return match
```

- Builds the record with the chances kept, writes the log in expert mode, and returns the record.

**In one line:** plays one match through the named functions, keeping every number, and logs it in expert mode.

---

## 9. `MatchEngine._log(m)`: the expert log

| Line written | Example |
|---|---|
| a header | `-- MD1: Arsenal v Atalanta` |
| the model's steps, from `format_trace` | `x' = (x - -0.151) / 88.495 = 0.767` |
| the three chances | `p_home = 0.622   p_draw = 0.194   p_away = 0.184` |
| the random number and the cut points | `u = 0.6394  ->  DRAW  (home if u < 0.622, draw if u < 0.816, else away)` |
| the score and its chance among scores of that outcome | `scoreline 0-0  (P = 0.231 given draw)` |
| the Elo step | `E_home = ... = 0.596   S_home = 0.5   K = 24.00` |
| the ratings before and after | `Arsenal: 1787.9 -> 1785.6 (-2.3)` |

`section(title)` and `note(text)` add a title or a free line to the same log, and do nothing outside expert mode.

---
---

# `match_engine.py`, ligne par ligne

> Cette page explique le code qui joue un match simulé. Pour l'idée (les cinq étapes, la règle graduée de 0 à 1), lis d'abord [`../match_engine.md`](../match_engine.md#le-moteur-de-match--un-match-simulé).

## Comment lire cette page

- Chaque fonction commence par ses **arguments**.
- Le code vient en groupes de 2 à 4 lignes, chacun suivi de points : quoi, pourquoi, et quelle idée générale.
- Chaque fonction se termine par **En une ligne**.

---

## 1. Les imports

```python
import json
import math
from functools import lru_cache
from pathlib import Path
```

- `json` (fourni avec Python) lit `coefs.json` ; `math` donne `math.exp` pour la softmax rapide ; `lru_cache` garde en mémoire la table des $K$ après la première lecture ; `Path` construit le chemin du fichier.

```python
from model.elo_score_updating_copy import expected_score, update_rating
from model.predictor import format_trace
from model.scorelines import outcome_of
```

- Trois imports du projet : les deux formules d'Elo, la fonction qui écrit les étapes du modèle en texte, et `outcome_of`, qui transforme un score en « home », « draw » ou « away ».
- La première ligne a un effet secondaire : `elo_score_updating_copy.py` importe pandas et numpy en haut, donc importer ce fichier en a aussi besoin, alors que rien ici ne s'en sert. C'est un bug connu.

---

## 2. Les réglages

| Code | Fait | Exemple |
|---|---|---|
| `STAGE_KEYS` | relie les noms courts des tours de la simulation à l'orthographe de `coefs.json` | `"qf" -> "Quarter Final"` |
| `STAGE_LABELS` | titres pour le journal | `"qf" -> "Quarter-finals"` |
| `DEFAULT_ELO = 1500.0` | la note d'un club qui n'en a pas | 1500.0 |
| `_S_HOME` | le résultat Elo de l'équipe à domicile pour chaque résultat | `{"home": 1.0, "draw": 0.5, "away": 0.0}` |

---

## 3. `load_k_table(comp, path)` : le $K$ de chaque tour

**Arguments :** `comp` : `str`, `"UCL"`, `"UEL"` ou `"UECL"`. `path` : `Path`, l'endroit où se trouve `coefs.json`.

```python
def load_k_table(comp, path=COEFS_JSON):
    table, settings = _load_k_table(comp, str(path))
    return dict(table), dict(settings)
```

- Appelle la version en cache ci-dessous, puis renvoie des **copies** de ses résultats avec `dict(...)`. Si un appelant modifiait la table reçue, l'original en cache resterait intact.
- `str(path)` est passé car `lru_cache` a besoin d'arguments utilisables comme clés, et un simple chemin en texte est le plus simple.

```python
@lru_cache(maxsize=None)
def _load_k_table(comp, path):
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    k_base, k_max = float(raw["k_base"]), float(raw["k_max"])
```

- `@lru_cache(maxsize=None)` garde la réponse pour chaque `(comp, path)` pour toujours : une simulation de 1 000 saisons lisait et analysait ce fichier 1 000 fois ; maintenant il est lu une fois. C'est la **mémoïsation**.
- Lit la vitesse de base 20 et le plafond 30.

```python
    block = raw["competitions"][comp]
    comp_mult = float(block["comp_mult"])
    table = {}
    for stage, key in STAGE_KEYS.items():
```

- Prend le bloc d'une compétition, par exemple la Ligue des champions avec un poids de 1.20.
- Parcourt les six tours simulés.

```python
        stage_mult = float(block["stages"][key])
        table[stage] = min(k_base * comp_mult * stage_mult, k_max)
    return table, {...}
```

- $K$ = base × poids de la compétition × poids du tour, plafonné à 30. Quart de finale de Ligue des champions : `min(20 × 1.20 × 1.08, 30) = 25.92`.
- `table : {} -> {"league": 24.0, "playoff": 24.72, "r16": 25.44, "qf": 25.92, "sf": 26.4, "final": 26.88}`. Le deuxième dictionnaire renvoyé garde les réglages bruts pour le journal.

**En une ligne :** prend une compétition et renvoie le $K$ de chacun de ses six tours.

---

## 4. `Match` : la fiche d'un match joué

**Arguments :** 17 valeurs, de `home` et `away` à `elo_home_after`, `elo_away_after` et `label` (le texte pour le journal, comme `"MD3"`).

```python
    __slots__ = ("home", "away", "stage", "neutral", "elo_home", "elo_away",
                 "probs", "u", "outcome", "home_goals", "away_goals", "k",
                 "e_home", "s_home", "elo_home_after", "elo_away_after", "label")
```

- Liste les 17 attributs permis : tout ce qui a produit le match, pour que l'interface et le journal puissent en montrer n'importe quelle partie.
- `__slots__` économise de la mémoire et transforme un attribut mal écrit en erreur. Une saison en construit environ 189.

```python
        self.home, self.away, self.stage, self.neutral = home, away, stage, neutral
        self.elo_home, self.elo_away, self.probs, self.u = elo_home, elo_away, probs, u
```

- Range les arguments quatre par quatre par **affectation de tuple** (les trois lignes suivantes font pareil pour le reste).
- Les arguments sont donnés par position, pas par nom. Une version qui parcourait des arguments nommés était plus lente que jouer le match lui-même, donc de simples affectations ont été gardées.

```python
    @property
    def winner(self):
        if self.outcome == "home":
            return self.home
```

- `@property` permet d'écrire `match.winner` sans parenthèses, comme une valeur rangée, alors qu'elle est calculée à chaque fois.
- Renvoie le club à domicile, le club à l'extérieur, ou `None` pour un nul. `score` est une autre propriété qui renvoie `"2-1"`.

---

## 5. `MatchEngine.__init__(model, sampler, ratings, k_table, rng, expert, k_settings)`

**Arguments :** `model` : le modèle de match (`MatchModel`). `sampler` : le tireur de scores (`ScorelineSampler`). `ratings` : `dict`, club vers note. `k_table` : `dict`, tour vers $K$. `rng` : `random.Random`, le seul générateur de hasard de la saison. `expert` : `bool`, écrire le journal. `k_settings` : `dict` ou `None`, réglages bruts pour le journal.

```python
        self.model = model
        self.sampler = sampler
        self.ratings = dict(ratings)
        self.k_table = k_table
```

- Garde des références vers les outils dont il a besoin : c'est l'**injection de dépendances**, le moteur reçoit ses outils au lieu de les créer, donc un test peut lui donner un faux modèle ou un générateur de hasard fixe.
- `dict(ratings)` fait une **copie**. Sans elle, la première saison simulée écrirait dans les notes d'origine, et chaque saison suivante partirait de la fin de la précédente.

```python
        self.rng = rng
        self.expert = expert
        self.trace = []
        self.played = 0
```

- Un seul générateur de hasard pour toute la saison : chaque choix au hasard (résultats, scores, pièces, tirs au but) en vient dans un ordre fixe, donc la même graine rejoue la même saison.
- `trace` est le journal, une liste de lignes de texte ; les titres de section commencent par `"== "` pour que l'interface puisse découper le journal en onglets.

---

## 6. `MatchEngine.play(home, away, stage, neutral, label)` : choisir le chemin

**Arguments :** `home`, `away` : `str`. `stage` : `str`, une clé de `STAGE_KEYS`. `neutral` : `bool`, `True` seulement pour la finale. `label` : `str` ou `None`, texte pour le journal.

```python
    def play(self, home, away, stage, neutral=False, label=None):
        if not self.expert and not neutral:
            return self._play_fast(home, away, stage, label)
        return self._play_full(home, away, stage, neutral, label)
```

- La plupart des matchs prennent le chemin rapide : pas besoin de journal et le terrain n'est pas neutre.
- Le mode expert a besoin de chaque nombre intermédiaire, et la finale a besoin d'interroger le modèle deux fois (une fois par sens), donc ceux-là prennent le chemin complet.

**En une ligne :** joue un match, par le chemin rapide quand c'est possible.

---

## 7. `MatchEngine._play_fast(home, away, stage, label)`

**Arguments :** comme `play`, sans `neutral` (toujours `False` ici).

```python
        ratings = self.ratings
        r_home = ratings.get(home, DEFAULT_ELO)
        r_away = ratings.get(away, DEFAULT_ELO)
        m = self.model
```

- Étape 1 : les notes **actuelles**, ou 1500 pour un club inconnu.
- `ratings = self.ratings` et `m = self.model` copient les références dans des noms locaux. Lire un nom local est un peu plus rapide que lire un attribut, et cette fonction tourne environ 189 000 fois dans une simulation de 1 000 saisons.

```python
        xs = (r_home - r_away - m.mean) / m.scale
        (ca, cd, ch), (ba, bd, bh) = m.coef, m.intercept
        za, zd, zh = ca * xs + ba, cd * xs + bd, ch * xs + bh
```

- Début de l'étape 2 : l'écart standardisé, puis les trois scores (extérieur, nul, domicile), écrits à la main au lieu d'une boucle.
- `(ca, cd, ch), (ba, bd, bh) = ...` déballe deux listes de trois d'un coup : `ca = -0.5384`, `cd = -0.0308`, `ch = 0.5692`, et pareil pour les valeurs de départ.
- Arsenal-Atalanta : `xs = 0.767`, `za, zd, zh = -0.423, -0.370, 0.793`.

```python
        top = za if za > zd else zd
        if zh > top:
            top = zh
        ea, ed, eh = math.exp(za - top), math.exp(zd - top), math.exp(zh - top)
```

- Trouve le plus grand score sans appeler `max` (un peu plus rapide), puis le soustrait à chaque score avant `exp`. Softmax ne change pas, et `exp` ne peut jamais déborder : c'est une **softmax numériquement stable**.
- `top = 0.793`, `ea, ed, eh = 0.296, 0.313, 1.0`.

```python
        total = ea + ed + eh
        p_home, p_draw = eh / total, ed / total
```

- Divise par le total : `p_home = 0.622`, `p_draw = 0.194`. La chance « extérieur » n'est jamais calculée : « extérieur » est simplement tout ce qui reste au-dessus de `p_home + p_draw`.

```python
        rng = self.rng
        u = rng.random()
        if u < p_home:
            outcome, s_home = "home", 1.0
```

- Étape 3 : un nombre au hasard, coupé par les totaux cumulés 0.622 et 0.816 (la règle graduée de [`../match_engine.md`](../match_engine.md), section 2). Cette façon de transformer un nombre uniforme en résultat s'appelle l'**échantillonnage par inversion**.
- La graine 42 donne `u = 0.6394`, qui tombe dans la branche `elif u < p_home + p_draw` : `outcome, s_home = "draw", 0.5`.

```python
        hg, ag = self.sampler.sample(outcome, rng)
```

- Étape 4 : un score qui correspond au résultat. Elle utilise exactement un nombre au hasard de plus, ce qui compte pour le point suivant.

```python
        k = self.k_table[stage]
        e_home = 1.0 / (1.0 + 10.0 ** ((r_away - r_home) / 400.0))
        new_home = r_home + k * (s_home - e_home)
        new_away = r_away + k * ((1.0 - s_home) - (1.0 - e_home))
```

- Étape 5 : la mise à jour Elo, avec les formules de `expected_score` et `update_rating` écrites directement.
- L'équipe à l'extérieur utilise `1 - s_home` et `1 - e_home`, donc son changement est exactement l'opposé de celui de l'équipe à domicile : **somme nulle par construction**.
- `k = 24`, `e_home = 0.596`, `new_home = 1787.88 + 24 × (0.5 − 0.596) = 1785.57`, `new_away = 1722.43`.

```python
        ratings[home] = new_home
        ratings[away] = new_away
        self.played += 1
        return Match(home, away, stage, False, r_home, r_away, None, u, outcome, ...)
```

- Réécrit les nouvelles notes, pour que les prochains matchs des clubs les utilisent.
- Renvoie la fiche. `probs` vaut `None` ici : les chances ne sont pas gardées, pour gagner du temps.

**En une ligne :** joue un match en le moins d'étapes possible et renvoie sa fiche ; le résultat est identique à `_play_full` pour la même graine.

---

## 8. `MatchEngine._play_full(home, away, stage, neutral, label)`

**Arguments :** comme `play`.

```python
        r_home = self.ratings.get(home, DEFAULT_ELO)
        r_away = self.ratings.get(away, DEFAULT_ELO)
        probs = self.model.probabilities(r_home, r_away, neutral=neutral,
                                         trace=self.expert)
```

- La même étape 1, puis l'étape 2 par la méthode du modèle lui-même, qui peut aussi faire la moyenne des deux sens pour un terrain neutre et garder chaque nombre pour le journal.

```python
        u = self.rng.random()
        if u < probs.p_home:
            outcome = "home"
        elif u < probs.p_home + probs.p_draw:
```

- La même étape 3 avec le même nombre au hasard unique, pour que les chemins rapide et complet restent alignés.

```python
        hg, ag = self.sampler.sample(outcome, self.rng)
        assert outcome_of(hg, ag) == outcome
```

- Étape 4, plus une vérification que le score correspond bien au résultat (un 2-1 doit être une victoire à domicile). `assert` est une vérification de développement : `python -O` la supprime.

```python
        e_home = expected_score(r_home, r_away)
        s_home = _S_HOME[outcome]
        new_home = update_rating(r_home, k, s_home, e_home)
        new_away = update_rating(r_away, k, 1.0 - s_home, 1.0 - e_home)
```

- Étape 5 par les fonctions Elo nommées. Mêmes nombres que le chemin rapide.

```python
        match = Match(...)
        if self.expert:
            self._log(match)
        return match
```

- Construit la fiche en gardant les chances, écrit le journal en mode expert, et renvoie la fiche.

**En une ligne :** joue un match par les fonctions nommées, en gardant chaque nombre, et l'écrit dans le journal en mode expert.

---

## 9. `MatchEngine._log(m)` : le journal expert

| Ligne écrite | Exemple |
|---|---|
| un titre | `-- MD1: Arsenal v Atalanta` |
| les étapes du modèle, par `format_trace` | `x' = (x - -0.151) / 88.495 = 0.767` |
| les trois chances | `p_home = 0.622   p_draw = 0.194   p_away = 0.184` |
| le nombre au hasard et les points de coupure | `u = 0.6394  ->  DRAW  (home if u < 0.622, draw if u < 0.816, else away)` |
| le score et sa chance parmi les scores de ce résultat | `scoreline 0-0  (P = 0.231 given draw)` |
| le pas Elo | `E_home = ... = 0.596   S_home = 0.5   K = 24.00` |
| les notes avant et après | `Arsenal: 1787.9 -> 1785.6 (-2.3)` |

`section(title)` et `note(text)` ajoutent un titre ou une ligne libre au même journal, et ne font rien hors du mode expert.
