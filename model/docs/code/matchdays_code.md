# `matchdays_ucl.py` and `matchdays_uecl.py`, line by line

> This page walks through the code of the matchday planner. For the idea (free days, fewest first, undo, restart), read [`../matchdays.md`](../matchdays.md) first.

*Version française : [plus bas](#matchdays_uclpy-et-matchdays_ueclpy-ligne-par-ligne).*

## How to read this page

- Each function starts with its **arguments**.
- The code comes in groups of 2 to 4 lines, each followed by bullets: what, why, and which general idea.
- Each function ends with **In one line**.

---

## 1. The imports

```python
import random
import time
from collections import defaultdict
```

- `random` (comes with Python): `random.Random` gives private random generators; `shuffle` mixes the free days.
- `time` (comes with Python): only for the demo at the bottom.
- `defaultdict` (from `collections`): `defaultdict(set)` gives an empty set for any club seen for the first time, so `busy[club].add(day)` never needs a check first.

```python
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
from model.draw_ucl import generate_draw
```

- `sys.path` is the list of folders Python searches when it imports something. Adding the project folder lets this file be run directly (`python model/matchdays_ucl.py`) and still find `model.draw_ucl`.
- `generate_draw` (from `model.draw_ucl`) is only used by the demo at the bottom of the file.

---

## 2. `_schedule_matchdays_once(all_matches, num_matchdays, rng, budget)`: one attempt

**Arguments:** `all_matches`: `list` of `(home, away)` tuples, every match of the draw. `num_matchdays`: `int`, 8 (or 6). `rng`: `random.Random`. `budget`: a `list` holding one number, the steps left. The underscore at the start of the name means "for use inside this file".

```python
    remaining = set(all_matches)
    busy = defaultdict(set)
    assigned = {}
```

- `remaining`: the matches not placed yet. A set, so removing and adding one is instant.
- `busy`: for each club, the set of days on which it already plays. `busy["Liverpool"]: set() -> {0}` once Liverpool are placed on day 1 (days are numbered from 0 inside the code).
- `assigned`: the answer being built, match to day.

```python
    def options(match):
        home, away = match
        return [d for d in range(num_matchdays)
                if d not in busy[home] and d not in busy[away]]
```

- An **inner function**: it is defined inside `_schedule_matchdays_once`, so it can read `busy` and `num_matchdays` directly without receiving them as arguments. This is called a **closure**.
- It returns the free days of one match: days on which neither club is busy. With Liverpool busy on day 0 and Juventus busy on day 1: `options(("Liverpool", "Juventus")) -> [2, 3, 4, 5, 6, 7]`.

```python
    def backtrack():
        if not remaining:
            return True
        budget[0] -= 1
        if budget[0] < 0:
            return False
```

- Another inner function, the recursive search. **Base case**: no match left means success.
- Each call spends one step. The budget is a one-element list so that every level of the recursion changes the same number (a plain `int` would only be changed locally).

```python
        chosen, choices = None, None
        for match in sorted(remaining):
            current = options(match)
            if choices is None or len(current) < len(choices):
                chosen, choices = match, current
                if len(current) <= 1:
                    break
```

- Finds the match with the fewest free days: **most constrained first**. As soon as one has 0 or 1, the scan stops early, since nothing can be better.
- `sorted(remaining)` gives the same order in every run (a set of text tuples would not), so the same seed gives the same calendar. The file's comment adds that this order also happened to need about half as many steps as another ordering that was tried.

```python
        if not choices:
            return False
        home, away = chosen
        remaining.discard(chosen)
        days = list(choices)
        rng.shuffle(days)
```

- A match with no free day is a dead end: report failure so the caller can undo.
- Otherwise, remove the match from `remaining` and shuffle a copy of its free days: the only random part of the planner.

```python
        for day in days:
            busy[home].add(day)
            busy[away].add(day)
            assigned[chosen] = day
```

- Tries each free day in turn: marks both clubs busy that day and records the answer.

```python
            if backtrack():
                return True
            del assigned[chosen]
            busy[home].discard(day)
            busy[away].discard(day)
```

- Goes deeper (**recursion**). If the rest succeeds, success travels back up.
- If not, it undoes exactly what it did (**backtracking**), and the loop tries the next day.

```python
        remaining.add(chosen)
        return False

    return assigned if backtrack() else None
```

- No day worked: put the match back and report failure.
- The last line starts the search and returns the full answer `{match: day}`, or `None` if this attempt failed.

**In one line:** tries once to give every match a day so that no club plays twice on a day; returns `{match: day}` or `None`.

---

## 3. `generate_matchdays(teams, *, seed, node_budget, max_attempts)`: the entry point

**Arguments:** `teams`: `dict`, a finished draw. `seed`: any value `random.Random` accepts, `None` for a fresh one. `node_budget`: `int`, steps per attempt (200 000). `max_attempts`: `int`, how many fresh starts (30). The `*` makes the last three keyword-only.

```python
    if seed is None:
        seed = random.random()
    all_matches = [(home, away) for home, data in teams.items() for away in data['home']]
```

- A fresh random seed if none is given.
- Lists every match once, from the host's side: for each club, each club it hosts. 144 matches for the Champions League.

```python
    sample = next(iter(teams.values()))
    num_matchdays = len(sample['home']) + len(sample['away'])
```

- Takes any one club (`next(iter(...))` gives the first value of a dictionary) and counts its matches: 4 + 4 = 8, or 3 + 3 = 6 for the Conference League.
- The number of days is read from the draw instead of written by hand, so the same function works for all three competitions.

```python
    rng = random.Random(seed)
    for _ in range(1, max_attempts + 1):
        result = _schedule_matchdays_once(
            all_matches, num_matchdays, random.Random(rng.random()), [node_budget])
```

- One "parent" generator made from the seed gives a new seed to each attempt: `random.Random(rng.random())`. Each attempt makes different random choices, but the whole sequence of attempts still depends only on the one seed, so the result is **reproducible**.
- Each attempt gets a fresh budget.

```python
        if result is not None:
            matchdays = [[] for _ in range(num_matchdays)]
            for match, day in result.items():
                matchdays[day].append(match)
            return matchdays
```

- On success, turns `{match: day}` into a list of days, each a list of matches: `[[18 matches], [18 matches], ...]`.
- `[[] for _ in range(8)]` builds 8 **different** empty lists. Writing `[[]] * 8` instead would build 8 names for the **same** list, a classic Python trap.

```python
    raise RuntimeError(f'no valid {num_matchdays}-:matchday schedule found in {max_attempts} attempts')
```

- After 30 failed attempts, a clear error. (The `-:` is a typo; it should read `-matchday`.)

**In one line:** takes a finished draw and a seed, and returns the matches split into 8 (or 6) days, every club once per day.

---

## 4. `verify_matchdays(teams, matchdays)`: the Conference League check

**Arguments:** `teams`: the draw. `matchdays`: the calendar to check.

```python
    if len(matchdays) != MATCHDAYS:
        raise AssertionError(...)
    scheduled = Counter()
```

- First, exactly 6 days.
- `Counter` (from `collections`) is a dictionary that counts things: `scheduled[match] += 1` for every match seen, starting from 0.

```python
    for day_number, day in enumerate(matchdays, start=1):
        if len(day) != MATCHES_PER_DAY:
            raise AssertionError(...)
        playing = Counter()
```

- Each day must hold 18 matches. `playing` counts how many times each club appears on this day.

```python
        for home, away in day:
            playing[home] += 1
            playing[away] += 1
            scheduled[(home, away)] += 1
```

- Counts both clubs of every match, and the match itself.

```python
        if len(playing) != len(teams):
            raise AssertionError(...)
        twice = [club for club, n in playing.items() if n > 1]
```

- All 36 clubs must appear that day, and none more than once.

```python
    drawn = Counter(fixtures(teams))
    if scheduled != drawn:
```

- Last check: the calendar holds exactly the matches of the draw. Comparing two `Counter`s catches a missing match, an invented match and a match placed twice, all at once.
- Like the draw's checker, it rebuilds everything from the finished calendar and never trusts the search's own notes.

**In one line:** rechecks a Conference League calendar from scratch and raises an error at the first broken rule.

---

## 5. `generate_uecl_matchdays(*, seed, teams, verify_result, pots, countries)`

| Line | Does |
|---|---|
| `if teams is None: teams = generate_draw(...)` | draws a new Conference League draw, unless the app passes the one it has already animated |
| `matchdays = generate_matchdays(teams, seed=seed)` | reuses the same planner as the Champions League; no second copy of the search |
| `if verify_result: verify_matchdays(teams, matchdays)` | runs the check of part 4 |
| `return teams, matchdays` | gives back both the draw and its calendar |

---
---

# `matchdays_ucl.py` et `matchdays_uecl.py`, ligne par ligne

> Cette page explique le code du planificateur des journées. Pour l'idée (jours libres, le moins d'abord, défaire, recommencer), lis d'abord [`../matchdays.md`](../matchdays.md#le-planificateur-des-journées--quel-match-se-joue-quel-jour).

## Comment lire cette page

- Chaque fonction commence par ses **arguments**.
- Le code vient en groupes de 2 à 4 lignes, chacun suivi de points : quoi, pourquoi, et quelle idée générale.
- Chaque fonction se termine par **En une ligne**.

---

## 1. Les imports

```python
import random
import time
from collections import defaultdict
```

- `random` (fourni avec Python) : `random.Random` donne des générateurs de hasard privés ; `shuffle` mélange les jours libres.
- `time` (fourni avec Python) : seulement pour la démo en bas du fichier.
- `defaultdict` (de `collections`) : `defaultdict(set)` donne un ensemble vide pour tout club vu pour la première fois, donc `busy[club].add(day)` n'a jamais besoin d'une vérification avant.

```python
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
from model.draw_ucl import generate_draw
```

- `sys.path` est la liste des dossiers où Python cherche quand il importe quelque chose. Ajouter le dossier du projet permet de lancer ce fichier directement (`python model/matchdays_ucl.py`) tout en trouvant `model.draw_ucl`.
- `generate_draw` (de `model.draw_ucl`) ne sert qu'à la démo en bas du fichier.

---

## 2. `_schedule_matchdays_once(all_matches, num_matchdays, rng, budget)` : un essai

**Arguments :** `all_matches` : `list` de tuples `(domicile, extérieur)`, tous les matchs du tirage. `num_matchdays` : `int`, 8 (ou 6). `rng` : `random.Random`. `budget` : une `list` qui contient un nombre, les pas restants. Le tiret bas au début du nom veut dire « à utiliser dans ce fichier ».

```python
    remaining = set(all_matches)
    busy = defaultdict(set)
    assigned = {}
```

- `remaining` : les matchs pas encore placés. Un ensemble, pour qu'en retirer ou en ajouter un soit immédiat.
- `busy` : pour chaque club, l'ensemble des jours où il joue déjà. `busy["Liverpool"] : set() -> {0}` une fois Liverpool placé le jour 1 (les jours sont numérotés à partir de 0 dans le code).
- `assigned` : la réponse en construction, match vers jour.

```python
    def options(match):
        home, away = match
        return [d for d in range(num_matchdays)
                if d not in busy[home] and d not in busy[away]]
```

- Une **fonction interne** : elle est définie dans `_schedule_matchdays_once`, donc elle peut lire `busy` et `num_matchdays` directement sans les recevoir en arguments. On appelle cela une **fermeture** (*closure*).
- Elle renvoie les jours libres d'un match : les jours où aucun des deux clubs n'est occupé. Avec Liverpool occupé le jour 0 et la Juventus le jour 1 : `options(("Liverpool", "Juventus")) -> [2, 3, 4, 5, 6, 7]`.

```python
    def backtrack():
        if not remaining:
            return True
        budget[0] -= 1
        if budget[0] < 0:
            return False
```

- Une autre fonction interne, la recherche récursive. **Cas de base** : plus aucun match veut dire réussite.
- Chaque appel dépense un pas. Le budget est une liste d'un élément pour que chaque niveau de la récursion modifie le même nombre (un simple `int` ne serait modifié que localement).

```python
        chosen, choices = None, None
        for match in sorted(remaining):
            current = options(match)
            if choices is None or len(current) < len(choices):
                chosen, choices = match, current
                if len(current) <= 1:
                    break
```

- Trouve le match qui a le moins de jours libres : **le plus contraint d'abord**. Dès qu'un match en a 0 ou 1, le parcours s'arrête tôt, car on ne peut pas trouver mieux.
- `sorted(remaining)` donne le même ordre à chaque lancement (un ensemble de tuples de texte, non), donc la même graine donne le même calendrier. Le commentaire du fichier ajoute que cet ordre a aussi demandé environ deux fois moins de pas qu'un autre ordre essayé.

```python
        if not choices:
            return False
        home, away = chosen
        remaining.discard(chosen)
        days = list(choices)
        rng.shuffle(days)
```

- Un match sans jour libre est une impasse : signaler l'échec pour que l'appelant puisse défaire.
- Sinon, retirer le match de `remaining` et mélanger une copie de ses jours libres : la seule partie au hasard du planificateur.

```python
        for day in days:
            busy[home].add(day)
            busy[away].add(day)
            assigned[chosen] = day
```

- Essaie chaque jour libre à tour de rôle : marque les deux clubs occupés ce jour-là et note la réponse.

```python
            if backtrack():
                return True
            del assigned[chosen]
            busy[home].discard(day)
            busy[away].discard(day)
```

- Va plus loin (**récursion**). Si la suite réussit, la réussite remonte.
- Sinon, défait exactement ce qu'elle a fait (**retour sur trace**), et la boucle essaie le jour suivant.

```python
        remaining.add(chosen)
        return False

    return assigned if backtrack() else None
```

- Aucun jour n'a marché : remettre le match et signaler l'échec.
- La dernière ligne lance la recherche et renvoie la réponse complète `{match: jour}`, ou `None` si cet essai a échoué.

**En une ligne :** essaie une fois de donner un jour à chaque match pour qu'aucun club ne joue deux fois le même jour ; renvoie `{match: jour}` ou `None`.

---

## 3. `generate_matchdays(teams, *, seed, node_budget, max_attempts)` : le point d'entrée

**Arguments :** `teams` : `dict`, un tirage fini. `seed` : toute valeur que `random.Random` accepte, `None` pour une nouvelle. `node_budget` : `int`, pas par essai (200 000). `max_attempts` : `int`, nombre de nouveaux départs (30). Le `*` oblige à donner les trois derniers par leur nom.

```python
    if seed is None:
        seed = random.random()
    all_matches = [(home, away) for home, data in teams.items() for away in data['home']]
```

- Une nouvelle graine au hasard si aucune n'est donnée.
- Liste chaque match une fois, du côté du club qui reçoit : pour chaque club, chaque club qu'il reçoit. 144 matchs pour la Ligue des champions.

```python
    sample = next(iter(teams.values()))
    num_matchdays = len(sample['home']) + len(sample['away'])
```

- Prend un club au hasard (`next(iter(...))` donne la première valeur d'un dictionnaire) et compte ses matchs : 4 + 4 = 8, ou 3 + 3 = 6 pour la Ligue Conférence.
- Le nombre de journées est lu dans le tirage au lieu d'être écrit à la main, donc la même fonction marche pour les trois compétitions.

```python
    rng = random.Random(seed)
    for _ in range(1, max_attempts + 1):
        result = _schedule_matchdays_once(
            all_matches, num_matchdays, random.Random(rng.random()), [node_budget])
```

- Un générateur « parent » créé à partir de la graine donne une nouvelle graine à chaque essai : `random.Random(rng.random())`. Chaque essai fait d'autres choix au hasard, mais toute la suite des essais ne dépend que de la graine, donc le résultat est **reproductible**.
- Chaque essai reçoit un budget neuf.

```python
        if result is not None:
            matchdays = [[] for _ in range(num_matchdays)]
            for match, day in result.items():
                matchdays[day].append(match)
            return matchdays
```

- En cas de réussite, transforme `{match: jour}` en liste de journées, chacune une liste de matchs : `[[18 matchs], [18 matchs], ...]`.
- `[[] for _ in range(8)]` construit 8 listes vides **différentes**. Écrire `[[]] * 8` construirait 8 noms pour la **même** liste, un piège classique de Python.

```python
    raise RuntimeError(f'no valid {num_matchdays}-:matchday schedule found in {max_attempts} attempts')
```

- Après 30 essais ratés, une erreur claire. (Le `-:` est une faute de frappe ; il faudrait `-matchday`.)

**En une ligne :** prend un tirage fini et une graine, et renvoie les matchs répartis en 8 (ou 6) journées, chaque club une fois par journée.

---

## 4. `verify_matchdays(teams, matchdays)` : la vérification de la Ligue Conférence

**Arguments :** `teams` : le tirage. `matchdays` : le calendrier à vérifier.

```python
    if len(matchdays) != MATCHDAYS:
        raise AssertionError(...)
    scheduled = Counter()
```

- D'abord, exactement 6 journées.
- `Counter` (de `collections`) est un dictionnaire qui compte : `scheduled[match] += 1` pour chaque match vu, en partant de 0.

```python
    for day_number, day in enumerate(matchdays, start=1):
        if len(day) != MATCHES_PER_DAY:
            raise AssertionError(...)
        playing = Counter()
```

- Chaque journée doit contenir 18 matchs. `playing` compte combien de fois chaque club apparaît ce jour-là.

```python
        for home, away in day:
            playing[home] += 1
            playing[away] += 1
            scheduled[(home, away)] += 1
```

- Compte les deux clubs de chaque match, et le match lui-même.

```python
        if len(playing) != len(teams):
            raise AssertionError(...)
        twice = [club for club, n in playing.items() if n > 1]
```

- Les 36 clubs doivent apparaître ce jour-là, et aucun plus d'une fois.

```python
    drawn = Counter(fixtures(teams))
    if scheduled != drawn:
```

- Dernière vérification : le calendrier contient exactement les matchs du tirage. Comparer deux `Counter` attrape d'un coup un match manquant, un match inventé et un match placé deux fois.
- Comme le vérificateur du tirage, il reconstruit tout à partir du calendrier fini et ne fait jamais confiance aux notes de la recherche.

**En une ligne :** revérifie un calendrier de Ligue Conférence depuis zéro et lève une erreur à la première règle cassée.

---

## 5. `generate_uecl_matchdays(*, seed, teams, verify_result, pots, countries)`

| Ligne | Fait |
|---|---|
| `if teams is None: teams = generate_draw(...)` | fait un nouveau tirage de Ligue Conférence, sauf si l'appli donne celui qu'elle a déjà animé |
| `matchdays = generate_matchdays(teams, seed=seed)` | réutilise le même planificateur que la Ligue des champions ; pas de deuxième copie de la recherche |
| `if verify_result: verify_matchdays(teams, matchdays)` | lance la vérification de la partie 4 |
| `return teams, matchdays` | rend à la fois le tirage et son calendrier |
