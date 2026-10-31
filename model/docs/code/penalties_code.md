# `penalties.py`, line by line

> This page walks through the code of the penalty shoot-out. For the idea (the rules, the pressure rule, rejection sampling), read [`../penalties.md`](../penalties.md) first.

*Version française : [plus bas](#penaltiespy-ligne-par-ligne).*

## How to read this page

- Each function starts with its **arguments**.
- The code comes in groups of 2 to 4 lines, each followed by bullets: what, why, and which general idea.
- Each function ends with **In one line**.
- The file imports nothing: the random numbers come from the generator the caller passes in.

---

## 1. The settings

| Code | Does | Example value |
|---|---|---|
| `P_SCORE = 0.76` | chance that a normal kick goes in | 76 in 100 |
| `MAX_ROUNDS = 40` | most rounds of sudden death before the code settles it | 40 |

---

## 2. `Shootout`: the record of one shoot-out

**Arguments:** `first`, `second`: `str`, the club that kicked first and the other one. `goals_first`, `goals_second`: `int`. `kicks_first`, `kicks_second`: `list` of `bool`, one per kick taken (`True` = scored).

```python
        self.first, self.second = first, second
        self.goals_first, self.goals_second = goals_first, goals_second
        self.kicks_first, self.kicks_second = kicks_first, kicks_second
        self.winner = first if goals_first > goals_second else second
```

- Stores everything, then works out the winner once. A shoot-out can never end level, so "not more goals" means the second club won.

```python
        self.p_winner = None
        self.u = None
```

- Filled in later by the caller under the "legs" method: the chance the winner was given, and the random number that picked it, so the app can explain the pick.

```python
    def score_for(self, club):
        if club == self.first:
            return self.goals_first, self.goals_second
        return self.goals_second, self.goals_first
```

- The score seen from one club: `score_for("Atalanta") -> (4, 3)`, `score_for("Arsenal") -> (3, 4)`.
- Any name that is not `first` is treated as `second`, so a misspelt name would quietly give the second club's view.

```python
        mark = {True: "o", False: "x"}
        n = max(len(self.kicks_first), len(self.kicks_second))
        def row(kicks):
            return " ".join([mark[k] for k in kicks] + ["-"] * (n - len(kicks)))
```

- In `sheet()`: turns each kick into `o` or `x` with a tiny dictionary used as a **lookup table**.
- The shorter row is padded with `-` so that round 5 sits in the same column for both clubs: `["x", "o", "o", "x"] + ["-"]`. `["-"] * 1` is a list repeated once.
- `row` is a small function defined inside `sheet`, used twice: once per club.

---

## 3. `_kick_once(random, p)`: play the kicks

**Arguments:** `random`: a function that returns a random number between 0 and 1 (the caller passes `rng.random`). `p`: `float`, the chance of scoring a normal kick.

```python
    ga = gb = 0
    ka, kb = [], []
    PRESSURE_DROP = 0.1
```

- Goals and kick lists of the club kicking first (`a`) and second (`b`).
- `PRESSURE_DROP` is set here, inside the function, so it is rebuilt on every call and hidden from the rest of the file (a known weakness: it belongs next to `P_SCORE`).
- The function receives `rng.random` itself, not `rng`: calling a local name is a little faster than looking up `.random` on every kick.

```python
    for rnd in range(5):
        q = p - PRESSURE_DROP if rnd == 4 and ga + 1 == gb else p
        scored = random() < q
        ka.append(scored)
        ga += scored
```

- Five rounds, numbered 0 to 4. On the fifth (`rnd == 4`), if A trails by exactly one goal, its kick is a must-score and its chance drops to 0.66.
- `random() < q` is `True` with chance `q`: one kick.
- `ga += scored` adds a `bool` to a number: `True` counts as 1, `False` as 0. So this one line counts the goal.

```python
        left = 4 - rnd
        if ga > gb + left + 1 or gb > ga + left:
            return ga, gb, ka, kb
```

- After A's kick, A has `left` kicks left and B has `left + 1` (B has not kicked this round yet).
- The shoot-out is over if A is ahead by more than all of B's remaining kicks, or B is ahead by more than all of A's. Example: round 5 (`left = 0`), A leads 4-2: `4 > 2 + 0 + 1`, so it stops at once and B's last kick is never taken.

```python
        u = p - PRESSURE_DROP if rnd == 4 and gb + 1 == ga else p
        scored = random() < u
        kb.append(scored)
        gb += scored
```

- The same for B: a must-score fifth kick if B trails by one. (The name `u` is confusing here: it is a chance, not a random number.)

```python
        if ga > gb + left or gb > ga + left:
            return ga, gb, ka, kb
```

- After B's kick both clubs have `left` kicks, so the test loses its `+ 1`.

```python
    for _ in range(MAX_ROUNDS):
        sa = random() < p
        sb = random() < p
        ka.append(sa)
        kb.append(sb)
```

- Sudden death: one kick each per round, always at the normal chance.

```python
        ga += sa
        gb += sb
        if sa != sb:
            return ga, gb, ka, kb
```

- `sa != sb` means exactly one of them scored: the round is decided.

```python
    ka.append(True)
    kb.append(False)
    return ga + 1, gb, ka, kb
```

- A safety net after 40 level rounds (about 1 chance in 300 million): A is given the win so the loop can never run forever.

**In one line:** plays a whole shoot-out between the club kicking first and the other, and returns both scores and both kick lists.

---

## 4. `kick(rng, club_a, club_b, p)`: a free shoot-out

**Arguments:** `rng`: `random.Random`. `club_a`, `club_b`: `str`. `p`: `float`, default `P_SCORE`.

```python
    first, second = (club_a, club_b) if rng.random() < 0.5 else (club_b, club_a)
    return Shootout(first, second, *_kick_once(rng.random, p))
```

- The coin for the order: one random number, below 0.5 means `club_a` kicks first.
- `_kick_once` returns four values; the `*` in front **unpacks** them as four separate arguments of `Shootout`.

**In one line:** tosses a coin for the order, plays the kicks, and returns the record.

---

## 5. `kick_for(rng, club_a, club_b, winner, p)`: a shoot-out with a known winner

**Arguments:** as `kick`, plus `winner`: `str`, the club that must win.

```python
    while True:
        so = kick(rng, club_a, club_b, p)
        if so.winner == winner:
            return so
```

- Plays free shoot-outs and returns the first one that the right club wins: **rejection sampling**. Half are accepted, so about 2 tries on average.
- The kept shoot-out is a perfectly normal shoot-out, just one that ended the right way round.
- Risk: if `winner` were neither club, no shoot-out could ever match and the loop would never end. A check such as `assert winner in (club_a, club_b)` at the top would close that door.

**In one line:** returns a realistic shoot-out that the chosen club wins.

---
---

# `penalties.py`, ligne par ligne

> Cette page explique le code de la séance de tirs au but. Pour l'idée (les règles, la règle de pression, l'échantillonnage par rejet), lisez d'abord [`../penalties.md`](../penalties.md#les-tirs-au-but).

## Comment lire cette page

- Chaque fonction commence par ses **arguments**.
- Le code vient en groupes de 2 à 4 lignes, chacun suivi de points : quoi, pourquoi, et quelle idée générale.
- Chaque fonction se termine par **En une ligne**.
- Le fichier n'importe rien : les nombres au hasard viennent du générateur que l'appelant fournit.

---

## 1. Les réglages

| Code | Fait | Exemple |
|---|---|---|
| `P_SCORE = 0.76` | chance qu'un tir normal entre | 76 sur 100 |
| `MAX_ROUNDS = 40` | nombre maximum de tours de mort subite avant que le code tranche | 40 |

---

## 2. `Shootout` : la fiche d'une séance

**Arguments :** `first`, `second` : `str`, le club qui a tiré en premier et l'autre. `goals_first`, `goals_second` : `int`. `kicks_first`, `kicks_second` : `list` de `bool`, un par tir tiré (`True` = marqué).

```python
        self.first, self.second = first, second
        self.goals_first, self.goals_second = goals_first, goals_second
        self.kicks_first, self.kicks_second = kicks_first, kicks_second
        self.winner = first if goals_first > goals_second else second
```

- Range tout, puis calcule le vainqueur une fois. Une séance ne peut jamais finir à égalité, donc « pas plus de buts » veut dire que le second club a gagné.

```python
        self.p_winner = None
        self.u = None
```

- Remplis plus tard par l'appelant avec la méthode « legs » : la chance donnée au vainqueur, et le nombre au hasard qui l'a choisi, pour que l'appli puisse expliquer le choix.

```python
    def score_for(self, club):
        if club == self.first:
            return self.goals_first, self.goals_second
        return self.goals_second, self.goals_first
```

- Le score vu par un club : `score_for("Atalanta") -> (4, 3)`, `score_for("Arsenal") -> (3, 4)`.
- Tout nom qui n'est pas `first` est traité comme `second`, donc un nom mal écrit donnerait en silence le point de vue du second club.

```python
        mark = {True: "o", False: "x"}
        n = max(len(self.kicks_first), len(self.kicks_second))
        def row(kicks):
            return " ".join([mark[k] for k in kicks] + ["-"] * (n - len(kicks)))
```

- Dans `sheet()` : transforme chaque tir en `o` ou `x` avec un petit dictionnaire utilisé comme **table de correspondance**.
- La ligne la plus courte est complétée par `-` pour que le tour 5 soit dans la même colonne pour les deux clubs : `["x", "o", "o", "x"] + ["-"]`. `["-"] * 1` est une liste répétée une fois.
- `row` est une petite fonction définie dans `sheet`, utilisée deux fois : une par club.

---

## 3. `_kick_once(random, p)` : jouer les tirs

**Arguments :** `random` : une fonction qui renvoie un nombre au hasard entre 0 et 1 (l'appelant passe `rng.random`). `p` : `float`, la chance de marquer un tir normal.

```python
    ga = gb = 0
    ka, kb = [], []
    PRESSURE_DROP = 0.1
```

- Buts et listes de tirs du club qui tire en premier (`a`) et en second (`b`).
- `PRESSURE_DROP` est défini ici, dans la fonction, donc il est recréé à chaque appel et caché du reste du fichier (un point faible connu : il devrait être à côté de `P_SCORE`).
- La fonction reçoit `rng.random` lui-même, pas `rng` : appeler un nom local est un peu plus rapide que chercher `.random` à chaque tir.

```python
    for rnd in range(5):
        q = p - PRESSURE_DROP if rnd == 4 and ga + 1 == gb else p
        scored = random() < q
        ka.append(scored)
        ga += scored
```

- Cinq tours, numérotés de 0 à 4. Au cinquième (`rnd == 4`), si A a exactement un but de retard, son tir est obligatoire et sa chance tombe à 0.66.
- `random() < q` vaut `True` avec la chance `q` : un tir.
- `ga += scored` ajoute un `bool` à un nombre : `True` compte 1, `False` compte 0. Cette seule ligne compte donc le but.

```python
        left = 4 - rnd
        if ga > gb + left + 1 or gb > ga + left:
            return ga, gb, ka, kb
```

- Après le tir de A, A a encore `left` tirs et B en a `left + 1` (B n'a pas encore tiré ce tour).
- La séance est finie si A a plus d'avance que tous les tirs restants de B, ou si B a plus d'avance que tous ceux de A. Exemple : tour 5 (`left = 0`), A mène 4-2 : `4 > 2 + 0 + 1`, donc tout s'arrête et le dernier tir de B n'est jamais tiré.

```python
        u = p - PRESSURE_DROP if rnd == 4 and gb + 1 == ga else p
        scored = random() < u
        kb.append(scored)
        gb += scored
```

- Pareil pour B : un cinquième tir obligatoire si B a un but de retard. (Le nom `u` est trompeur ici : c'est une chance, pas un nombre au hasard.)

```python
        if ga > gb + left or gb > ga + left:
            return ga, gb, ka, kb
```

- Après le tir de B, les deux clubs ont `left` tirs, donc le test perd son `+ 1`.

```python
    for _ in range(MAX_ROUNDS):
        sa = random() < p
        sb = random() < p
        ka.append(sa)
        kb.append(sb)
```

- Mort subite : un tir chacun par tour, toujours avec la chance normale.

```python
        ga += sa
        gb += sb
        if sa != sb:
            return ga, gb, ka, kb
```

- `sa != sb` veut dire qu'exactement l'un des deux a marqué : le tour est décidé.

```python
    ka.append(True)
    kb.append(False)
    return ga + 1, gb, ka, kb
```

- Un filet de sécurité après 40 tours à égalité (environ 1 chance sur 300 millions) : A reçoit la victoire pour que la boucle ne tourne jamais à l'infini.

**En une ligne :** joue toute une séance entre le club qui tire en premier et l'autre, et renvoie les deux scores et les deux listes de tirs.

---

## 4. `kick(rng, club_a, club_b, p)` : une séance libre

**Arguments :** `rng` : `random.Random`. `club_a`, `club_b` : `str`. `p` : `float`, par défaut `P_SCORE`.

```python
    first, second = (club_a, club_b) if rng.random() < 0.5 else (club_b, club_a)
    return Shootout(first, second, *_kick_once(rng.random, p))
```

- La pièce pour l'ordre : un nombre au hasard, sous 0.5 veut dire que `club_a` tire en premier.
- `_kick_once` renvoie quatre valeurs ; le `*` devant les **déballe** en quatre arguments séparés pour `Shootout`.

**En une ligne :** lance une pièce pour l'ordre, joue les tirs, et renvoie la fiche.

---

## 5. `kick_for(rng, club_a, club_b, winner, p)` : une séance dont on connaît le vainqueur

**Arguments :** comme `kick`, plus `winner` : `str`, le club qui doit gagner.

```python
    while True:
        so = kick(rng, club_a, club_b, p)
        if so.winner == winner:
            return so
```

- Joue des séances libres et renvoie la première que le bon club gagne : l'**échantillonnage par rejet**. La moitié sont acceptées, donc environ 2 essais en moyenne.
- La séance gardée est une séance parfaitement normale, juste une qui a fini dans le bon sens.
- Risque : si `winner` n'était aucun des deux clubs, aucune séance ne conviendrait jamais et la boucle ne s'arrêterait jamais. Une vérification comme `assert winner in (club_a, club_b)` au début fermerait cette porte.

**En une ligne :** renvoie une séance réaliste que le club choisi gagne.
