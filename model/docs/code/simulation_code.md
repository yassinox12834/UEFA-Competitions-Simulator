# `simulation.py`, line by line

> This page walks through the code that runs one season and the Monte Carlo. For the idea (one season, repeating it, how much luck is left), read [`../monte_carlo.md`](../monte_carlo.md) first.

*Version française : [plus bas](#simulationpy-ligne-par-ligne).*

## How to read this page

- Each function starts with its **arguments**.
- The code comes in groups of 2 to 4 lines, each followed by bullets: what, why, and which general idea.
- Each function ends with **In one line**.
- The text-export functions (`summary_lines`, `describe_tie`, `write_log`) and the log header are summed up in a table at the end.

---

## 1. The imports

```python
import json
import os
import random
import time
```

- `json` reads the ratings file; `os` gives `os.cpu_count()`; `random` gives one `random.Random` per season; `time.perf_counter()` measures durations. All come with Python.

```python
from model import knockout, league_phase
from model.match_engine import DEFAULT_ELO, STAGE_LABELS, MatchEngine, load_k_table
from model.names import resolve_all
from model.predictor import MatchModel
from model.scorelines import ScorelineSampler
```

- Every other part of the model: this file is the **orchestrator**, the one place that calls all the others in the right order.

| Code | Does |
|---|---|
| `ELO_JSON` | path of `eeelo_final.json`, the starting ratings |
| `STAGES = ("top8", "top24", "r16", "qf", "sf", "final", "winner")` | the columns of the table of chances |
| `PARALLEL_FROM = 2000` | from this many seasons, use several processes |

---

## 2. `SimConfig(method, expert, seed, runs)`: the user's choices

**Arguments:** `method`: `str`, one of `knockout.METHODS`. `expert`: `bool`, write the log. `seed`: any value, or `None` for a fresh one. `runs`: `int`, stored only.

```python
        if method not in knockout.METHODS:
            raise ValueError(f"method must be one of {knockout.METHODS}")
        self.method = method
        self.expert = expert
```

- Refuses an unknown method as early as possible, before any season starts.

```python
        ranint = random.randint(-400, 400)
        self.seed = random.random() + ranint if seed is None else seed
```

- Without a seed, a fresh one is made from Python's shared generator: a decimal number between −400 and 401, for example 137.52.
- **Known bug:** the first line runs **even when a seed is given**, so every `SimConfig` uses up a number of the shared generator for nothing. Moving it inside the "no seed" case would fix it.

---

## 3. `Resources(model, sampler, ratings)`: the three files, read once

**Arguments:** `model`: a `MatchModel` or `None`. `sampler`: a `ScorelineSampler` or `None`. `ratings`: `dict` or `None`. `None` means "read it from disk".

```python
        self.model = model or MatchModel.load()
        self.sampler = sampler or ScorelineSampler.load()
```

- `a or b` gives `a` if it is something, otherwise `b`: a short way to write "use what was given, or load the default". Loading only happens when nothing was passed.

```python
        if ratings is None:
            ratings = {c: float(r) for c, r in
                       json.loads(ELO_JSON.read_text(encoding="utf-8")).items()}
        self.ratings = ratings
        self._seeds = {}
```

- Reads the 984 ratings and makes each one a `float`.
- `_seeds` is an empty memory for `seeds_for` below.

```python
    def seeds_for(self, clubs):
        key = tuple(clubs)
        if key not in self._seeds:
            self._seeds[key] = seed_ratings(clubs, self.ratings)
        seeds, resolutions = self._seeds[key]
        return dict(seeds), resolutions
```

- Finds the ratings of the draw's clubs **once** per list of clubs and remembers them (**memoisation**). Matching names used to take 60 % of the time of a Monte Carlo when it was redone every season.
- `tuple(clubs)` is used as the key because a list cannot be a dictionary key (it could change), but a tuple can.
- `dict(seeds)` returns a **copy**, so a season that changes ratings cannot change the remembered ones.

**In one line:** holds the match model, the score table and the ratings, and gives each club its starting rating without redoing the work.

---

## 4. `seed_ratings(clubs, ratings)`

```python
    resolutions = resolve_all(clubs, ratings.keys())
    seeds = {}
    for res in resolutions:
        seeds[res.club] = ratings[res.key] if res.key is not None else DEFAULT_ELO
    return seeds, resolutions
```

- Asks `names.py` to match every pot name to a ratings-file name ([`names_code.md`](names_code.md)).
- Each club gets its rating, or 1500 if it was not found. `"Bayern Munich" -> "Bayern München" -> 1811.07`.

**In one line:** turns pot names into `{club: rating}`, plus the record of how each name was matched.

---

## 5. `SimulationResult` and `stage_reached`

```python
    def __init__(self, **kw):
        for name in self.__slots__:
            setattr(self, name, kw.get(name))
```

- `**kw` collects every named argument into a dictionary. The loop copies each allowed one onto the object with `setattr`, and sets the missing ones to `None`.

```python
        for row in self.table:
            reached[row.club] = "top24" if row.rank <= 24 else "league"
            if row.rank <= 8:
                reached[row.club] = "top8"
```

- In `stage_reached`: first, every club's furthest step after the league phase: out (`"league"`), top 24 or top 8.

```python
        for stage in ("r16", "qf", "sf", "final"):
            for tie in self.rounds.get(stage, ()):
                reached[tie.a] = reached[tie.b] = stage
        reached[self.champion] = "winner"
```

- Then, round by round, both clubs of every tie are marked as having reached it; a later round overwrites an earlier one. Finally the champion is marked `"winner"`.
- `self.rounds.get(stage, ())` gives an empty tuple if a round is missing, so the loop simply does nothing.

**In one line:** returns, for each club, the furthest round it reached in this season.

---

## 6. `simulate(comp, teams, matchdays, config, resources)`: one season

**Arguments:** `comp`: `str`, `"UCL"`, `"UEL"` or `"UECL"`. `teams`: `dict`, the draw. `matchdays`: `list` of days. `config`: `SimConfig` or `None`. `resources`: `Resources` or `None`.

```python
    config = config or SimConfig()
    res = resources or Resources()
    t0 = time.perf_counter()
```

- Defaults if nothing was given, and a start time to measure the season.

```python
    clubs = list(teams)
    seeds, resolutions = res.seeds_for(clubs)
    k_table, k_settings = load_k_table(comp)
```

- `list(teams)` gives the club names in pot order (a dictionary keeps the order in which keys were added).
- The starting ratings, and the $K$ of each round for this competition.

```python
    engine = MatchEngine(res.model, res.sampler, seeds, k_table,
                         random.Random(config.seed), expert=config.expert,
                         k_settings=k_settings)
```

- One engine for the whole season, with **one** private random generator made from the seed. Every random choice of the season comes from it, which is why the same seed always replays the same season.

```python
    warnings = [f"{r.club}: not found in the Elo file, starting at {DEFAULT_ELO:.0f}"
                for r in resolutions if r.key is None]
```

- One warning per club whose name could not be matched; the app shows them, so a missing club is never silent.

```python
    league = league_phase.play_league_phase(engine, matchdays)
    table = league_phase.build_table(clubs, league, seeds)
    rounds = knockout.play_knockout(engine, table, config.method)
    champion = rounds["final"][0].winner
```

- The season itself in four lines: league phase, table, knockout rounds, champion. (In expert mode, the real code also writes the table and the tiebreaker explanations to the log between the second and third lines.)
- `build_table` receives the **starting** ratings `seeds`, not the current ones, for the last tiebreaker.

```python
    return SimulationResult(
        comp=comp, config=config, clubs=clubs, resolutions=resolutions,
        seed_ratings=seeds, league=league, table=table, rounds=rounds,
        champion=champion, final_ratings=dict(engine.ratings), ...)
```

- Packs everything into one record, including a copy of the ratings at the end of the season and the time it took.

**In one line:** plays one complete season from a draw and returns everything that happened.

---

## 7. `monte_carlo(comp, teams, matchdays, config, runs, resources, progress, workers)`

**Arguments:** as `simulate`, plus `runs`: `int`, how many seasons. `progress`: a function called as `progress(done, total)`, or `None`. `workers`: `int` or `None` for automatic.

```python
    base = random.Random(config.seed)
    seeds = [base.random() for _ in range(runs)]
    clubs = list(teams)
    days = [sorted(day) for day in matchdays]
```

- Draws **all** the season seeds before playing anything: season `i` always uses `seeds[i]`, whichever process plays it. So the result is the same with 1 process or 8.
- Sorts each day's matches once here, instead of once per season.

```python
    if workers is None:
        workers = min(os.cpu_count() or 1, 8) if runs >= PARALLEL_FROM else 1
```

- Below 2 000 seasons, one process (starting processes has a cost). Above, one per core, at most 8. `os.cpu_count() or 1` guards against a computer that does not report its core count.

```python
    if workers > 1:
        try:
            counts, points = _mc_parallel(comp, clubs, days, config.method, seeds,
                                          workers, progress)
        except Cancelled:
            raise
        except Exception:
            counts = points = None
```

- Tries the parallel way. If the user pressed Cancel, `Cancelled` is passed on (`raise` without anything re-raises the same error). Any other error (for example processes that cannot start) is caught, and the code falls back to one process.
- The order of the two `except` blocks matters: Python uses the first that matches, so `Cancelled` must come before the general `Exception`.

```python
    if counts is None:
        res = resources or Resources()
        counts, points = _mc_block(comp, clubs, days, config.method, seeds, res,
                                   progress, runs)
    return MonteCarloResult(comp, runs, counts, points, time.perf_counter() - t0, config)
```

- One-process way: play every season here. Then wrap the counts in a result object.

**In one line:** plays `runs` seasons, in one or several processes, and returns how often each club reached each round.

---

## 8. `_mc_block(comp, clubs, days, method, seeds, res, progress, total)`: count

```python
    counts = {club: dict.fromkeys(STAGES, 0) for club in clubs}
    points = dict.fromkeys(clubs, 0)
```

- One counter per club and per round, all starting at 0. `dict.fromkeys(STAGES, 0)` gives `{"top8": 0, "top24": 0, ...}`. Safe because 0 is a number; `dict.fromkeys(STAGES, [])` would give every key the **same** list.

```python
    chain = ("top24", "r16", "qf", "sf", "final", "winner")
    upto = {stage: chain[:i + 1] for i, stage in enumerate(chain)}
    upto["top8"] = upto["top24"]
```

- `upto[stage]` lists every round a club has reached if it got to `stage`: `upto["sf"] = ("top24", "r16", "qf", "sf")`. `chain[:i + 1]` is a **slice**, the first `i + 1` items.
- "Top 8" is not in the chain (a club can reach the round of 16 through the play-offs without being top 8), so it counts like "top 24" here and is added separately below.

```python
    for i, seed in enumerate(seeds):
        run_cfg = SimConfig(method, expert=False, seed=seed)
        result = simulate(comp, clubs, days, run_cfg, res)
```

- One season per seed, without the log (it would only slow things down).

```python
        for row in result.table:
            points[row.club] += row.points
            if row.rank <= 8:
                counts[row.club]["top8"] += 1
```

- Adds up each club's league points (to show average points later) and counts the top-8 finishes.

```python
        for club, stage in result.stage_reached().items():
            for s in upto.get(stage, ()):
                counts[club][s] += 1
        if progress is not None:
            progress(i + 1, total or len(seeds))
```

- A semi-finalist adds 1 to top 24, round of 16, quarter-finals and semi-finals. A club out in the league phase (`"league"`) is not in `upto`, so `get` returns an empty tuple and nothing is added.
- Reports progress after every season. If the user cancels, the `progress` function raises `Cancelled`, which stops the loop from the outside: the loop needs no stop flag of its own.

**In one line:** plays one season per seed and counts, for every club, the rounds it reached and its league points.

---

## 9. `_mc_parallel(comp, clubs, days, method, seeds, workers, progress)`

```python
    from concurrent.futures import ProcessPoolExecutor, as_completed
    size = max(50, len(seeds) // (workers * 4))
    chunks = [seeds[i:i + size] for i in range(0, len(seeds), size)]
```

- Imported inside the function: only needed for big runs.
- Cuts the seeds into chunks of about a quarter of each worker's share (at least 50), so the progress bar moves several times. 10 000 seasons on 2 workers: chunks of 1 250.

```python
    pool = ProcessPoolExecutor(max_workers=workers, initializer=_mc_worker_init)
    try:
        futures = [pool.submit(_mc_worker, (comp, clubs, days, method, chunk))
                   for chunk in chunks]
```

- Starts the processes. `initializer=_mc_worker_init` runs once in each new process and loads its own `Resources` from disk. **Known bug:** this means custom ratings passed to `monte_carlo` are ignored by the processes.
- `pool.submit` sends one chunk to the pool and returns a **future**, a promise of a result that will exist later.

```python
        for fut in as_completed(futures):
            n, (c, p) = fut.result()
            for club in clubs:
                points[club] += p[club]
```

- `as_completed` gives each future as soon as it finishes, whatever the order, so the counts are merged as early as possible. The real code then adds each round's count the same way.

```python
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
```

- `finally` runs whether the loop ended normally, was cancelled, or failed. `cancel_futures=True` drops the chunks not started yet, and `wait=False` returns at once, so Cancel feels immediate.
- A `with ProcessPoolExecutor() as pool:` block was not used on purpose: leaving it waits for every job, which would make Cancel wait for the whole Monte Carlo.

**In one line:** spreads the seasons over several processes and merges their counts as they finish.

---

## 10. Text export and log header

| Function | Does |
|---|---|
| `summary_lines(result)` | the season as text: a header line, warnings, the league table, every round, the champion |
| `describe_tie(tie)` | one line per tie, for example `Atalanta 0-0 Arsenal  \|  Arsenal 0-0 Atalanta  (agg 0-0, aet 1-0)  ->  Arsenal` |
| `write_log(result, dest_dir, stamp)` | writes the summary, then the expert log, to `data/processed/sim_UCL_<date-time>.txt`, with `encoding="utf-8"` so names like "Başakşehir" are saved correctly on Windows |
| `_log_header(...)` | in expert mode, writes the model's numbers, the score table used, the $K$ of each round, and every club's starting rating with how its name was matched |
| `MonteCarloResult.rows()` | turns counts into chances, sorted by chance of winning, then of reaching the final, and so on |
| `Cancelled` | an empty error class used only as a "stop" signal |

---
---

# `simulation.py`, ligne par ligne

> Cette page explique le code qui joue une saison et le Monte Carlo. Pour l'idée (une saison, la répéter, combien de hasard il reste), lis d'abord [`../monte_carlo.md`](../monte_carlo.md#la-simulation-et-le-monte-carlo).

## Comment lire cette page

- Chaque fonction commence par ses **arguments**.
- Le code vient en groupes de 2 à 4 lignes, chacun suivi de points : quoi, pourquoi, et quelle idée générale.
- Chaque fonction se termine par **En une ligne**.
- Les fonctions d'export en texte (`summary_lines`, `describe_tie`, `write_log`) et l'en-tête du journal sont résumées dans un tableau à la fin.

---

## 1. Les imports

```python
import json
import os
import random
import time
```

- `json` lit le fichier des notes ; `os` donne `os.cpu_count()` ; `random` donne un `random.Random` par saison ; `time.perf_counter()` mesure les durées. Tous fournis avec Python.

```python
from model import knockout, league_phase
from model.match_engine import DEFAULT_ELO, STAGE_LABELS, MatchEngine, load_k_table
from model.names import resolve_all
from model.predictor import MatchModel
from model.scorelines import ScorelineSampler
```

- Toutes les autres parties du modèle : ce fichier est le **chef d'orchestre**, le seul endroit qui appelle tous les autres dans le bon ordre.

| Code | Fait |
|---|---|
| `ELO_JSON` | chemin de `eeelo_final.json`, les notes de départ |
| `STAGES = ("top8", "top24", "r16", "qf", "sf", "final", "winner")` | les colonnes du tableau des chances |
| `PARALLEL_FROM = 2000` | à partir de ce nombre de saisons, utiliser plusieurs processus |

---

## 2. `SimConfig(method, expert, seed, runs)` : les choix de l'utilisateur

**Arguments :** `method` : `str`, une des `knockout.METHODS`. `expert` : `bool`, écrire le journal. `seed` : n'importe quelle valeur, ou `None` pour une nouvelle. `runs` : `int`, seulement gardé.

```python
        if method not in knockout.METHODS:
            raise ValueError(f"method must be one of {knockout.METHODS}")
        self.method = method
        self.expert = expert
```

- Refuse une méthode inconnue le plus tôt possible, avant le début de toute saison.

```python
        ranint = random.randint(-400, 400)
        self.seed = random.random() + ranint if seed is None else seed
```

- Sans graine, une nouvelle est fabriquée avec le générateur partagé de Python : un nombre décimal entre −400 et 401, par exemple 137.52.
- **Bug connu :** la première ligne s'exécute **même quand une graine est donnée**, donc chaque `SimConfig` consomme pour rien un nombre du générateur partagé. La déplacer dans le cas « pas de graine » corrigerait cela.

---

## 3. `Resources(model, sampler, ratings)` : les trois fichiers, lus une fois

**Arguments :** `model` : un `MatchModel` ou `None`. `sampler` : un `ScorelineSampler` ou `None`. `ratings` : `dict` ou `None`. `None` veut dire « le lire sur le disque ».

```python
        self.model = model or MatchModel.load()
        self.sampler = sampler or ScorelineSampler.load()
```

- `a or b` donne `a` s'il contient quelque chose, sinon `b` : une façon courte d'écrire « utiliser ce qui a été donné, ou charger la valeur par défaut ». Le chargement n'a lieu que si rien n'a été donné.

```python
        if ratings is None:
            ratings = {c: float(r) for c, r in
                       json.loads(ELO_JSON.read_text(encoding="utf-8")).items()}
        self.ratings = ratings
        self._seeds = {}
```

- Lit les 984 notes et transforme chacune en `float`.
- `_seeds` est une mémoire vide pour `seeds_for` ci-dessous.

```python
    def seeds_for(self, clubs):
        key = tuple(clubs)
        if key not in self._seeds:
            self._seeds[key] = seed_ratings(clubs, self.ratings)
        seeds, resolutions = self._seeds[key]
        return dict(seeds), resolutions
```

- Trouve les notes des clubs du tirage **une fois** par liste de clubs et s'en souvient (**mémoïsation**). Faire correspondre les noms prenait 60 % du temps d'un Monte Carlo quand c'était refait à chaque saison.
- `tuple(clubs)` sert de clé car une liste ne peut pas être une clé de dictionnaire (elle pourrait changer), alors qu'un tuple le peut.
- `dict(seeds)` renvoie une **copie**, pour qu'une saison qui change les notes ne puisse pas changer celles gardées en mémoire.

**En une ligne :** garde le modèle de match, la table des scores et les notes, et donne à chaque club sa note de départ sans refaire le travail.

---

## 4. `seed_ratings(clubs, ratings)`

```python
    resolutions = resolve_all(clubs, ratings.keys())
    seeds = {}
    for res in resolutions:
        seeds[res.club] = ratings[res.key] if res.key is not None else DEFAULT_ELO
    return seeds, resolutions
```

- Demande à `names.py` de relier chaque nom des chapeaux à un nom du fichier des notes ([`names_code.md`](names_code.md)).
- Chaque club reçoit sa note, ou 1500 s'il est introuvable. `"Bayern Munich" -> "Bayern München" -> 1811.07`.

**En une ligne :** transforme les noms des chapeaux en `{club: note}`, plus la fiche de la façon dont chaque nom a été relié.

---

## 5. `SimulationResult` et `stage_reached`

```python
    def __init__(self, **kw):
        for name in self.__slots__:
            setattr(self, name, kw.get(name))
```

- `**kw` rassemble tous les arguments nommés dans un dictionnaire. La boucle copie chaque argument permis sur l'objet avec `setattr`, et met `None` pour ceux qui manquent.

```python
        for row in self.table:
            reached[row.club] = "top24" if row.rank <= 24 else "league"
            if row.rank <= 8:
                reached[row.club] = "top8"
```

- Dans `stage_reached` : d'abord, le point le plus loin de chaque club après la phase de ligue : éliminé (`"league"`), top 24 ou top 8.

```python
        for stage in ("r16", "qf", "sf", "final"):
            for tie in self.rounds.get(stage, ()):
                reached[tie.a] = reached[tie.b] = stage
        reached[self.champion] = "winner"
```

- Puis, tour par tour, les deux clubs de chaque confrontation sont marqués comme l'ayant atteint ; un tour plus loin écrase le précédent. Enfin le champion est marqué `"winner"`.
- `self.rounds.get(stage, ())` donne un tuple vide si un tour manque, donc la boucle ne fait simplement rien.

**En une ligne :** renvoie, pour chaque club, le tour le plus loin qu'il a atteint dans cette saison.

---

## 6. `simulate(comp, teams, matchdays, config, resources)` : une saison

**Arguments :** `comp` : `str`, `"UCL"`, `"UEL"` ou `"UECL"`. `teams` : `dict`, le tirage. `matchdays` : `list` de journées. `config` : `SimConfig` ou `None`. `resources` : `Resources` ou `None`.

```python
    config = config or SimConfig()
    res = resources or Resources()
    t0 = time.perf_counter()
```

- Des valeurs par défaut si rien n'est donné, et une heure de départ pour mesurer la saison.

```python
    clubs = list(teams)
    seeds, resolutions = res.seeds_for(clubs)
    k_table, k_settings = load_k_table(comp)
```

- `list(teams)` donne les noms des clubs dans l'ordre des chapeaux (un dictionnaire garde l'ordre dans lequel les clés ont été ajoutées).
- Les notes de départ, et le $K$ de chaque tour pour cette compétition.

```python
    engine = MatchEngine(res.model, res.sampler, seeds, k_table,
                         random.Random(config.seed), expert=config.expert,
                         k_settings=k_settings)
```

- Un seul moteur pour toute la saison, avec **un seul** générateur de hasard privé créé à partir de la graine. Chaque choix au hasard de la saison en vient, c'est pourquoi la même graine rejoue toujours la même saison.

```python
    warnings = [f"{r.club}: not found in the Elo file, starting at {DEFAULT_ELO:.0f}"
                for r in resolutions if r.key is None]
```

- Un avertissement par club dont le nom n'a pas pu être relié ; l'appli les affiche, donc un club manquant ne passe jamais inaperçu.

```python
    league = league_phase.play_league_phase(engine, matchdays)
    table = league_phase.build_table(clubs, league, seeds)
    rounds = knockout.play_knockout(engine, table, config.method)
    champion = rounds["final"][0].winner
```

- La saison elle-même en quatre lignes : phase de ligue, classement, tours à élimination directe, champion. (En mode expert, le vrai code écrit aussi le classement et les explications des égalités dans le journal entre la deuxième et la troisième ligne.)
- `build_table` reçoit les notes **de départ** `seeds`, pas les actuelles, pour le dernier critère de départage.

```python
    return SimulationResult(
        comp=comp, config=config, clubs=clubs, resolutions=resolutions,
        seed_ratings=seeds, league=league, table=table, rounds=rounds,
        champion=champion, final_ratings=dict(engine.ratings), ...)
```

- Range tout dans une seule fiche, y compris une copie des notes à la fin de la saison et la durée.

**En une ligne :** joue une saison complète à partir d'un tirage et renvoie tout ce qui s'est passé.

---

## 7. `monte_carlo(comp, teams, matchdays, config, runs, resources, progress, workers)`

**Arguments :** comme `simulate`, plus `runs` : `int`, combien de saisons. `progress` : une fonction appelée comme `progress(done, total)`, ou `None`. `workers` : `int` ou `None` pour automatique.

```python
    base = random.Random(config.seed)
    seeds = [base.random() for _ in range(runs)]
    clubs = list(teams)
    days = [sorted(day) for day in matchdays]
```

- Tire **toutes** les graines des saisons avant de jouer quoi que ce soit : la saison `i` utilise toujours `seeds[i]`, quel que soit le processus qui la joue. Le résultat est donc le même avec 1 processus ou 8.
- Trie les matchs de chaque journée une seule fois ici, au lieu d'une fois par saison.

```python
    if workers is None:
        workers = min(os.cpu_count() or 1, 8) if runs >= PARALLEL_FROM else 1
```

- Sous 2 000 saisons, un seul processus (démarrer des processus a un coût). Au-dessus, un par cœur, au plus 8. `os.cpu_count() or 1` protège contre un ordinateur qui ne donne pas son nombre de cœurs.

```python
    if workers > 1:
        try:
            counts, points = _mc_parallel(comp, clubs, days, config.method, seeds,
                                          workers, progress)
        except Cancelled:
            raise
        except Exception:
            counts = points = None
```

- Essaie la voie parallèle. Si l'utilisateur a appuyé sur Annuler, `Cancelled` est transmis (`raise` sans rien relance la même erreur). Toute autre erreur (par exemple des processus qui ne démarrent pas) est attrapée, et le code se replie sur un seul processus.
- L'ordre des deux blocs `except` compte : Python utilise le premier qui correspond, donc `Cancelled` doit venir avant le `Exception` général.

```python
    if counts is None:
        res = resources or Resources()
        counts, points = _mc_block(comp, clubs, days, config.method, seeds, res,
                                   progress, runs)
    return MonteCarloResult(comp, runs, counts, points, time.perf_counter() - t0, config)
```

- Voie à un seul processus : jouer toutes les saisons ici. Puis ranger les comptes dans un objet résultat.

**En une ligne :** joue `runs` saisons, dans un ou plusieurs processus, et renvoie combien de fois chaque club a atteint chaque tour.

---

## 8. `_mc_block(comp, clubs, days, method, seeds, res, progress, total)` : compter

```python
    counts = {club: dict.fromkeys(STAGES, 0) for club in clubs}
    points = dict.fromkeys(clubs, 0)
```

- Un compteur par club et par tour, tous à 0. `dict.fromkeys(STAGES, 0)` donne `{"top8": 0, "top24": 0, ...}`. Sans danger car 0 est un nombre ; `dict.fromkeys(STAGES, [])` donnerait **la même** liste à toutes les clés.

```python
    chain = ("top24", "r16", "qf", "sf", "final", "winner")
    upto = {stage: chain[:i + 1] for i, stage in enumerate(chain)}
    upto["top8"] = upto["top24"]
```

- `upto[stage]` liste chaque tour qu'un club a atteint s'il est arrivé à `stage` : `upto["sf"] = ("top24", "r16", "qf", "sf")`. `chain[:i + 1]` est une **tranche**, les `i + 1` premiers éléments.
- Le « top 8 » n'est pas dans la chaîne (un club peut atteindre les huitièmes par les barrages sans être dans le top 8), donc il compte ici comme « top 24 » et il est ajouté à part plus bas.

```python
    for i, seed in enumerate(seeds):
        run_cfg = SimConfig(method, expert=False, seed=seed)
        result = simulate(comp, clubs, days, run_cfg, res)
```

- Une saison par graine, sans journal (il ne ferait que ralentir).

```python
        for row in result.table:
            points[row.club] += row.points
            if row.rank <= 8:
                counts[row.club]["top8"] += 1
```

- Additionne les points de chaque club en phase de ligue (pour afficher la moyenne plus tard) et compte les places dans le top 8.

```python
        for club, stage in result.stage_reached().items():
            for s in upto.get(stage, ()):
                counts[club][s] += 1
        if progress is not None:
            progress(i + 1, total or len(seeds))
```

- Un demi-finaliste ajoute 1 au top 24, aux huitièmes, aux quarts et aux demies. Un club éliminé en phase de ligue (`"league"`) n'est pas dans `upto`, donc `get` renvoie un tuple vide et rien n'est ajouté.
- Signale l'avancement après chaque saison. Si l'utilisateur annule, la fonction `progress` lève `Cancelled`, ce qui arrête la boucle de l'extérieur : la boucle n'a pas besoin de son propre drapeau d'arrêt.

**En une ligne :** joue une saison par graine et compte, pour chaque club, les tours atteints et ses points en phase de ligue.

---

## 9. `_mc_parallel(comp, clubs, days, method, seeds, workers, progress)`

```python
    from concurrent.futures import ProcessPoolExecutor, as_completed
    size = max(50, len(seeds) // (workers * 4))
    chunks = [seeds[i:i + size] for i in range(0, len(seeds), size)]
```

- Importé dans la fonction : seulement utile pour les gros lancements.
- Coupe les graines en paquets d'environ un quart de la part de chaque processus (au moins 50), pour que la barre de progression bouge plusieurs fois. 10 000 saisons sur 2 processus : des paquets de 1 250.

```python
    pool = ProcessPoolExecutor(max_workers=workers, initializer=_mc_worker_init)
    try:
        futures = [pool.submit(_mc_worker, (comp, clubs, days, method, chunk))
                   for chunk in chunks]
```

- Démarre les processus. `initializer=_mc_worker_init` s'exécute une fois dans chaque nouveau processus et charge ses propres `Resources` depuis le disque. **Bug connu :** cela veut dire que les notes personnalisées données à `monte_carlo` sont ignorées par les processus.
- `pool.submit` envoie un paquet au groupe de processus et renvoie un **future**, une promesse de résultat qui existera plus tard.

```python
        for fut in as_completed(futures):
            n, (c, p) = fut.result()
            for club in clubs:
                points[club] += p[club]
```

- `as_completed` donne chaque future dès qu'il est fini, dans n'importe quel ordre, donc les comptes sont fusionnés le plus tôt possible. Le vrai code ajoute ensuite le compte de chaque tour de la même façon.

```python
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
```

- `finally` s'exécute que la boucle se soit finie normalement, ait été annulée, ou ait échoué. `cancel_futures=True` abandonne les paquets pas encore commencés, et `wait=False` rend la main tout de suite, pour qu'Annuler paraisse immédiat.
- Un bloc `with ProcessPoolExecutor() as pool:` n'a pas été utilisé exprès : en sortir attend la fin de chaque tâche, ce qui ferait attendre Annuler jusqu'à la fin de tout le Monte Carlo.

**En une ligne :** répartit les saisons sur plusieurs processus et fusionne leurs comptes au fur et à mesure.

---

## 10. Export en texte et en-tête du journal

| Fonction | Fait |
|---|---|
| `summary_lines(result)` | la saison en texte : une ligne d'en-tête, les avertissements, le classement, chaque tour, le champion |
| `describe_tie(tie)` | une ligne par confrontation, par exemple `Atalanta 0-0 Arsenal  \|  Arsenal 0-0 Atalanta  (agg 0-0, aet 1-0)  ->  Arsenal` |
| `write_log(result, dest_dir, stamp)` | écrit le résumé, puis le journal expert, dans `data/processed/sim_UCL_<date-heure>.txt`, avec `encoding="utf-8"` pour que des noms comme « Başakşehir » soient bien enregistrés sous Windows |
| `_log_header(...)` | en mode expert, écrit les nombres du modèle, la table de scores utilisée, le $K$ de chaque tour, et la note de départ de chaque club avec la façon dont son nom a été relié |
| `MonteCarloResult.rows()` | transforme les comptes en chances, triées par chance de gagner, puis d'atteindre la finale, etc. |
| `Cancelled` | une classe d'erreur vide utilisée seulement comme signal « stop » |
