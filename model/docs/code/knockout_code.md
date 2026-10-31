# `knockout.py`, line by line

> This page walks through the code of the knockout phase. For the idea (the bracket, the three methods), read [`../knockout.md`](../knockout.md) first.

*Version française : [plus bas](#knockoutpy-ligne-par-ligne).*

## How to read this page

- Each function starts with its **arguments**.
- The code comes in groups of 2 to 4 lines, each followed by bullets: what, why, and which general idea.
- Each function ends with **In one line**.

---

## 1. The imports and settings

```python
from model import penalties
from model.elo_score_updating import expected_score, update_rating
```

- `penalties` (from this project) plays the shoot-outs; `expected_score` and `update_rating` (from this project) are the two Elo formulas.
- No module from outside the project is needed.

| Code | Does |
|---|---|
| `METHODS = ("legs", "aggregate", "oneshot")` | the three ways to settle a tie |
| `DEFAULT_METHOD = "legs"` | the method used when none is chosen |
| `PLAYOFF_SEEDED = ((9, 10), (11, 12), (13, 14), (15, 16))` | the better-ranked pairs of the play-offs |
| `PLAYOFF_UNSEEDED = ((23, 24), (21, 22), (19, 20), (17, 18))` | position `i` here meets position `i` of the seeded list |
| `R16_TOP = ((1, 2), (3, 4), (5, 6), (7, 8))` | pair `i` meets the winners of play-off group `3 - i` |
| `QF_BRACKET = ((1, 8), (3, 5), (2, 7), (4, 6))` | which round-of-16 ties meet in each quarter-final |

Writing the bracket as data, not as `if` statements, means the shape of the competition can be read and changed in four lines.

---

## 2. `Tie`: the record of one tie

**Arguments:** `a`: `str`, the club hosting the second leg. `b`: `str`, the other club. `stage`: `str`, `"playoff"`, `"r16"`, `"qf"`, `"sf"` or `"final"`. `tag`: where the tie sits in the bracket. `seed_a`, `seed_b`: league positions.

```python
        self.a, self.b, self.stage, self.tag = a, b, stage, tag
        self.method = None
        self.legs = []
        self.score_a = self.score_b = None
```

- The tie starts empty; the play functions fill it in: the method used, the two `Match` records, and the score (aggregate goals or leg points).

```python
        self.extra_time = None
        self.shootout = None
        self.p_advance = None
        self.winner = None
        self.lines = []
```

- `None` means "did not happen": no extra time, no shoot-out. `p_advance` is only set by "oneshot".
- `lines` collects plain-text explanations; the same lines feed the log and the tie's detail card in the app, so both always say the same thing.

```python
    @property
    def loser(self):
        return self.b if self.winner == self.a else self.a
```

- Computed from the winner, so it can never disagree with it. `pens` and `pens_won` are two more properties that give the shoot-out score, or `None`.

---

## 3. `play_tie(engine, tie, method)`: one two-legged tie

**Arguments:** `engine`: the `MatchEngine`. `tie`: a `Tie`. `method`: `str`, one of `METHODS`.

```python
    if method not in METHODS:
        raise ValueError(f"unknown two-leg method {method!r}, choose from {METHODS}")
    tie.method = method
    engine.section(f"{tie.stage}: {tie.a} v {tie.b}  [{method}]")
```

- Refuses an unknown method at once, with a message listing the valid ones. `!r` puts quotes around the wrong value, so an empty or misspelt text is easy to see.
- Opens a section of the expert log for this tie.

```python
    {"legs": _play_legs, "aggregate": _play_aggregate,
     "oneshot": _play_oneshot}[method](engine, tie)
```

- A **dictionary of functions**: the method name picks a function, which is then called with `(engine, tie)`. This replaces a chain of `if ... elif ... elif`, and adding a fourth method means adding one function and one entry. This idea is called **dispatch**.

```python
    for line in tie.lines:
        engine.note("   " + line)
    engine.note(f"   => {tie.winner} through")
    return tie
```

- Copies the tie's explanations into the log, then the winner.

**In one line:** checks the method, runs the matching function, logs the tie and returns it.

---

## 4. `_two_legs(engine, tie)`

```python
    leg1 = engine.play(tie.b, tie.a, tie.stage, label=f"{tie.stage} leg 1")
    leg2 = engine.play(tie.a, tie.b, tie.stage, label=f"{tie.stage} leg 2")
    tie.legs = [leg1, leg2]
    return leg1, leg2
```

- Leg 1 at B's ground, leg 2 at A's ground: B is the home side of the first `play`, A of the second.
- Both are ordinary matches: they move the ratings like any other, so the result of leg 1 changes the chances of leg 2 a little.

---

## 5. `_play_legs(engine, tie)`: the "legs" method

```python
    leg1, leg2 = _two_legs(engine, tie)
    pts_a = (1.0 - leg1.s_home) + leg2.s_home
    pts_b = leg1.s_home + (1.0 - leg2.s_home)
```

- `s_home` is the home side's result in a match: 1, 0.5 or 0. A is away in leg 1, so A's points there are `1 - s_home`; A is at home in leg 2, so its points are `s_home`.
- Juventus (A) v Manchester City: leg 1 City 2-1 Juventus gives `s_home = 1`, so Juventus get 0; leg 2 Juventus 3-1 City gives 1. `pts_a = 0 + 1 = 1`, `pts_b = 1 + 0 = 1`: level.

```python
    if pts_a != pts_b:
        tie.winner = tie.a if pts_a > pts_b else tie.b
        return
```

- More points goes through, and the function stops early (**early return**).

```python
    r_a, r_b = engine.ratings[tie.a], engine.ratings[tie.b]
    p_a = expected_score(r_a, r_b)
    u = engine.rng.random()
    winner = tie.a if u < p_a else tie.b
```

- Level: A's chance is its Elo expected score, computed with the ratings **after** both legs.
- One random number decides, like a weighted coin: below `p_a`, A goes through. With `p_a = 0.586` and `u = 0.6257`, B goes through. A yes/no draw with a fixed chance like this is called a **Bernoulli trial**.

```python
    so = penalties.kick_for(engine.rng, tie.a, tie.b, winner)
    so.p_winner, so.u = (p_a if winner == tie.a else 1.0 - p_a), u
    tie.shootout, tie.winner = so, winner
```

- The winner is already chosen; `kick_for` creates a realistic shoot-out that this club wins ([`penalties_code.md`](penalties_code.md)).
- The chance and the random number are stored on the shoot-out, so the app can show "the Elo expected score gave Atalanta a 41 % chance".

**In one line:** plays both legs, gives 1 or 0.5 point per leg, and on a tie picks the winner with the Elo expected score before creating its shoot-out.

---

## 6. `_play_aggregate(engine, tie)` and `_settle_level`

```python
    leg1, leg2 = _two_legs(engine, tie)
    agg_a = leg1.away_goals + leg2.home_goals
    agg_b = leg1.home_goals + leg2.away_goals
```

- A's goals: away in leg 1, at home in leg 2. Juventus: 1 + 3 = 4; City: 2 + 1 = 3.

```python
    if agg_a != agg_b:
        tie.winner = tie.a if agg_a > agg_b else tie.b
        return
    _settle_level(engine, tie, home=tie.a, away=tie.b)
```

- More goals goes through. If level, extra time is played at A's ground (the end of the second leg).

```python
    et_home, et_away = engine.sampler.sample_extra_time(engine.rng)
    tie.extra_time = (et_home, et_away) if home == tie.a else (et_away, et_home)
    if et_home != et_away:
        tie.winner = home if et_home > et_away else away
        return
```

- `_settle_level` draws an extra-time score ([`scorelines_code.md`](scorelines_code.md), part 7) and stores it in A-then-B order, like every other score of the tie.
- A different score decides the tie. Ratings do **not** move for extra time.

```python
    so = penalties.kick(engine.rng, tie.a, tie.b)
    so.p_winner = 0.5
    tie.shootout, tie.winner = so, so.winner
```

- Still level: a free shoot-out, where the shoot-out itself decides. Each club has a 50 % chance before it starts.

**In one line:** adds the goals of both legs; on a tie, plays extra time, then a shoot-out.

---

## 7. `_play_oneshot(engine, tie)`: the "oneshot" method

```python
    r_a, r_b = engine.ratings[tie.a], engine.ratings[tie.b]
    at_a = engine.model.probabilities(r_a, r_b, trace=engine.expert)
    at_b = engine.model.probabilities(r_b, r_a, trace=engine.expert)
```

- Asks the match model twice: once with A at home, once with B at home.

```python
    p_a = (at_a.p_home + at_b.p_away) / 2
    p_b = (at_a.p_away + at_b.p_home) / 2
    p_adv = p_a / (p_a + p_b)
```

- `p_a`: A's chance of winning one match, averaged over both grounds. Arsenal: `(0.622 + 0.475) / 2 = 0.548`; Atalanta: `0.239`.
- Dividing by `p_a + p_b` drops the draws so the two chances add up to 1 (**renormalising**): `0.548 / 0.787 = 0.696`.

```python
    u = engine.rng.random()
    tie.p_advance = p_adv
    tie.winner = tie.a if u < p_adv else tie.b
```

- One random number decides the whole tie.

```python
    k = engine.k_table[tie.stage]
    e_a = expected_score(r_a, r_b)
    s_a = 1.0 if tie.winner == tie.a else 0.0
    engine.ratings[tie.a] = update_rating(r_a, k, s_a, e_a)
```

- One Elo step for the whole tie, as if it were one match won or lost; the next line does the same for B with `1 - s_a` and `1 - e_a`, so the two changes cancel out.

**In one line:** decides the tie with one random number, using each club's chance of winning one match, then moves the ratings once.

---

## 8. `play_final(engine, tie)`

```python
    match = engine.play(tie.a, tie.b, "final", neutral=True, label="Final")
    tie.legs = [match]
    tie.score_a, tie.score_b = match.home_goals, match.away_goals
```

- One match with `neutral=True`: the engine averages both orientations so nobody gets home advantage ([`match_engine_code.md`](match_engine_code.md), part 8).

```python
    if match.winner is not None:
        tie.winner = match.winner
    else:
        _settle_level(engine, tie, home=tie.a, away=tie.b)
```

- A draw after 90 minutes goes to extra time, then penalties, whatever method was chosen for the earlier rounds.

---

## 9. The bracket: `_pair_up`, `draw_playoffs`, `draw_r16`, `_next_round`

```python
def _pair_up(seeded, unseeded, rng):
    (s1, s2), (u1, u2) = seeded, unseeded
    if rng.random() < 0.5:
        return [(s1, u1), (s2, u2)]
    return [(s1, u2), (s2, u1)]
```

- A coin decides which of the two better-ranked clubs meets which of the two others. `(Arsenal, Real Madrid)` and `(AC Milan, Feyenoord)` give either Arsenal v AC Milan and Real Madrid v Feyenoord, or Arsenal v Feyenoord and Real Madrid v AC Milan.
- The coin uses the season's own random generator, so the same seed gives the same bracket.

```python
    for slot, (seeded, unseeded) in enumerate(zip(PLAYOFF_SEEDED, PLAYOFF_UNSEEDED)):
        s_clubs = tuple(by_rank[r] for r in seeded)
        u_clubs = tuple(by_rank[r] for r in unseeded)
        for a, b in _pair_up(s_clubs, u_clubs, rng):
```

- In `draw_playoffs`: `zip` walks the two lists of pairs side by side: (9/10 with 23/24), (11/12 with 21/22), ... `by_rank` turns a position into a club name.
- Each tie gets `tag = slot` (0 to 3), its group number, which the next round needs. The better-ranked club is `a`, so it hosts the second leg.

```python
    winners_by_slot = {}
    for tie in playoff_ties:
        winners_by_slot.setdefault(tie.tag, []).append(tie.winner)
```

- In `draw_r16`: groups the play-off winners by group number. `setdefault(tag, [])` creates the empty list the first time a group is seen, then `append` adds the winner: `{0: ["Feyenoord", "Real Madrid"], 1: [...], ...}`.

```python
    for index, top in enumerate(R16_TOP):
        top_clubs = tuple(by_rank[r] for r in top)
        opponents = tuple(winners_by_slot[3 - index])
```

- `3 - index` reverses the order: the pair 1st/2nd (index 0) meets group 3 (15th/16th v 17th/18th), the weakest path; 7th/8th (index 3) meet group 0 (9th/10th v 23rd/24th).
- Each round-of-16 tie is tagged with the league position of its top-8 club, which `QF_BRACKET` uses.

```python
    winner_by_tag = {tie.tag: tie.winner for tie in previous}
    for index, (t1, t2) in enumerate(pairs_by_tag):
        first, second = winner_by_tag[t1], winner_by_tag[t2]
        if rng.random() < 0.5:
            first, second = second, first
```

- In `_next_round`: finds the winners by tag and pairs them as the bracket says; a coin decides who hosts the second leg. The new ties are tagged 0, 1, 2, ... so the same function builds the semi-finals with `((0, 1), (2, 3))` and the final with `((0, 1),)`.

---

## 10. `play_knockout(engine, table, method)`: from table to champion

**Arguments:** `engine`: the `MatchEngine`. `table`: the ranked `Row` list. `method`: `str`.

```python
    by_rank = {row.rank: row.club for row in table}
    rng = engine.rng
    rounds = {}
```

- `by_rank`: `{1: "Barcelona", 2: "Club Brugge", ...}`. `rounds` will hold every round's ties.

```python
    playoffs = draw_playoffs(by_rank, rng)
    rounds["playoff"] = [play_tie(engine, tie, method) for tie in playoffs]
    r16 = draw_r16(by_rank, rounds["playoff"], rng)
    rounds["r16"] = [play_tie(engine, tie, method) for tie in r16]
```

- Draw, then play, round after round. The round of 16 needs the play-off winners, so it can only be drawn after the play-offs are played.

```python
    qf = _next_round(rounds["r16"], QF_BRACKET, "qf", rng, by_rank)
    sf = _next_round(rounds["qf"], ((0, 1), (2, 3)), "sf", rng, by_rank)
    final = _next_round(rounds["sf"], ((0, 1),), "final", rng, by_rank)[0]
    rounds["final"] = [play_final(engine, final)]
```

- The quarter-finals, semi-finals and final are built with the same helper (each followed in the real code by its `play_tie` line). `[0]` takes the single tie of the final.

**In one line:** takes the league table and returns every tie of every round, the last one holding the champion.

---

## 11. `_rank_of(by_rank, club)`

| Line | Does |
|---|---|
| `reverse = _REVERSE.get(id(by_rank))` | looks for a saved reverse table (club to position) for this exact `by_rank` dictionary |
| `if reverse is None or reverse[0] is not by_rank:` | builds it if missing; the `is` test makes sure the saved table belongs to this very dictionary, not to an old one that happened to get the same memory address |
| `_REVERSE.clear()` | keeps only one saved table at a time, so memory never grows |
| `return reverse[1].get(club)` | the club's position, or `None` |

---
---

# `knockout.py`, ligne par ligne

> Cette page explique le code de la phase à élimination directe. Pour l'idée (le tableau, les trois méthodes), lisez d'abord [`../knockout.md`](../knockout.md#la-phase-à-élimination-directe--barrages-tableau-et-finale).

## Comment lire cette page

- Chaque fonction commence par ses **arguments**.
- Le code vient en groupes de 2 à 4 lignes, chacun suivi de points : quoi, pourquoi, et quelle idée générale.
- Chaque fonction se termine par **En une ligne**.

---

## 1. Les imports et les réglages

```python
from model import penalties
from model.elo_score_updating import expected_score, update_rating
```

- `penalties` (de ce projet) joue les tirs au but ; `expected_score` et `update_rating` (de ce projet) sont les deux formules d'Elo.
- Aucun module extérieur au projet n'est nécessaire.

| Code | Fait |
|---|---|
| `METHODS = ("legs", "aggregate", "oneshot")` | les trois façons de décider une confrontation |
| `DEFAULT_METHOD = "legs"` | la méthode utilisée quand aucune n'est choisie |
| `PLAYOFF_SEEDED = ((9, 10), (11, 12), (13, 14), (15, 16))` | les paires les mieux classées des barrages |
| `PLAYOFF_UNSEEDED = ((23, 24), (21, 22), (19, 20), (17, 18))` | la position `i` ici rencontre la position `i` de la liste des mieux classés |
| `R16_TOP = ((1, 2), (3, 4), (5, 6), (7, 8))` | la paire `i` rencontre les vainqueurs du groupe de barrage `3 - i` |
| `QF_BRACKET = ((1, 8), (3, 5), (2, 7), (4, 6))` | quelles confrontations des huitièmes se rencontrent en quarts |

Écrire le tableau sous forme de données, et non de `if`, permet de lire et de changer la forme de la compétition en quatre lignes.

---

## 2. `Tie` : la fiche d'une confrontation

**Arguments :** `a` : `str`, le club qui reçoit au retour. `b` : `str`, l'autre club. `stage` : `str`, `"playoff"`, `"r16"`, `"qf"`, `"sf"` ou `"final"`. `tag` : la place de la confrontation dans le tableau. `seed_a`, `seed_b` : places au classement.

```python
        self.a, self.b, self.stage, self.tag = a, b, stage, tag
        self.method = None
        self.legs = []
        self.score_a = self.score_b = None
```

- La confrontation commence vide ; les fonctions de jeu la remplissent : la méthode utilisée, les deux fiches `Match`, et le score (buts cumulés ou points des matchs).

```python
        self.extra_time = None
        self.shootout = None
        self.p_advance = None
        self.winner = None
        self.lines = []
```

- `None` veut dire « ne s'est pas produit » : pas de prolongation, pas de tirs au but. `p_advance` n'est rempli que par « oneshot ».
- `lines` rassemble des explications en texte simple ; les mêmes lignes alimentent le journal et la fiche détaillée de la confrontation dans l'appli, donc les deux disent toujours la même chose.

```python
    @property
    def loser(self):
        return self.b if self.winner == self.a else self.a
```

- Calculé à partir du vainqueur, donc il ne peut jamais le contredire. `pens` et `pens_won` sont deux autres propriétés qui donnent le score des tirs au but, ou `None`.

---

## 3. `play_tie(engine, tie, method)` : une confrontation aller-retour

**Arguments :** `engine` : le `MatchEngine`. `tie` : un `Tie`. `method` : `str`, une des `METHODS`.

```python
    if method not in METHODS:
        raise ValueError(f"unknown two-leg method {method!r}, choose from {METHODS}")
    tie.method = method
    engine.section(f"{tie.stage}: {tie.a} v {tie.b}  [{method}]")
```

- Refuse tout de suite une méthode inconnue, avec un message qui liste les bonnes. `!r` met des guillemets autour de la mauvaise valeur, pour qu'un texte vide ou mal écrit se voie facilement.
- Ouvre une section du journal expert pour cette confrontation.

```python
    {"legs": _play_legs, "aggregate": _play_aggregate,
     "oneshot": _play_oneshot}[method](engine, tie)
```

- Un **dictionnaire de fonctions** : le nom de la méthode choisit une fonction, qui est ensuite appelée avec `(engine, tie)`. Cela remplace une chaîne de `if ... elif ... elif`, et ajouter une quatrième méthode veut dire ajouter une fonction et une entrée. Cette idée s'appelle la **répartition** (*dispatch*).

```python
    for line in tie.lines:
        engine.note("   " + line)
    engine.note(f"   => {tie.winner} through")
    return tie
```

- Recopie les explications de la confrontation dans le journal, puis le vainqueur.

**En une ligne :** vérifie la méthode, lance la fonction correspondante, écrit la confrontation dans le journal et la renvoie.

---

## 4. `_two_legs(engine, tie)`

```python
    leg1 = engine.play(tie.b, tie.a, tie.stage, label=f"{tie.stage} leg 1")
    leg2 = engine.play(tie.a, tie.b, tie.stage, label=f"{tie.stage} leg 2")
    tie.legs = [leg1, leg2]
    return leg1, leg2
```

- Le match aller chez B, le retour chez A : B est l'équipe à domicile du premier `play`, A du second.
- Ce sont deux matchs ordinaires : ils font bouger les notes comme les autres, donc le résultat de l'aller change un peu les chances du retour.

---

## 5. `_play_legs(engine, tie)` : la méthode « legs »

```python
    leg1, leg2 = _two_legs(engine, tie)
    pts_a = (1.0 - leg1.s_home) + leg2.s_home
    pts_b = leg1.s_home + (1.0 - leg2.s_home)
```

- `s_home` est le résultat de l'équipe à domicile dans un match : 1, 0.5 ou 0. A est à l'extérieur à l'aller, donc ses points y valent `1 - s_home` ; A est à domicile au retour, donc ses points valent `s_home`.
- Juventus (A) contre Manchester City : aller City 2-1 Juventus donne `s_home = 1`, donc la Juventus a 0 ; retour Juventus 3-1 City donne 1. `pts_a = 0 + 1 = 1`, `pts_b = 1 + 0 = 1` : égalité.

```python
    if pts_a != pts_b:
        tie.winner = tie.a if pts_a > pts_b else tie.b
        return
```

- Le plus de points se qualifie, et la fonction s'arrête tôt (**retour anticipé**).

```python
    r_a, r_b = engine.ratings[tie.a], engine.ratings[tie.b]
    p_a = expected_score(r_a, r_b)
    u = engine.rng.random()
    winner = tie.a if u < p_a else tie.b
```

- Égalité : la chance de A est son score attendu Elo, calculé avec les notes **après** les deux matchs.
- Un nombre au hasard décide, comme une pièce truquée : sous `p_a`, A se qualifie. Avec `p_a = 0.586` et `u = 0.6257`, c'est B. Un tirage oui/non avec une chance fixe comme celui-ci s'appelle une **épreuve de Bernoulli**.

```python
    so = penalties.kick_for(engine.rng, tie.a, tie.b, winner)
    so.p_winner, so.u = (p_a if winner == tie.a else 1.0 - p_a), u
    tie.shootout, tie.winner = so, winner
```

- Le vainqueur est déjà choisi ; `kick_for` crée une séance de tirs au but réaliste que ce club gagne ([`penalties_code.md`](penalties_code.md)).
- La chance et le nombre au hasard sont gardés sur la séance, pour que l'appli puisse afficher « le score attendu Elo donnait 41 % à l'Atalanta ».

**En une ligne :** joue les deux matchs, donne 1 ou 0.5 point par match, et en cas d'égalité choisit le vainqueur avec le score attendu Elo avant de créer sa séance de tirs au but.

---

## 6. `_play_aggregate(engine, tie)` et `_settle_level`

```python
    leg1, leg2 = _two_legs(engine, tie)
    agg_a = leg1.away_goals + leg2.home_goals
    agg_b = leg1.home_goals + leg2.away_goals
```

- Les buts de A : à l'extérieur à l'aller, à domicile au retour. Juventus : 1 + 3 = 4 ; City : 2 + 1 = 3.

```python
    if agg_a != agg_b:
        tie.winner = tie.a if agg_a > agg_b else tie.b
        return
    _settle_level(engine, tie, home=tie.a, away=tie.b)
```

- Le plus de buts se qualifie. En cas d'égalité, la prolongation se joue chez A (la fin du match retour).

```python
    et_home, et_away = engine.sampler.sample_extra_time(engine.rng)
    tie.extra_time = (et_home, et_away) if home == tie.a else (et_away, et_home)
    if et_home != et_away:
        tie.winner = home if et_home > et_away else away
        return
```

- `_settle_level` tire un score de prolongation ([`scorelines_code.md`](scorelines_code.md), partie 7) et le range dans l'ordre A puis B, comme tous les autres scores de la confrontation.
- Un score différent décide. Les notes ne bougent **pas** pour la prolongation.

```python
    so = penalties.kick(engine.rng, tie.a, tie.b)
    so.p_winner = 0.5
    tie.shootout, tie.winner = so, so.winner
```

- Toujours égalité : une séance de tirs au but libre, où c'est la séance qui décide. Chaque club a 50 % de chances avant qu'elle commence.

**En une ligne :** additionne les buts des deux matchs ; en cas d'égalité, joue la prolongation, puis les tirs au but.

---

## 7. `_play_oneshot(engine, tie)` : la méthode « oneshot »

```python
    r_a, r_b = engine.ratings[tie.a], engine.ratings[tie.b]
    at_a = engine.model.probabilities(r_a, r_b, trace=engine.expert)
    at_b = engine.model.probabilities(r_b, r_a, trace=engine.expert)
```

- Interroge le modèle de match deux fois : une fois avec A à domicile, une fois avec B à domicile.

```python
    p_a = (at_a.p_home + at_b.p_away) / 2
    p_b = (at_a.p_away + at_b.p_home) / 2
    p_adv = p_a / (p_a + p_b)
```

- `p_a` : la chance de A de gagner un match, en moyenne sur les deux stades. Arsenal : `(0.622 + 0.475) / 2 = 0.548` ; Atalanta : `0.239`.
- Diviser par `p_a + p_b` enlève les nuls pour que les deux chances fassent 1 au total (**renormaliser**) : `0.548 / 0.787 = 0.696`.

```python
    u = engine.rng.random()
    tie.p_advance = p_adv
    tie.winner = tie.a if u < p_adv else tie.b
```

- Un seul nombre au hasard décide toute la confrontation.

```python
    k = engine.k_table[tie.stage]
    e_a = expected_score(r_a, r_b)
    s_a = 1.0 if tie.winner == tie.a else 0.0
    engine.ratings[tie.a] = update_rating(r_a, k, s_a, e_a)
```

- Un seul pas Elo pour toute la confrontation, comme si c'était un match gagné ou perdu ; la ligne suivante fait pareil pour B avec `1 - s_a` et `1 - e_a`, donc les deux changements s'annulent.

**En une ligne :** décide la confrontation avec un seul nombre au hasard, à partir de la chance de chaque club de gagner un match, puis fait bouger les notes une fois.

---

## 8. `play_final(engine, tie)`

```python
    match = engine.play(tie.a, tie.b, "final", neutral=True, label="Final")
    tie.legs = [match]
    tie.score_a, tie.score_b = match.home_goals, match.away_goals
```

- Un seul match avec `neutral=True` : le moteur fait la moyenne des deux sens pour que personne n'ait l'avantage du terrain ([`match_engine_code.md`](match_engine_code.md), partie 8).

```python
    if match.winner is not None:
        tie.winner = match.winner
    else:
        _settle_level(engine, tie, home=tie.a, away=tie.b)
```

- Un nul après 90 minutes mène à la prolongation, puis aux tirs au but, quelle que soit la méthode choisie pour les tours d'avant.

---

## 9. Le tableau : `_pair_up`, `draw_playoffs`, `draw_r16`, `_next_round`

```python
def _pair_up(seeded, unseeded, rng):
    (s1, s2), (u1, u2) = seeded, unseeded
    if rng.random() < 0.5:
        return [(s1, u1), (s2, u2)]
    return [(s1, u2), (s2, u1)]
```

- Une pièce décide lequel des deux clubs les mieux classés rencontre lequel des deux autres. `(Arsenal, Real Madrid)` et `(AC Milan, Feyenoord)` donnent soit Arsenal-AC Milan et Real Madrid-Feyenoord, soit Arsenal-Feyenoord et Real Madrid-AC Milan.
- La pièce utilise le générateur de hasard de la saison, donc la même graine donne le même tableau.

```python
    for slot, (seeded, unseeded) in enumerate(zip(PLAYOFF_SEEDED, PLAYOFF_UNSEEDED)):
        s_clubs = tuple(by_rank[r] for r in seeded)
        u_clubs = tuple(by_rank[r] for r in unseeded)
        for a, b in _pair_up(s_clubs, u_clubs, rng):
```

- Dans `draw_playoffs` : `zip` parcourt les deux listes de paires côte à côte : (9/10 avec 23/24), (11/12 avec 21/22), ... `by_rank` transforme une place en nom de club.
- Chaque confrontation reçoit `tag = slot` (0 à 3), son numéro de groupe, dont le tour suivant a besoin. Le club le mieux classé est `a`, donc il reçoit au retour.

```python
    winners_by_slot = {}
    for tie in playoff_ties:
        winners_by_slot.setdefault(tie.tag, []).append(tie.winner)
```

- Dans `draw_r16` : regroupe les vainqueurs des barrages par numéro de groupe. `setdefault(tag, [])` crée la liste vide la première fois qu'on voit un groupe, puis `append` ajoute le vainqueur : `{0: ["Feyenoord", "Real Madrid"], 1: [...], ...}`.

```python
    for index, top in enumerate(R16_TOP):
        top_clubs = tuple(by_rank[r] for r in top)
        opponents = tuple(winners_by_slot[3 - index])
```

- `3 - index` inverse l'ordre : la paire 1er/2e (index 0) rencontre le groupe 3 (15e/16e contre 17e/18e), le chemin le plus facile ; 7e/8e (index 3) rencontrent le groupe 0 (9e/10e contre 23e/24e).
- Chaque confrontation des huitièmes reçoit comme étiquette la place au classement de son club du top 8, utilisée par `QF_BRACKET`.

```python
    winner_by_tag = {tie.tag: tie.winner for tie in previous}
    for index, (t1, t2) in enumerate(pairs_by_tag):
        first, second = winner_by_tag[t1], winner_by_tag[t2]
        if rng.random() < 0.5:
            first, second = second, first
```

- Dans `_next_round` : retrouve les vainqueurs par étiquette et les associe comme le dit le tableau ; une pièce décide qui reçoit au retour. Les nouvelles confrontations sont étiquetées 0, 1, 2, ... donc la même fonction construit les demies avec `((0, 1), (2, 3))` et la finale avec `((0, 1),)`.

---

## 10. `play_knockout(engine, table, method)` : du classement au champion

**Arguments :** `engine` : le `MatchEngine`. `table` : la liste de `Row` classées. `method` : `str`.

```python
    by_rank = {row.rank: row.club for row in table}
    rng = engine.rng
    rounds = {}
```

- `by_rank` : `{1: "Barcelona", 2: "Club Brugge", ...}`. `rounds` gardera les confrontations de chaque tour.

```python
    playoffs = draw_playoffs(by_rank, rng)
    rounds["playoff"] = [play_tie(engine, tie, method) for tie in playoffs]
    r16 = draw_r16(by_rank, rounds["playoff"], rng)
    rounds["r16"] = [play_tie(engine, tie, method) for tie in r16]
```

- Tirer, puis jouer, tour après tour. Les huitièmes ont besoin des vainqueurs des barrages, donc ils ne peuvent être tirés qu'après les barrages.

```python
    qf = _next_round(rounds["r16"], QF_BRACKET, "qf", rng, by_rank)
    sf = _next_round(rounds["qf"], ((0, 1), (2, 3)), "sf", rng, by_rank)
    final = _next_round(rounds["sf"], ((0, 1),), "final", rng, by_rank)[0]
    rounds["final"] = [play_final(engine, final)]
```

- Les quarts, les demies et la finale sont construits avec la même fonction (chacun suivi dans le vrai code de sa ligne `play_tie`). `[0]` prend la seule confrontation de la finale.

**En une ligne :** prend le classement de la phase de ligue et renvoie chaque confrontation de chaque tour, la dernière contenant le champion.

---

## 11. `_rank_of(by_rank, club)`

| Ligne | Fait |
|---|---|
| `reverse = _REVERSE.get(id(by_rank))` | cherche une table inversée (club vers place) déjà gardée pour ce dictionnaire `by_rank` précis |
| `if reverse is None or reverse[0] is not by_rank:` | la construit si elle manque ; le test `is` vérifie que la table gardée appartient bien à ce dictionnaire-là, et pas à un ancien qui aurait reçu la même adresse en mémoire |
| `_REVERSE.clear()` | ne garde qu'une table à la fois, pour que la mémoire ne grossisse jamais |
| `return reverse[1].get(club)` | la place du club, ou `None` |
