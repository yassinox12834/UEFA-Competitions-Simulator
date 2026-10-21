# `draw_ucl.py` and `draw_uecl.py`, line by line

> This page walks through the code of the draw. For the idea (slots, hardest first, undo, restart, check), read [`../draw.md`](../draw.md) first.

*Version française : [plus bas](#draw_uclpy-et-draw_ueclpy-ligne-par-ligne).*

## How to read this page

- Each function starts with its **arguments**.
- The code comes in groups of 2 to 4 lines, each followed by bullets: what, why, and which general idea.
- Each function ends with **In one line**.
- Parts 1 to 10 follow `draw_ucl.py` (Champions League and Europa League). Part 11 shows what `draw_uecl.py` does differently.

---

## 1. The imports

```python
import csv
import random
import time
from collections import defaultdict
```

- `csv` (comes with Python) reads the country of each club from a CSV file.
- `random` (comes with Python) gives `random.Random`, a random generator that belongs to this draw only, and its `shuffle` method.
- `time` (comes with Python) is only used by the demo at the bottom, to time a draw.
- `defaultdict` (from `collections`, comes with Python) is a dictionary that invents a starting value for a missing key: `defaultdict(int)` reads a missing key as 0, so counting with `+= 1` works without checking first.

```python
from functools import lru_cache
from itertools import chain
from pathlib import Path
```

- `lru_cache` (from `functools`) remembers what a function returned, so a second call with the same arguments returns the saved answer at once: **memoisation**. Used to read the country file only once per competition.
- `chain` (from `itertools`) walks through several lists one after the other as if they were one, without building a new list.
- `Path` (from `pathlib`) builds the path to the country file.

---

## 2. The settings

| Code | Does | Example value |
|---|---|---|
| `BASE_DIR = Path(__file__).resolve().parents[1]` | the project folder, found from this file's own place | `.../UEFA` |
| `CSV_PATH` | the file with each club's country | `data/processed/countries_filled_25.csv` |
| `MAX_PER_COUNTRY = 2` | most opponents from one country | 2 |
| `MAX_ATTEMPTS = 50` | fresh starts before giving up | 50 |
| `NODE_BUDGET = 200_000` | steps allowed per attempt; `_` is only there to make the number easier to read | 200 000 |
| `POTS_UCL`, `POTS_UEL` | four lists of nine club names each | `['Real Madrid', 'Manchester City', ...]` |
| `POTS_BY_COMP` | picks the right pots from the competition code | `POTS_BY_COMP['UEL']` |

---

## 3. `build_teams(pots, countries)`: one record per club

**Arguments:** `pots`: `list` of `list` of `str`, the pots. `countries`: `dict`, club to country.

```python
    teams = {}
    for pot_number, pot in enumerate(pots, start=1):
        for club in pot:
```

- `enumerate(pots, start=1)` gives each pot with its number, starting at 1 instead of 0, so pot numbers match the ones people use.
- Two nested loops visit every club of every pot: 36 clubs.

```python
            teams[club] = {
                'country': countries[club],
                'pot': pot_number,
                'home': [],
                'away': [],
                'played': set(),
                'counts': defaultdict(int),
            }
    return teams
```

- Each club gets a dictionary: its country and pot (fixed), and four things the search will fill: who it hosts (`home`), who it visits (`away`), everyone it already plays (`played`), and how many opponents per country (`counts`).
- `played` and `counts` repeat information already in `home` and `away`. They exist only for speed: "have we already met?" becomes an instant set lookup, and "how many Spanish opponents?" an instant dictionary read. Keeping a quick copy of information like this is a form of **caching**.
- `teams["Liverpool"]: {'country': 'England', 'pot': 1, 'home': [], 'away': [], 'played': set(), 'counts': {}}`.

**In one line:** turns the pots and countries into one empty record per club.

---

## 4. `link` and `unlink`: write and erase one match

**Arguments:** `teams`: `dict`, the records. `host_club`, `guest_club`: `str`, the home and away clubs.

```python
    host['home'].append(guest_club)
    guest['away'].append(host_club)
    host['played'].add(guest_club)
    guest['played'].add(host_club)
```

- Writes the match in **both** clubs' records at once, which is how rule 6 (both lists agree) is kept: the code never writes one side without the other.
- Liverpool hosts Juventus: `teams["Liverpool"]["home"]: [] -> ["Juventus"]`, `teams["Juventus"]["away"]: [] -> ["Liverpool"]`.

```python
    host['counts'][guest['country']] += 1
    guest['counts'][host['country']] += 1
```

- Each club counts one more opponent from the other's country: `teams["Liverpool"]["counts"]["Italy"]: 0 -> 1`. Thanks to `defaultdict(int)`, a country never seen starts at 0.

```python
def unlink(teams, host_club, guest_club):
    host['home'].pop()
    guest['away'].pop()
    host['played'].discard(guest_club)
```

- `unlink` does exactly the opposite, in the same order, so `unlink` after `link` leaves everything as it was.
- `.pop()` removes the **last** item of the list. That is correct because the search always undoes the most recent match first (last in, first out, like a stack of plates). It is also faster than `.remove(club)`, which would search the list.
- The two count lines below it subtract 1 again.

**In one line:** `link` records a match in both clubs' records; `unlink` takes it back.

---

## 5. `options(slot, teams, slots, pots, constraints)`: who can fill this slot?

**Arguments:** `slot`: `tuple` `(club, pot, is_home)`, the game to fill. `teams`: the records. `slots`: `set` of the slots still open. `pots`: the pots. `constraints`: `set` of `(host, guest)` pairs the user banned.

```python
    club, pot, is_home = slot
    me = teams[club]
    valid = []
    for other in pots[pot - 1]:
```

- Unpacks the slot. `('Liverpool', 2, False)` means "Liverpool still needs to travel to a pot-2 club".
- Only the clubs of the right pot are tried; `pot - 1` because lists start at 0 while pots start at 1.

```python
        if other == club:
            continue
        them = teams[other]
        if them['country'] == me['country']:
            continue
```

- Each test that fails skips this club with `continue` and moves to the next one. The order matters only for speed: cheap tests that fail often come first.
- Test 1: a club cannot play itself (it happens when the slot is against its own pot). Test 2: same country is forbidden (rule 3).

```python
        if (other, me['pot'], not is_home) not in slots:
            continue
        if other in me['played']:
            continue
```

- Test 3: the **mirror** slot, the same game seen from the other club, must still be open. If Liverpool would travel to Juventus, Juventus must still need "host a pot-1 club". This keeps rule 2 for the other club too.
- Test 4: no rematch (rule 5), an instant check thanks to the `played` set.

```python
        if me['counts'][them['country']] >= MAX_PER_COUNTRY:
            continue
        if them['counts'][me['country']] >= MAX_PER_COUNTRY:
            continue
```

- Tests 5 and 6: the country limit (rule 4), on **both** sides. One side is not enough: Barcelona may have met no English club yet while Arsenal has already met 2 Spanish ones; this match would push Arsenal to 3.

```python
        if ((club, other) if is_home else (other, club)) in constraints:
            continue
        valid.append(other)
    return valid
```

- Test 7: the user's bans (rule 7). A ban is an **ordered** pair (host, guest), so the code first builds the pair this game would create: `(club, other)` if `club` is at home, `(other, club)` otherwise.
- A club that passes all seven tests is added to `valid`.

**In one line:** takes one open slot and returns the list of clubs that can legally fill it.

---

## 6. `fill(teams, slots, rng, budget, pots, constraints)`: the search

**Arguments:** `teams`, `slots`, `pots`, `constraints`: as above. `rng`: `random.Random`, the draw's random generator. `budget`: a `list` holding one number, the steps left.

```python
    if not slots:
        return True
    budget[0] -= 1
    if budget[0] < 0:
        return False
```

- If no slot is left, the draw is complete: `True` travels back up through every waiting call. This is the **base case** of a recursive function, the point where it stops calling itself.
- Each call spends one step of the budget. When the budget is gone, this attempt gives up.
- The budget is a list with one number, not a plain number, so that every level of the recursion changes **the same** box. A plain `int` cannot be changed in place: `budget -= 1` inside a call would only change a local copy.

```python
    chosen, choices = None, None
    for slot in sorted(slots):
        current = options(slot, teams, slots, pots, constraints)
        if choices is None or len(current) < len(choices):
```

- Scans every open slot and keeps the one with the fewest possible clubs: the **most constrained first** rule.
- `sorted(slots)` instead of `slots`: a set of text tuples is walked in an order that changes each time Python starts, so without sorting, the same seed could give different draws. Sorting fixes the order: **reproducibility**.

```python
            chosen, choices = slot, current
            if len(current) <= 1:
                break
```

- Remembers the best slot so far. As soon as one has 0 or 1 option, nothing better can be found, so the scan stops early with `break`: this saves up to 288 calls to `options`.

```python
    club, _, is_home = chosen
    me = teams[club]
    slots.discard(chosen)
    rng.shuffle(choices)
```

- Closes the chosen slot, then shuffles its possible clubs with the draw's own generator. This shuffle is the **only** source of randomness in the whole draw.

```python
    for other in choices:
        mirror = (other, me['pot'], not is_home)
        host_club, guest_club = (club, other) if is_home else (other, club)
        link(teams, host_club, guest_club)
        slots.discard(mirror)
```

- Tries each possible club in turn. It works out the mirror slot (the same game for the other club) and who is at home.
- Writes the match with `link` and closes the mirror slot too: one match fills two slots.

```python
        if fill(teams, slots, rng, budget, pots, constraints):
            return True
        slots.add(mirror)
        unlink(teams, host_club, guest_club)
```

- Calls itself on the smaller problem (**recursion**). If the rest of the draw succeeds, success is passed up.
- If not, it undoes this choice exactly (reopens the mirror, erases the match) and the loop tries the next club. This is **backtracking**.

```python
    slots.add(chosen)
    return False
```

- No club worked: reopen the chosen slot so everything is as it was, and tell the caller to try its own next option.

**In one line:** fills every open slot, hardest first, trying clubs in random order and undoing choices that lead to a dead end; returns `True` when the draw is complete.

---

## 7. `draw(teams, rng, pots, constraints)`: up to 50 attempts

**Arguments:** `teams`, `pots`, `constraints`: as above. `rng`: `random.Random`.

```python
    for attempt in range(1, MAX_ATTEMPTS + 1):
        for team in teams.values():
            team['home'].clear()
            team['away'].clear()
```

- Each attempt starts from an empty draw: every list, set and count is cleared (the two lines after these clear `played` and `counts`).
- The random generator is **not** reset, so a new attempt makes different random choices.

```python
        slots = {(club, pot, is_home)
                 for club in teams
                 for pot in range(1, len(pots) + 1)
                 for is_home in (True, False)}
```

- A **set comprehension** builds all 288 slots: every club, every pot, home and away.

```python
        if fill(teams, slots, rng, [NODE_BUDGET], pots, constraints):
            return attempt
    raise RuntimeError(f'no valid draw found in {MAX_ATTEMPTS} attempts{extra}')
```

- Each attempt gets a fresh budget `[200_000]`. On success, it returns the attempt number (useful to measure how often restarts are needed).
- After 50 failures it raises an error; `extra` adds "(k constraint(s) in force)" when the user had bans, so an impossible set of bans can be told apart from a real search failure.

**In one line:** runs the search up to 50 times from scratch, and returns the number of the attempt that worked.

---

## 8. `verify(teams, pots, constraints)`: the independent check

**Arguments:** `teams`: a finished draw. `pots`, `constraints`: as above.

```python
    for club, team in teams.items():
        drawn = list(opponents(team))
        if len(drawn) != 2 * len(pots):
            raise AssertionError(f'{club} has {len(drawn)} matches')
```

- `opponents` (a two-line helper) uses `chain` to join the home and away lists. Rule 1: 8 opponents.
- It reads **only** `home` and `away`, never the `played` and `counts` shortcuts. If a bug had broken a shortcut, a check that trusted it would share the bug; recomputing from the real lists catches it.
- It raises `AssertionError` with `raise` instead of using the `assert` keyword: `python -O` deletes every `assert`, but never a `raise`.

```python
        if len(set(drawn)) != len(drawn):
            raise AssertionError(f'{club} plays someone twice')
        for side in ('home', 'away'):
            pots_played = sorted(teams[other]['pot'] for other in team[side])
```

- Rule 5: turning a list into a set removes duplicates, so a shorter set means someone appears twice.
- Rule 2: the pots of the home opponents, sorted, must be exactly `[1, 2, 3, 4]`, and the same for the away opponents.

```python
        counts = defaultdict(int)
        for other in drawn:
            other_country = teams[other]['country']
            if other_country == team['country']:
```

- Rules 3 and 4, recounted from zero: no same-country opponent, at most 2 per country.

```python
        for other in team['home']:
            if club not in teams[other]['away']:
                raise AssertionError(f'{club} vs {other} is not mirrored')
            if (club, other) in constraints:
```

- Rule 6: every club this club hosts must have this club in its away list. Rule 7: no hosted pair may be a banned pair.

**In one line:** rechecks all 7 rules on the finished draw from the raw lists, and raises an error naming the club at the first broken rule.

---

## 9. `generate_draw(*, comp, seed, verify_result, pots, countries, constraints)`: the entry point

**Arguments:** all keyword-only (the `*` forces `generate_draw(comp='UEL', seed=3)` instead of positional values). `comp`: `'UCL'` or `'UEL'`. `seed`: any value `random.Random` accepts. `verify_result`: `bool`. `pots`, `countries`: optional replacements. `constraints`: a `set` of `(host, guest)` tuples, or `None`.

```python
    if seed is None:
        seed = random.random()
    if pots is None:
        pots = POTS_BY_COMP[comp]
    if countries is None:
        countries = _countries(comp)
```

- Fills in defaults. `seed=None` means "a fresh random draw"; it is computed **inside** the function, so each call gets a new one.
- `_countries(comp)` reads the country file once per competition thanks to `@lru_cache`.

```python
    if constraints is None:
        constraints = frozenset()
    elif not isinstance(constraints, (set, frozenset)):
        raise TypeError(...)
```

- No bans becomes an empty **frozenset** (a set that cannot be changed).
- A list of bans is refused loudly. In Python `('a', 'b') == ['a', 'b']` is `False`, so a ban written as a list would simply never match and never work. Failing early with a clear message is better than a ban that silently does nothing.

```python
    teams = build_teams(pots, countries)
    draw(teams, random.Random(seed), pots, constraints)
    if verify_result:
        verify(teams, pots, constraints)
    return teams
```

- Builds the records, runs the draw with a **private** generator `random.Random(seed)` (other code using `random` cannot disturb it), checks it (about 0.2 ms, so it is always on), and returns the records.

**In one line:** takes a competition, a seed and optional pots, countries and bans, and returns a complete, checked draw.

---

## 10. Small helpers

| Function | Does |
|---|---|
| `load_countries(path, wanted)` | reads the CSV with `encoding='utf-8-sig'` (removes the invisible bytes Excel adds at the start); for clubs not found by exact name, asks `model.names.resolve_all`; raises `ValueError` listing any club still missing |
| `_countries(comp)` | `@lru_cache` wrapper: reads the countries of one competition's clubs once |
| `opponents(team)` | `chain(team['home'], team['away'])`: all opponents in one pass |
| `fixtures(teams)` | `[(club, other) for club ... for other in team['home']]`: the 144 matches, each once, from the host's side |
| `show(teams, pots)` | prints each club with its home and away opponents, sorted by pot |

---

## 11. What `draw_uecl.py` does differently

The Conference League file reuses the same structure. Two parts are new.

### `paired_pot(pot)`

```python
def paired_pot(pot):
    return pot + 1 if pot in (1, 3, 5) else pot - 1
```

- Pot 1 goes with 2, 3 with 4, 5 with 6: `paired_pot(3) = 4`, `paired_pot(4) = 3`.
- A club plays one pot of each pair at home and the other away; this is what guarantees 3 home and 3 away matches.

### The inside of `fill`

```python
    candidates = []
    for is_home in (True, False):
        slot = (club, pot, is_home)
        if slot in slots:
            for other in options(slot, teams, slots, pots, constraints):
                candidates.append((other, is_home))
```

- In the Conference League, a club meets each pot **once**, home or away. So the real question is "who, and in which direction?", and each candidate is a pair `(opponent, at home?)`.
- Both directions are collected, then shuffled together.

```python
    closed = [s for s in ((club, pot, True), (club, pot, False)) if s in slots]
    slots.difference_update(closed)
```

- Both directions of this club against this pot are closed at once, because only one of them will be used.
- `difference_update` removes several items from a set in one call.

```python
        mirror   = (other, me['pot'], not is_home)
        leftover = (other, me['pot'], is_home)
        partner  = (club,  paired_pot(pot), is_home)
        partner2 = (other, paired_pot(me['pot']), not is_home)
```

- A match closes up to four more slots. `mirror`: the same game for the other club. `leftover`: the other club's second direction against our pot (it meets only one club of our pot). `partner`: our slot against the paired pot **in the same direction**, now forbidden, because the paired pot must be played the other way. `partner2`: the same rule for the other club.
- Example: Chelsea (pot 1) hosts Molde (pot 2). Chelsea must now play pot 2's partner... pot 1 is paired with pot 2 itself, so Chelsea's pot-1 game must be away, and Molde's pot-1 game... is this one; Molde's paired pot is pot 1, so its away slot against pot 1 is used here and its pot-2 game must be at home.

```python
        removed = [s for s in (mirror, leftover, partner, partner2) if s in slots]
        slots.difference_update(removed)
        if fill(teams, slots, rng, budget, pots, constraints):
            return True
        slots.update(removed)
```

- Only the slots really open are removed, and exactly those are put back on failure, so undoing leaves the set as it was.

The Conference League file also counts opponents per country by walking through the lists each time (`faced_from`), instead of keeping a `counts` shortcut. It is a little slower (about twice the time of a Champions League draw), but there is no shortcut that could go out of date.

---
---

# `draw_ucl.py` et `draw_uecl.py`, ligne par ligne

> Cette page explique le code du tirage. Pour l'idée (cases, la plus difficile d'abord, défaire, recommencer, vérifier), lis d'abord [`../draw.md`](../draw.md#le-tirage--qui-joue-contre-qui).

## Comment lire cette page

- Chaque fonction commence par ses **arguments**.
- Le code vient en groupes de 2 à 4 lignes, chacun suivi de points : quoi, pourquoi, et quelle idée générale.
- Chaque fonction se termine par **En une ligne**.
- Les parties 1 à 10 suivent `draw_ucl.py` (Ligue des champions et Ligue Europa). La partie 11 montre ce que `draw_uecl.py` fait autrement.

---

## 1. Les imports

```python
import csv
import random
import time
from collections import defaultdict
```

- `csv` (fourni avec Python) lit le pays de chaque club dans un fichier CSV.
- `random` (fourni avec Python) donne `random.Random`, un générateur de hasard qui n'appartient qu'à ce tirage, et sa méthode `shuffle` (mélanger).
- `time` (fourni avec Python) ne sert qu'à la démo en bas du fichier, pour chronométrer un tirage.
- `defaultdict` (de `collections`, fourni avec Python) est un dictionnaire qui invente une valeur de départ pour une clé absente : `defaultdict(int)` lit une clé absente comme 0, donc compter avec `+= 1` marche sans vérifier avant.

```python
from functools import lru_cache
from itertools import chain
from pathlib import Path
```

- `lru_cache` (de `functools`) se souvient de ce qu'une fonction a renvoyé, donc un deuxième appel avec les mêmes arguments renvoie tout de suite la réponse gardée : la **mémoïsation**. Sert à ne lire le fichier des pays qu'une fois par compétition.
- `chain` (de `itertools`) parcourt plusieurs listes l'une après l'autre comme si c'était une seule, sans construire de nouvelle liste.
- `Path` (de `pathlib`) construit le chemin du fichier des pays.

---

## 2. Les réglages

| Code | Fait | Exemple |
|---|---|---|
| `BASE_DIR = Path(__file__).resolve().parents[1]` | le dossier du projet, trouvé à partir de l'emplacement de ce fichier | `.../UEFA` |
| `CSV_PATH` | le fichier avec le pays de chaque club | `data/processed/countries_filled_25.csv` |
| `MAX_PER_COUNTRY = 2` | nombre maximum d'adversaires d'un même pays | 2 |
| `MAX_ATTEMPTS = 50` | nouveaux départs avant d'abandonner | 50 |
| `NODE_BUDGET = 200_000` | pas permis par essai ; le `_` sert seulement à rendre le nombre plus lisible | 200 000 |
| `POTS_UCL`, `POTS_UEL` | quatre listes de neuf noms de clubs chacune | `['Real Madrid', 'Manchester City', ...]` |
| `POTS_BY_COMP` | choisit les bons chapeaux selon le code de la compétition | `POTS_BY_COMP['UEL']` |

---

## 3. `build_teams(pots, countries)` : une fiche par club

**Arguments :** `pots` : `list` de `list` de `str`, les chapeaux. `countries` : `dict`, club vers pays.

```python
    teams = {}
    for pot_number, pot in enumerate(pots, start=1):
        for club in pot:
```

- `enumerate(pots, start=1)` donne chaque chapeau avec son numéro, en partant de 1 au lieu de 0, pour que les numéros correspondent à ceux qu'on utilise d'habitude.
- Deux boucles imbriquées visitent chaque club de chaque chapeau : 36 clubs.

```python
            teams[club] = {
                'country': countries[club],
                'pot': pot_number,
                'home': [],
                'away': [],
                'played': set(),
                'counts': defaultdict(int),
            }
    return teams
```

- Chaque club reçoit un dictionnaire : son pays et son chapeau (fixes), et quatre choses que la recherche va remplir : qui il reçoit (`home`), chez qui il va (`away`), tous ceux qu'il joue déjà (`played`), et combien d'adversaires par pays (`counts`).
- `played` et `counts` répètent une information déjà dans `home` et `away`. Ils n'existent que pour la vitesse : « s'est-on déjà rencontrés ? » devient une recherche immédiate dans un ensemble, et « combien d'adversaires espagnols ? » une lecture immédiate dans un dictionnaire. Garder une copie rapide d'une information comme ça est une forme de **cache**.
- `teams["Liverpool"] : {'country': 'England', 'pot': 1, 'home': [], 'away': [], 'played': set(), 'counts': {}}`.

**En une ligne :** transforme les chapeaux et les pays en une fiche vide par club.

---

## 4. `link` et `unlink` : écrire et effacer un match

**Arguments :** `teams` : `dict`, les fiches. `host_club`, `guest_club` : `str`, le club à domicile et le club à l'extérieur.

```python
    host['home'].append(guest_club)
    guest['away'].append(host_club)
    host['played'].add(guest_club)
    guest['played'].add(host_club)
```

- Écrit le match dans les fiches des **deux** clubs à la fois, et c'est ainsi que la règle 6 (les deux listes sont d'accord) est respectée : le code n'écrit jamais un côté sans l'autre.
- Liverpool reçoit la Juventus : `teams["Liverpool"]["home"] : [] -> ["Juventus"]`, `teams["Juventus"]["away"] : [] -> ["Liverpool"]`.

```python
    host['counts'][guest['country']] += 1
    guest['counts'][host['country']] += 1
```

- Chaque club compte un adversaire de plus du pays de l'autre : `teams["Liverpool"]["counts"]["Italy"] : 0 -> 1`. Grâce à `defaultdict(int)`, un pays jamais vu part de 0.

```python
def unlink(teams, host_club, guest_club):
    host['home'].pop()
    guest['away'].pop()
    host['played'].discard(guest_club)
```

- `unlink` fait exactement l'inverse, dans le même ordre, donc `unlink` après `link` remet tout comme avant.
- `.pop()` enlève le **dernier** élément de la liste. C'est correct car la recherche défait toujours le match le plus récent d'abord (dernier entré, premier sorti, comme une pile d'assiettes). C'est aussi plus rapide que `.remove(club)`, qui chercherait dans la liste.
- Les deux lignes de comptage en dessous retirent 1.

**En une ligne :** `link` inscrit un match dans les fiches des deux clubs ; `unlink` le retire.

---

## 5. `options(slot, teams, slots, pots, constraints)` : qui peut remplir cette case ?

**Arguments :** `slot` : `tuple` `(club, chapeau, à domicile)`, le match à remplir. `teams` : les fiches. `slots` : `set` des cases encore ouvertes. `pots` : les chapeaux. `constraints` : `set` de paires `(domicile, extérieur)` interdites par l'utilisateur.

```python
    club, pot, is_home = slot
    me = teams[club]
    valid = []
    for other in pots[pot - 1]:
```

- Déballe la case. `('Liverpool', 2, False)` veut dire « Liverpool doit encore se déplacer chez un club du chapeau 2 ».
- Seuls les clubs du bon chapeau sont essayés ; `pot - 1` car les listes commencent à 0 alors que les chapeaux commencent à 1.

```python
        if other == club:
            continue
        them = teams[other]
        if them['country'] == me['country']:
            continue
```

- Chaque test qui échoue saute ce club avec `continue` et passe au suivant. L'ordre ne compte que pour la vitesse : les tests rapides qui échouent souvent viennent d'abord.
- Test 1 : un club ne peut pas se jouer lui-même (ça arrive quand la case est contre son propre chapeau). Test 2 : même pays interdit (règle 3).

```python
        if (other, me['pot'], not is_home) not in slots:
            continue
        if other in me['played']:
            continue
```

- Test 3 : la case **miroir**, le même match vu par l'autre club, doit encore être ouverte. Si Liverpool allait chez la Juventus, la Juventus doit encore avoir besoin de « recevoir un club du chapeau 1 ». Cela garde la règle 2 pour l'autre club aussi.
- Test 4 : pas de deuxième rencontre (règle 5), une vérification immédiate grâce à l'ensemble `played`.

```python
        if me['counts'][them['country']] >= MAX_PER_COUNTRY:
            continue
        if them['counts'][me['country']] >= MAX_PER_COUNTRY:
            continue
```

- Tests 5 et 6 : la limite par pays (règle 4), des **deux** côtés. Un seul côté ne suffit pas : Barcelone n'a peut-être encore rencontré aucun club anglais alors qu'Arsenal a déjà rencontré 2 clubs espagnols ; ce match ferait passer Arsenal à 3.

```python
        if ((club, other) if is_home else (other, club)) in constraints:
            continue
        valid.append(other)
    return valid
```

- Test 7 : les interdictions de l'utilisateur (règle 7). Une interdiction est une paire **ordonnée** (domicile, extérieur), donc le code construit d'abord la paire que ce match créerait : `(club, other)` si `club` est à domicile, `(other, club)` sinon.
- Un club qui passe les sept tests est ajouté à `valid`.

**En une ligne :** prend une case ouverte et renvoie la liste des clubs qui peuvent la remplir en respectant les règles.

---

## 6. `fill(teams, slots, rng, budget, pots, constraints)` : la recherche

**Arguments :** `teams`, `slots`, `pots`, `constraints` : comme plus haut. `rng` : `random.Random`, le générateur de hasard du tirage. `budget` : une `list` qui contient un seul nombre, les pas restants.

```python
    if not slots:
        return True
    budget[0] -= 1
    if budget[0] < 0:
        return False
```

- S'il ne reste aucune case, le tirage est complet : `True` remonte à travers tous les appels en attente. C'est le **cas de base** d'une fonction récursive, le moment où elle arrête de s'appeler elle-même.
- Chaque appel dépense un pas du budget. Quand le budget est épuisé, cet essai abandonne.
- Le budget est une liste avec un nombre, pas un simple nombre, pour que chaque niveau de la récursion modifie **la même** boîte. Un simple `int` ne peut pas être modifié sur place : `budget -= 1` dans un appel ne changerait qu'une copie locale.

```python
    chosen, choices = None, None
    for slot in sorted(slots):
        current = options(slot, teams, slots, pots, constraints)
        if choices is None or len(current) < len(choices):
```

- Parcourt chaque case ouverte et garde celle qui a le moins de clubs possibles : la règle **le plus contraint d'abord**.
- `sorted(slots)` au lieu de `slots` : un ensemble de tuples de texte est parcouru dans un ordre qui change à chaque démarrage de Python, donc sans tri, la même graine pourrait donner des tirages différents. Trier fixe l'ordre : la **reproductibilité**.

```python
            chosen, choices = slot, current
            if len(current) <= 1:
                break
```

- Retient la meilleure case jusqu'ici. Dès qu'une case a 0 ou 1 possibilité, on ne trouvera pas mieux, donc le parcours s'arrête tôt avec `break` : cela économise jusqu'à 288 appels à `options`.

```python
    club, _, is_home = chosen
    me = teams[club]
    slots.discard(chosen)
    rng.shuffle(choices)
```

- Ferme la case choisie, puis mélange ses clubs possibles avec le générateur propre au tirage. Ce mélange est la **seule** source de hasard de tout le tirage.

```python
    for other in choices:
        mirror = (other, me['pot'], not is_home)
        host_club, guest_club = (club, other) if is_home else (other, club)
        link(teams, host_club, guest_club)
        slots.discard(mirror)
```

- Essaie chaque club possible à tour de rôle. Calcule la case miroir (le même match pour l'autre club) et qui est à domicile.
- Écrit le match avec `link` et ferme aussi la case miroir : un match remplit deux cases.

```python
        if fill(teams, slots, rng, budget, pots, constraints):
            return True
        slots.add(mirror)
        unlink(teams, host_club, guest_club)
```

- S'appelle elle-même sur le problème plus petit (la **récursion**). Si le reste du tirage réussit, la réussite remonte.
- Sinon, elle défait exactement ce choix (rouvre le miroir, efface le match) et la boucle essaie le club suivant. C'est le **retour sur trace**.

```python
    slots.add(chosen)
    return False
```

- Aucun club n'a marché : rouvrir la case choisie pour que tout soit comme avant, et dire à l'appelant d'essayer sa propre possibilité suivante.

**En une ligne :** remplit chaque case ouverte, la plus difficile d'abord, en essayant les clubs dans un ordre au hasard et en défaisant les choix qui mènent à une impasse ; renvoie `True` quand le tirage est complet.

---

## 7. `draw(teams, rng, pots, constraints)` : jusqu'à 50 essais

**Arguments :** `teams`, `pots`, `constraints` : comme plus haut. `rng` : `random.Random`.

```python
    for attempt in range(1, MAX_ATTEMPTS + 1):
        for team in teams.values():
            team['home'].clear()
            team['away'].clear()
```

- Chaque essai part d'un tirage vide : chaque liste, ensemble et compteur est vidé (les deux lignes suivantes vident `played` et `counts`).
- Le générateur de hasard n'est **pas** remis à zéro, donc un nouvel essai fait d'autres choix au hasard.

```python
        slots = {(club, pot, is_home)
                 for club in teams
                 for pot in range(1, len(pots) + 1)
                 for is_home in (True, False)}
```

- Un **ensemble en compréhension** construit les 288 cases : chaque club, chaque chapeau, domicile et extérieur.

```python
        if fill(teams, slots, rng, [NODE_BUDGET], pots, constraints):
            return attempt
    raise RuntimeError(f'no valid draw found in {MAX_ATTEMPTS} attempts{extra}')
```

- Chaque essai reçoit un budget neuf `[200_000]`. En cas de réussite, il renvoie le numéro de l'essai (utile pour mesurer à quel point les nouveaux départs sont nécessaires).
- Après 50 échecs, il lève une erreur ; `extra` ajoute « (k constraint(s) in force) » quand l'utilisateur avait des interdictions, pour distinguer des interdictions impossibles d'un vrai échec de la recherche.

**En une ligne :** lance la recherche jusqu'à 50 fois depuis zéro, et renvoie le numéro de l'essai qui a marché.

---

## 8. `verify(teams, pots, constraints)` : la vérification indépendante

**Arguments :** `teams` : un tirage fini. `pots`, `constraints` : comme plus haut.

```python
    for club, team in teams.items():
        drawn = list(opponents(team))
        if len(drawn) != 2 * len(pots):
            raise AssertionError(f'{club} has {len(drawn)} matches')
```

- `opponents` (une petite fonction de deux lignes) utilise `chain` pour joindre les listes domicile et extérieur. Règle 1 : 8 adversaires.
- Elle lit **seulement** `home` et `away`, jamais les raccourcis `played` et `counts`. Si un bug avait cassé un raccourci, une vérification qui lui ferait confiance partagerait le bug ; tout recalculer à partir des vraies listes l'attrape.
- Elle lève `AssertionError` avec `raise` au lieu d'utiliser le mot-clé `assert` : `python -O` supprime chaque `assert`, mais jamais un `raise`.

```python
        if len(set(drawn)) != len(drawn):
            raise AssertionError(f'{club} plays someone twice')
        for side in ('home', 'away'):
            pots_played = sorted(teams[other]['pot'] for other in team[side])
```

- Règle 5 : transformer une liste en ensemble enlève les doublons, donc un ensemble plus court veut dire que quelqu'un apparaît deux fois.
- Règle 2 : les chapeaux des adversaires à domicile, triés, doivent être exactement `[1, 2, 3, 4]`, et pareil pour les adversaires à l'extérieur.

```python
        counts = defaultdict(int)
        for other in drawn:
            other_country = teams[other]['country']
            if other_country == team['country']:
```

- Règles 3 et 4, recomptées depuis zéro : aucun adversaire du même pays, au plus 2 par pays.

```python
        for other in team['home']:
            if club not in teams[other]['away']:
                raise AssertionError(f'{club} vs {other} is not mirrored')
            if (club, other) in constraints:
```

- Règle 6 : chaque club que ce club reçoit doit avoir ce club dans sa liste « extérieur ». Règle 7 : aucune paire reçue ne doit être une paire interdite.

**En une ligne :** revérifie les 7 règles sur le tirage fini à partir des listes brutes, et lève une erreur qui nomme le club à la première règle cassée.

---

## 9. `generate_draw(*, comp, seed, verify_result, pots, countries, constraints)` : le point d'entrée

**Arguments :** tous à donner par nom (le `*` oblige à écrire `generate_draw(comp='UEL', seed=3)` au lieu de valeurs par position). `comp` : `'UCL'` ou `'UEL'`. `seed` : toute valeur que `random.Random` accepte. `verify_result` : `bool`. `pots`, `countries` : remplacements facultatifs. `constraints` : un `set` de tuples `(domicile, extérieur)`, ou `None`.

```python
    if seed is None:
        seed = random.random()
    if pots is None:
        pots = POTS_BY_COMP[comp]
    if countries is None:
        countries = _countries(comp)
```

- Remplit les valeurs par défaut. `seed=None` veut dire « un tirage au hasard tout neuf » ; il est calculé **dans** la fonction, donc chaque appel en reçoit un nouveau.
- `_countries(comp)` lit le fichier des pays une fois par compétition grâce à `@lru_cache`.

```python
    if constraints is None:
        constraints = frozenset()
    elif not isinstance(constraints, (set, frozenset)):
        raise TypeError(...)
```

- Pas d'interdiction devient un **frozenset** vide (un ensemble qui ne peut pas être modifié).
- Une liste d'interdictions est refusée bruyamment. En Python, `('a', 'b') == ['a', 'b']` vaut `False`, donc une interdiction écrite sous forme de liste ne correspondrait jamais et ne marcherait jamais. Échouer tôt avec un message clair vaut mieux qu'une interdiction qui ne fait rien en silence.

```python
    teams = build_teams(pots, countries)
    draw(teams, random.Random(seed), pots, constraints)
    if verify_result:
        verify(teams, pots, constraints)
    return teams
```

- Construit les fiches, lance le tirage avec un générateur **privé** `random.Random(seed)` (un autre code qui utilise `random` ne peut pas le déranger), le vérifie (environ 0.2 ms, donc toujours activé), et renvoie les fiches.

**En une ligne :** prend une compétition, une graine et éventuellement des chapeaux, des pays et des interdictions, et renvoie un tirage complet et vérifié.

---

## 10. Petites fonctions utiles

| Fonction | Fait |
|---|---|
| `load_countries(path, wanted)` | lit le CSV avec `encoding='utf-8-sig'` (enlève les octets invisibles qu'Excel ajoute au début) ; pour les clubs pas trouvés par leur nom exact, demande à `model.names.resolve_all` ; lève `ValueError` en listant les clubs toujours introuvables |
| `_countries(comp)` | enveloppe `@lru_cache` : lit une seule fois les pays des clubs d'une compétition |
| `opponents(team)` | `chain(team['home'], team['away'])` : tous les adversaires en un seul passage |
| `fixtures(teams)` | `[(club, other) for club ... for other in team['home']]` : les 144 matchs, chacun une fois, du côté du club qui reçoit |
| `show(teams, pots)` | affiche chaque club avec ses adversaires à domicile et à l'extérieur, triés par chapeau |

---

## 11. Ce que `draw_uecl.py` fait autrement

Le fichier de la Ligue Conférence reprend la même structure. Deux parties sont nouvelles.

### `paired_pot(pot)`

```python
def paired_pot(pot):
    return pot + 1 if pot in (1, 3, 5) else pot - 1
```

- Le chapeau 1 va avec le 2, le 3 avec le 4, le 5 avec le 6 : `paired_pot(3) = 4`, `paired_pot(4) = 3`.
- Un club joue un chapeau de chaque paire à domicile et l'autre à l'extérieur ; c'est ce qui garantit 3 matchs à domicile et 3 à l'extérieur.

### L'intérieur de `fill`

```python
    candidates = []
    for is_home in (True, False):
        slot = (club, pot, is_home)
        if slot in slots:
            for other in options(slot, teams, slots, pots, constraints):
                candidates.append((other, is_home))
```

- En Ligue Conférence, un club rencontre chaque chapeau **une fois**, à domicile ou à l'extérieur. La vraie question est donc « qui, et dans quel sens ? », et chaque candidat est une paire `(adversaire, à domicile ?)`.
- Les deux sens sont rassemblés, puis mélangés ensemble.

```python
    closed = [s for s in ((club, pot, True), (club, pot, False)) if s in slots]
    slots.difference_update(closed)
```

- Les deux sens de ce club contre ce chapeau sont fermés d'un coup, car un seul des deux sera utilisé.
- `difference_update` retire plusieurs éléments d'un ensemble en un seul appel.

```python
        mirror   = (other, me['pot'], not is_home)
        leftover = (other, me['pot'], is_home)
        partner  = (club,  paired_pot(pot), is_home)
        partner2 = (other, paired_pot(me['pot']), not is_home)
```

- Un match ferme jusqu'à quatre cases de plus. `mirror` : le même match pour l'autre club. `leftover` : l'autre sens de l'autre club contre notre chapeau (il ne rencontre qu'un club de notre chapeau). `partner` : notre case contre le chapeau associé **dans le même sens**, désormais interdite, car le chapeau associé doit être joué dans l'autre sens. `partner2` : la même règle pour l'autre club.

```python
        removed = [s for s in (mirror, leftover, partner, partner2) if s in slots]
        slots.difference_update(removed)
        if fill(teams, slots, rng, budget, pots, constraints):
            return True
        slots.update(removed)
```

- Seules les cases vraiment ouvertes sont retirées, et exactement celles-là sont remises en cas d'échec, donc défaire laisse l'ensemble comme il était.

Le fichier de la Ligue Conférence compte aussi les adversaires par pays en parcourant les listes à chaque fois (`faced_from`), au lieu de garder un raccourci `counts`. C'est un peu plus lent (environ deux fois le temps d'un tirage de Ligue des champions), mais il n'y a pas de raccourci qui pourrait devenir faux.
