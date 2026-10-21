# `league_phase.py`, line by line

> This page walks through the code that plays the league phase and builds the table. For the idea (points, tiebreakers, sorting like a dictionary), read [`../league_phase.md`](../league_phase.md) first.

*Version française : [plus bas](#league_phasepy-ligne-par-ligne).*

## How to read this page

- Each function starts with its **arguments**.
- The code comes in groups of 2 to 4 lines, each followed by bullets: what, why, and which general idea.
- Each function ends with **In one line**.
- This file imports nothing: it only uses Python itself.

---

## 1. `Row`: one club's line in the table

**Arguments:** `club`: `str`. `seed_elo`: `float`, the club's rating before the competition (the last tiebreaker).

```python
    __slots__ = ("club", "played", "wins", "draws", "losses", "gf", "ga",
                 "away_gf", "away_wins", "points", "opponents", "opp_points",
                 "seed_elo", "rank")
```

- The fixed list of attributes. Besides saving memory, it catches typing mistakes: `row.point += 3` (missing "s") raises an error instead of silently creating a new attribute, which would leave the real points wrong.

```python
        self.club = club
        self.played = self.wins = self.draws = self.losses = 0
        self.gf = self.ga = self.away_gf = self.away_wins = self.points = 0
        self.opponents = []
```

- `a = b = c = 0` is a **chained assignment**: all names get 0. Safe here because 0 is a number, which cannot be changed in place.
- `gf` and `ga` are "goals for" and "goals against". `opponents` starts as a new empty list for each row (written separately, because a chained `= []` would make every name share **one** list).

```python
    @property
    def gd(self):
        return self.gf - self.ga
```

- Goal difference is **computed** when asked, never stored, so it can never disagree with the goals. `@property` lets code write `row.gd` without brackets.

---

## 2. `Row.record(goals_for, goals_against, away, opponent)`: add one match

**Arguments:** `goals_for`, `goals_against`: `int`, this club's goals and the opponent's. `away`: `bool`, `True` if this club played away. `opponent`: `str`.

```python
        self.played += 1
        self.gf += goals_for
        self.ga += goals_against
        self.opponents.append(opponent)
```

- Every match adds to the counters: this is the **accumulator pattern**, once per club per match.
- The opponent is remembered for the "opponents' points" tiebreaker, which can only be computed at the end.

```python
        if away:
            self.away_gf += goals_for
        if goals_for > goals_against:
            self.wins += 1
            self.points += 3
```

- Away goals are counted separately (tiebreaker 4).
- A win gives 3 points. A club that wins 2-0 away: `gf: 0 -> 2`, `away_gf: 0 -> 2`, `wins: 0 -> 1`, `points: 0 -> 3`, and the line below adds 1 to `away_wins`.

```python
        elif goals_for == goals_against:
            self.draws += 1
            self.points += 1
        else:
            self.losses += 1
```

- A draw gives 1 point; a defeat gives none, only the counter of losses goes up.

**In one line:** adds one match to a club's line: goals, result, points, and the opponent's name.

---

## 3. `Row.sort_key()`: the numbers used to rank

```python
    def sort_key(self):
        return (self.points, self.gd, self.gf, self.away_gf, self.wins,
                self.away_wins, self.opp_points, self.seed_elo)
```

- Returns the eight ranking numbers as one **tuple**, in the order of the tiebreakers.
- Python compares tuples item by item, like words in a dictionary (**lexicographic order**), so sorting by this tuple applies the whole chain of tiebreakers in one line.
- Every item is "bigger is better", so a single `reverse=True` sort is enough. Club C of the example: `(4, 3, 4, 3, 1, 1, 2, ...)`.

---

## 4. `play_league_phase(engine, matchdays)`: play every match

**Arguments:** `engine`: a `MatchEngine` ([`match_engine_code.md`](match_engine_code.md)). `matchdays`: `list` of days, each a `list` of `(home, away)`.

```python
    played = []
    for number, day in enumerate(matchdays, start=1):
        engine.section(f"Matchday {number}")
```

- `enumerate(..., start=1)` numbers the days from 1.
- `engine.section` adds a title to the expert log (and does nothing outside expert mode); the app turns these titles into tabs.

```python
        played.append([engine.play(home, away, "league", label=f"MD{number}")
                       for home, away in sorted(day)])
    return played
```

- A **list comprehension** plays the 18 matches of the day and keeps the 18 `Match` records.
- `sorted(day)`: the days come out of the planner in an order that can change between runs. Sorting makes the same seed give exactly the same season.
- `"league"` tells the engine which $K$ to use; `label="MD3"` is the text shown in the log.

**In one line:** plays every match of every day in a fixed order and returns the played matches, day by day.

---

## 5. `build_table(clubs, played, seed_ratings)`: rank the clubs

**Arguments:** `clubs`: `list` of `str`, all 36 clubs in pot order. `played`: the output of `play_league_phase`. `seed_ratings`: `dict`, club to rating before the competition.

```python
    rows = {club: Row(club, seed_ratings.get(club, 1500.0)) for club in clubs}
```

- One empty line per club, in a **dictionary comprehension**. `.get(club, 1500.0)` uses 1500 for a club with no rating (written directly here, a second copy of the engine's default).

```python
    for day in played:
        for m in day:
            rows[m.home].record(m.home_goals, m.away_goals, False, m.away)
            rows[m.away].record(m.away_goals, m.home_goals, True, m.home)
```

- **Pass 1**: every match is recorded twice, once from each side. For the away club, the goals are swapped (its "for" is the home club's "against").
- This only reads four attributes of each match (`home`, `away`, `home_goals`, `away_goals`), so any object with those four works: this is **duck typing**, which lets tests feed hand-made scores without running the engine.

```python
    for row in rows.values():
        row.opp_points = sum(rows[o].points for o in row.opponents)
```

- **Pass 2**: opponents' points. It needs everyone's **final** points, which only exist after pass 1 is over; computing it during pass 1 would add up half-finished totals.
- Club A of the example played B (0 points) and D (2 points): `opp_points: 0 -> 2`.

```python
    ordered = sorted(rows.values(), key=Row.sort_key, reverse=True)
    for rank, row in enumerate(ordered, start=1):
        row.rank = rank
    return ordered
```

- `key=Row.sort_key` tells `sorted` to compare clubs by their tuple of section 3; `reverse=True` puts the biggest first.
- Python's sort is **stable**: clubs equal on all eight numbers keep their input order, which is the pot order. That is the real last resort.
- Then each row gets its rank, 1 to 36.

**In one line:** adds up every club's results and returns the clubs in table order, with their rank.

---

## 6. `explain_ties(ordered)`: say which tiebreaker decided

**Arguments:** `ordered`: the ranked rows.

```python
    for above, below in zip(ordered, ordered[1:]):
        if above.points != below.points:
            continue
```

- `zip(ordered, ordered[1:])` pairs each club with the one just below it: (1st, 2nd), (2nd, 3rd), ... This is a common trick to walk through **neighbours** in a list.
- Pairs not level on points need no explanation and are skipped.

```python
        ka, kb = above.sort_key(), below.sort_key()
        for i, (va, vb) in enumerate(zip(ka, kb)):
            if va != vb:
                lines.append(f"... split by {names[i]} ({va:g} v {vb:g})")
                break
```

- Walks through both tuples side by side and stops at the first number that differs; its position `i` gives the tiebreaker's name.
- `{va:g}` prints numbers without useless decimals: `3` rather than `3.0`.
- Result for the example: `1. C ahead of 2. A: level on points, split by goal difference (3 v 2)`.

```python
        else:
            lines.append(f"... identical on every tiebreaker, alphabetical order")
```

- This `else` belongs to the `for` loop, not to the `if`: it runs only if the loop ended **without** `break`, that is when all eight numbers were equal (a **for-else**).
- **Known bug:** the text says "alphabetical order", but the real order is the pot order (stable sort, section 5).

**In one line:** returns one sentence per pair of neighbours level on points, naming the tiebreaker that separated them.

---

## 7. `format_table(ordered, width)`

| Code | Does |
|---|---|
| `head = f"{'#':>2}  {'Club':{width}} ..."` | the header line; `:>2` aligns to the right on 2 characters, `:{width}` pads the club name to 26 characters |
| `lines = [head, "-" * len(head)]` | a line of dashes as long as the header |
| `f"... {r.gd:>+4} ..."` | `+` always shows the sign: `+3`, `-5` |
| `return lines` | a list of text lines for the log and the console |

---
---

# `league_phase.py`, ligne par ligne

> Cette page explique le code qui joue la phase de ligue et construit le classement. Pour l'idée (points, critères de départage, tri comme un dictionnaire), lis d'abord [`../league_phase.md`](../league_phase.md#la-phase-de-ligue--les-matchs-et-le-classement).

## Comment lire cette page

- Chaque fonction commence par ses **arguments**.
- Le code vient en groupes de 2 à 4 lignes, chacun suivi de points : quoi, pourquoi, et quelle idée générale.
- Chaque fonction se termine par **En une ligne**.
- Ce fichier n'importe rien : il n'utilise que Python lui-même.

---

## 1. `Row` : la ligne d'un club dans le classement

**Arguments :** `club` : `str`. `seed_elo` : `float`, la note du club avant la compétition (le dernier critère).

```python
    __slots__ = ("club", "played", "wins", "draws", "losses", "gf", "ga",
                 "away_gf", "away_wins", "points", "opponents", "opp_points",
                 "seed_elo", "rank")
```

- La liste fixe des attributs. En plus d'économiser de la mémoire, elle attrape les fautes de frappe : `row.point += 3` (sans « s ») provoque une erreur au lieu de créer en silence un nouvel attribut, ce qui laisserait les vrais points faux.

```python
        self.club = club
        self.played = self.wins = self.draws = self.losses = 0
        self.gf = self.ga = self.away_gf = self.away_wins = self.points = 0
        self.opponents = []
```

- `a = b = c = 0` est une **affectation en chaîne** : tous les noms reçoivent 0. Sans danger ici car 0 est un nombre, qui ne peut pas être modifié sur place.
- `gf` et `ga` sont les « buts pour » et « buts contre ». `opponents` commence comme une nouvelle liste vide pour chaque ligne (écrite à part, car un `= []` en chaîne ferait partager **une seule** liste à tous les noms).

```python
    @property
    def gd(self):
        return self.gf - self.ga
```

- La différence de buts est **calculée** quand on la demande, jamais rangée, donc elle ne peut jamais contredire les buts. `@property` permet d'écrire `row.gd` sans parenthèses.

---

## 2. `Row.record(goals_for, goals_against, away, opponent)` : ajouter un match

**Arguments :** `goals_for`, `goals_against` : `int`, les buts de ce club et ceux de l'adversaire. `away` : `bool`, `True` si ce club jouait à l'extérieur. `opponent` : `str`.

```python
        self.played += 1
        self.gf += goals_for
        self.ga += goals_against
        self.opponents.append(opponent)
```

- Chaque match s'ajoute aux compteurs : c'est le **schéma de l'accumulateur**, une fois par club et par match.
- L'adversaire est retenu pour le critère « points des adversaires », qui ne peut être calculé qu'à la fin.

```python
        if away:
            self.away_gf += goals_for
        if goals_for > goals_against:
            self.wins += 1
            self.points += 3
```

- Les buts à l'extérieur sont comptés à part (critère 4).
- Une victoire donne 3 points. Un club qui gagne 2-0 à l'extérieur : `gf : 0 -> 2`, `away_gf : 0 -> 2`, `wins : 0 -> 1`, `points : 0 -> 3`, et la ligne en dessous ajoute 1 à `away_wins`.

```python
        elif goals_for == goals_against:
            self.draws += 1
            self.points += 1
        else:
            self.losses += 1
```

- Un nul donne 1 point ; une défaite n'en donne aucun, seul le compteur de défaites augmente.

**En une ligne :** ajoute un match à la ligne d'un club : buts, résultat, points, et le nom de l'adversaire.

---

## 3. `Row.sort_key()` : les nombres utilisés pour classer

```python
    def sort_key(self):
        return (self.points, self.gd, self.gf, self.away_gf, self.wins,
                self.away_wins, self.opp_points, self.seed_elo)
```

- Renvoie les huit nombres du classement sous forme d'un seul **tuple**, dans l'ordre des critères.
- Python compare les tuples élément par élément, comme des mots dans un dictionnaire (**ordre lexicographique**), donc trier selon ce tuple applique toute la chaîne de critères en une ligne.
- Chaque élément suit la règle « plus grand, c'est mieux », donc un seul tri `reverse=True` suffit. Le club C de l'exemple : `(4, 3, 4, 3, 1, 1, 2, ...)`.

---

## 4. `play_league_phase(engine, matchdays)` : jouer chaque match

**Arguments :** `engine` : un `MatchEngine` ([`match_engine_code.md`](match_engine_code.md)). `matchdays` : `list` de journées, chacune une `list` de `(domicile, extérieur)`.

```python
    played = []
    for number, day in enumerate(matchdays, start=1):
        engine.section(f"Matchday {number}")
```

- `enumerate(..., start=1)` numérote les journées à partir de 1.
- `engine.section` ajoute un titre au journal expert (et ne fait rien hors du mode expert) ; l'appli transforme ces titres en onglets.

```python
        played.append([engine.play(home, away, "league", label=f"MD{number}")
                       for home, away in sorted(day)])
    return played
```

- Une **liste en compréhension** joue les 18 matchs de la journée et garde les 18 fiches `Match`.
- `sorted(day)` : les journées sortent du planificateur dans un ordre qui peut changer d'un lancement à l'autre. Les trier fait que la même graine donne exactement la même saison.
- `"league"` dit au moteur quel $K$ utiliser ; `label="MD3"` est le texte affiché dans le journal.

**En une ligne :** joue chaque match de chaque journée dans un ordre fixe et renvoie les matchs joués, journée par journée.

---

## 5. `build_table(clubs, played, seed_ratings)` : classer les clubs

**Arguments :** `clubs` : `list` de `str`, les 36 clubs dans l'ordre des chapeaux. `played` : le résultat de `play_league_phase`. `seed_ratings` : `dict`, club vers note avant la compétition.

```python
    rows = {club: Row(club, seed_ratings.get(club, 1500.0)) for club in clubs}
```

- Une ligne vide par club, dans un **dictionnaire en compréhension**. `.get(club, 1500.0)` utilise 1500 pour un club sans note (écrit directement ici, une deuxième copie de la valeur par défaut du moteur).

```python
    for day in played:
        for m in day:
            rows[m.home].record(m.home_goals, m.away_goals, False, m.away)
            rows[m.away].record(m.away_goals, m.home_goals, True, m.home)
```

- **Passage 1** : chaque match est enregistré deux fois, une fois de chaque côté. Pour le club à l'extérieur, les buts sont inversés (ses buts « pour » sont les buts « contre » du club à domicile).
- Cela ne lit que quatre attributs de chaque match (`home`, `away`, `home_goals`, `away_goals`), donc n'importe quel objet avec ces quatre attributs convient : c'est le **typage canard** (*duck typing*), qui permet aux tests de fournir des scores faits à la main sans lancer le moteur.

```python
    for row in rows.values():
        row.opp_points = sum(rows[o].points for o in row.opponents)
```

- **Passage 2** : les points des adversaires. Il faut les points **finaux** de tout le monde, qui n'existent qu'une fois le passage 1 fini ; les calculer pendant le passage 1 additionnerait des totaux à moitié faits.
- Le club A de l'exemple a joué B (0 point) et D (2 points) : `opp_points : 0 -> 2`.

```python
    ordered = sorted(rows.values(), key=Row.sort_key, reverse=True)
    for rank, row in enumerate(ordered, start=1):
        row.rank = rank
    return ordered
```

- `key=Row.sort_key` dit à `sorted` de comparer les clubs selon leur tuple de la section 3 ; `reverse=True` met le plus grand en premier.
- Le tri de Python est **stable** : des clubs égaux sur les huit nombres gardent leur ordre d'entrée, qui est l'ordre des chapeaux. C'est le vrai dernier recours.
- Ensuite chaque ligne reçoit son rang, de 1 à 36.

**En une ligne :** additionne les résultats de chaque club et renvoie les clubs dans l'ordre du classement, avec leur rang.

---

## 6. `explain_ties(ordered)` : dire quel critère a décidé

**Arguments :** `ordered` : les lignes classées.

```python
    for above, below in zip(ordered, ordered[1:]):
        if above.points != below.points:
            continue
```

- `zip(ordered, ordered[1:])` associe chaque club à celui juste en dessous : (1er, 2e), (2e, 3e), ... C'est une astuce courante pour parcourir des **voisins** dans une liste.
- Les paires qui ne sont pas à égalité de points n'ont pas besoin d'explication et sont sautées.

```python
        ka, kb = above.sort_key(), below.sort_key()
        for i, (va, vb) in enumerate(zip(ka, kb)):
            if va != vb:
                lines.append(f"... split by {names[i]} ({va:g} v {vb:g})")
                break
```

- Parcourt les deux tuples côte à côte et s'arrête au premier nombre différent ; sa position `i` donne le nom du critère.
- `{va:g}` affiche les nombres sans décimales inutiles : `3` plutôt que `3.0`.
- Résultat pour l'exemple : `1. C ahead of 2. A: level on points, split by goal difference (3 v 2)`.

```python
        else:
            lines.append(f"... identical on every tiebreaker, alphabetical order")
```

- Ce `else` appartient à la boucle `for`, pas au `if` : il ne s'exécute que si la boucle s'est finie **sans** `break`, c'est-à-dire quand les huit nombres étaient égaux (un **for-else**).
- **Bug connu :** le texte dit « alphabetical order », mais le vrai ordre est l'ordre des chapeaux (tri stable, section 5).

**En une ligne :** renvoie une phrase par paire de voisins à égalité de points, qui nomme le critère qui les a séparés.

---

## 7. `format_table(ordered, width)`

| Code | Fait |
|---|---|
| `head = f"{'#':>2}  {'Club':{width}} ..."` | la ligne de titres ; `:>2` aligne à droite sur 2 caractères, `:{width}` complète le nom du club jusqu'à 26 caractères |
| `lines = [head, "-" * len(head)]` | une ligne de tirets aussi longue que les titres |
| `f"... {r.gd:>+4} ..."` | `+` affiche toujours le signe : `+3`, `-5` |
| `return lines` | une liste de lignes de texte pour le journal et la console |
