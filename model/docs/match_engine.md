# The match engine: one simulated match

> This part plays **one** match of the simulation. It reads both clubs' ratings, works out the chances of each result, rolls a die to pick the result, picks a score that fits it, and updates both ratings. The league phase and the knockout rounds both use it for every match.

*Version française : [plus bas](#le-moteur-de-match--un-match-simulé).*

## In short

- **What goes in:** two clubs, the round (league phase, quarter-final, ...), and whether the ground is neutral (only for the final).
- **What comes out:** a played match: the result, the score, every number used, and both clubs' new ratings.
- **Where it is used:** the league phase ([`league_phase.md`](league_phase.md)) and the knockout rounds ([`knockout.md`](knockout.md)) call it for every match; about 189 times per simulated Champions League season.
- **Code:** `model/match_engine.py`. Line-by-line walkthrough: [`code/match_engine_code.md`](code/match_engine_code.md).

---

## 1. The five steps

Every simulated match goes through the same five steps, always in this order:

| Step | What happens | Explained in |
|---|---|---|
| 1 | read both clubs' **current** ratings (they change during the season) | [`elo.md`](elo.md) |
| 2 | turn the rating gap into three chances: home win, draw, away win | [`logistic_regression.md`](logistic_regression.md) |
| 3 | roll a die to pick the result | section 2 below |
| 4 | pick a score that fits the result | [`scorelines.md`](scorelines.md) |
| 5 | update both ratings | section 3 below |

In expert mode, every number of every step is also written to a log, so a person can follow the match line by line.

---

## 2. Step 3: one random number picks the result

Imagine a ruler from 0 to 1, cut into three pieces. Each piece is as long as the chance of one result:

```
 0                       0.622        0.816               1
 |-------- home ---------|--- draw ---|------ away -------|
```

For Arsenal at home to Atalanta, the chances are 62.2 % home win, 19.4 % draw and 18.4 % away win. So the home piece goes from 0 to 0.622, the draw piece from 0.622 to 0.816 (0.622 + 0.194), and the away piece from 0.816 to 1.

The computer then picks a random number $u$ between 0 and 1, where every value is equally likely, and looks at which piece it falls in:

| $u$ | Falls in | Result |
|---|---|---|
| 0.30 | the home piece (below 0.622) | Arsenal win |
| 0.6394 | the draw piece (between 0.622 and 0.816) | draw |
| 0.90 | the away piece (above 0.816) | Atalanta win |

Why is it fair? Because the chance of landing in a piece is exactly its length. Over many matches, $u$ falls below 0.622 in 62.2 % of them, so Arsenal win 62.2 % of the time, exactly as the model said.

---

## 3. Step 5: both ratings move

After the result, both ratings move with the Elo rule of [`elo.md`](elo.md), section 4. The size of the step, $K$, depends on the competition and the round:

| Competition | league phase | play-off | round of 16 | quarter-final | semi-final | final |
|---|---|---|---|---|---|---|
| Champions League | 24.00 | 24.72 | 25.44 | 25.92 | 26.40 | 26.88 |
| Europa League | 22.40 | 23.07 | 23.74 | 24.19 | 24.64 | 25.09 |
| Conference League | 21.20 | 21.84 | 22.47 | 22.90 | 23.32 | 23.74 |

Whatever one club gains, the other loses: the two changes always add up to 0.

These new ratings are used for the club's **next** match in the same season. So a club on a winning run gets stronger during the competition, and a club that keeps losing gets weaker. Every new simulated season starts again from the original ratings.

---

## 4. A full example: Arsenal v Atalanta

Champions League league phase, with the random generator started from the number 42. This is the real expert log:

```
-- MD1: Arsenal v Atalanta
   x = R_home - R_away = 1787.880 - 1720.120 = 67.760
   x' = (x - -0.151) / 88.495 = 0.767
   z_home = +0.5692 * x' +0.3562 = 0.793
   z_draw = -0.0308 * x' -0.3459 = -0.370
   z_away = -0.5384 * x' -0.0103 = -0.423
   p_home = 0.622   p_draw = 0.194   p_away = 0.184
   u = 0.6394  ->  DRAW  (home if u < 0.622, draw if u < 0.816, else away)
   scoreline 0-0  (P = 0.231 given draw)
   Elo: E_home = 1/(1+10^((1720.1-1787.9)/400)) = 0.596   S_home = 0.5   K = 24.00
        Arsenal: 1787.9 -> 1785.6 (-2.3)   Atalanta: 1720.1 -> 1722.4 (+2.3)
```

Line by line, in plain words:

1. The rating gap is 67.76 points.
2. The model turns it into three chances: 62.2 %, 19.4 %, 18.4 %.
3. The random number is 0.6394: above 0.622, below 0.816, so the result is a **draw**.
4. Among real draws, 0-0 happens 23.1 % of the time; this time the score is 0-0.
5. Arsenal were expected to take 0.596 of the point and took only 0.5, so they lose 2.3 points; Atalanta gain 2.3.

Had $u$ been 0.30, Arsenal would have won and gained 9.70 points. Had it been 0.90, Atalanta would have won and Arsenal would have lost 14.30. A favourite loses more for a defeat than it gains for a win, because the win was expected.

---

## 5. The final, on a neutral ground

The match model learnt from real matches, where the home side has an advantage. A final is played at a neutral stadium, so nobody should get that advantage. For the final, the engine asks the model twice, once with each club "at home", and takes the average ([`logistic_regression.md`](logistic_regression.md), section 9). For Arsenal and Atalanta: 54.8 % Arsenal, 21.2 % draw, 23.9 % Atalanta.

---

## 6. Try it in Python

One match, from ratings to new ratings, with the real numbers of the match model.

```python
import math
import random

# The 8 numbers of the match model (see logistic_regression.md)
AVERAGE_GAP, TYPICAL_GAP = -0.1508, 88.4953
SLOPE = {"home": 0.5692, "draw": -0.0308, "away": -0.5384}
START = {"home": 0.3562, "draw": -0.3459, "away": -0.0103}

# How often each score happened in real matches (top scores only; the real table has them all)
SCORES = {"home": {(1, 0): 377, (2, 0): 341, (2, 1): 399, (3, 0): 212, (3, 1): 204},
          "draw": {(0, 0): 225, (1, 1): 458, (2, 2): 237, (3, 3): 50, (4, 4): 5},
          "away": {(0, 1): 321, (0, 2): 237, (1, 2): 322, (0, 3): 136, (1, 3): 139}}

def play(home, away, ratings, k, rng):
    r_home, r_away = ratings[home], ratings[away]
    # 1. three chances
    x = (r_home - r_away - AVERAGE_GAP) / TYPICAL_GAP
    powered = {o: math.exp(SLOPE[o] * x + START[o]) for o in SLOPE}
    total = sum(powered.values())
    p = {o: v / total for o, v in powered.items()}
    # 2. one random number picks the result
    u = rng.random()
    if u < p["home"]:
        result = "home"
    elif u < p["home"] + p["draw"]:
        result = "draw"
    else:
        result = "away"
    # 3. a score for that result, picked in proportion to how often it happened
    table = SCORES[result]
    goals = rng.choices(list(table), weights=list(table.values()))[0]
    # 4. Elo update
    e_home = 1 / (1 + 10 ** ((r_away - r_home) / 400))
    s_home = {"home": 1.0, "draw": 0.5, "away": 0.0}[result]
    ratings[home] = r_home + k * (s_home - e_home)
    ratings[away] = r_away - k * (s_home - e_home)
    print(f"chances {p['home']:.3f} / {p['draw']:.3f} / {p['away']:.3f}, u = {u:.4f} -> {result}")
    print(f"{home} {goals[0]}-{goals[1]} {away}")
    print(f"{home} {r_home:.2f} -> {ratings[home]:.2f}, {away} {r_away:.2f} -> {ratings[away]:.2f}")

ratings = {"Arsenal": 1787.88, "Atalanta": 1720.12}
play("Arsenal", "Atalanta", ratings, k=24, rng=random.Random(42))
```

Output (the same as the real engine's log above):

```
chances 0.622 / 0.194 / 0.184, u = 0.6394 -> draw
Arsenal 0-0 Atalanta
Arsenal 1787.88 -> 1785.57, Atalanta 1720.12 -> 1722.43
```

Change `42` to another number to play the match again with another roll of the die.

---

## 7. What the code uses

### Python modules

| Module | Comes with Python? | What it does here |
|---|---|---|
| `math` | yes | `math.exp` for the three chances (step 2) |
| `json` | yes | reads the $K$ settings from `data/reference/coefs.json` |
| `functools` (`lru_cache`) | yes | reads `coefs.json` once, not once per season |
| `pathlib` | yes | the path to `coefs.json` |

It also uses three other parts of the project:

| From | What |
|---|---|
| `model/elo_score_updating.py` | `expected_score` and `update_rating` (step 5) |
| `model/predictor.py` | the match model (step 2) and `format_trace` for the log |
| `model/scorelines.py` | the score picker (step 4) and `outcome_of` |

### Functions and classes in `model/match_engine.py`

| Name | In one line |
|---|---|
| `MatchEngine` | holds everything a season needs: the ratings, the model, the score picker, the random generator, the log |
| `MatchEngine.play` | plays one match; chooses the fast or the full way |
| `MatchEngine._play_fast` | the five steps written in a few lines, used when nothing is logged (most of the time) |
| `MatchEngine._play_full` | the same five steps through the named functions, used in expert mode and for the final |
| `MatchEngine._log` | writes the expert log of one match |
| `MatchEngine.section`, `note` | add a title or a line to the log, only in expert mode |
| `Match` | a record of one played match and every number that produced it |
| `load_k_table` | reads the $K$ values of one competition (section 3) |

**Why two ways to play a match?** A simulation of 1 000 seasons plays about 189 000 matches, and this is where almost all the time goes. The fast way does the same maths in fewer steps and takes about 1.5 microseconds per match, against 3.4 for the full way and 16.8 with the log. Both use the random numbers in exactly the same order, so with the same seed they give exactly the same result.

How each line works: [`code/match_engine_code.md`](code/match_engine_code.md).

---

## 8. What can go wrong

- **The two models do not agree about home advantage.** The match model knows that playing at home helps; the Elo update does not (two equal clubs both expect 0.5). So the home side of a match between equal clubs gains about 1.7 rating points on average. In the league phase this cancels out (4 home and 4 away matches each). In a two-legged knockout tie it does not quite: the club that plays the first leg at home gains a little before the second leg. Over 60 000 simulated ties between equal clubs, the club hosting the second leg went through 49.1 % of the time instead of 50 %.
- **The score does not move the ratings.** A 5-0 and a 1-0 count the same.
- **Extra time and penalties do not move the ratings.** Only the 90-minute result counts.
- **The score does not depend on the rating gap**, only on the result (see [`scorelines.md`](scorelines.md)).
- **Three default ratings for one idea**: 1500 here and in the league table, 1450 in the Elo program.

### Known bugs

- **Not a bug any more: "the app needs pandas".** `elo_score_updating.py` imports pandas and numpy only inside `run()`, so this file can import its two Elo functions without them. Checked in 1.1.0: `model.simulation` imports with pandas and scikit-learn blocked, and the Windows build excludes both.
- **On the fast way, the chances are not stored** (`Match.probs` is `None`). Any future code that reads them from a normal simulated match would crash.

---

## 9. Ideas for later

- **Home advantage inside Elo**: give the home side about 50 to 70 extra points when computing the expected score, and none at the final. This would fix the small effect of section 8.
- **Let the score count a little**: make the rating step grow slowly with the goal difference, so a 4-0 counts more than a 1-0, but not four times more.

---

## 10. Words to know

| Word | Meaning |
|---|---|
| result (outcome) | home win, draw or away win after 90 minutes |
| score (scoreline) | the goals, home first: "2-1" |
| random number $u$ | a number between 0 and 1 where every value is equally likely |
| seed | the starting number of the random generator: same seed, same season |
| $K$ | how much one match can move a rating |
| neutral ground | a match where neither club is at home; here only the final |
| expert mode | a setting of the app that writes every number of every match to a log |

---
---

# Le moteur de match : un match simulé

> Cette partie joue **un** match de la simulation. Elle lit les notes des deux clubs, calcule les chances de chaque résultat, lance un dé pour choisir le résultat, choisit un score qui lui correspond, et met à jour les deux notes. La phase de ligue et les tours à élimination directe l'utilisent pour chaque match.

## En bref

- **Ce qui entre :** deux clubs, le tour (phase de ligue, quart de finale, ...), et si le terrain est neutre (seulement pour la finale).
- **Ce qui sort :** un match joué : le résultat, le score, chaque nombre utilisé, et les nouvelles notes des deux clubs.
- **Où c'est utilisé :** la phase de ligue ([`league_phase.md`](league_phase.md)) et les tours à élimination directe ([`knockout.md`](knockout.md)) l'appellent pour chaque match ; environ 189 fois par saison simulée de Ligue des champions.
- **Code :** `model/match_engine.py`. Explication ligne par ligne : [`code/match_engine_code.md`](code/match_engine_code.md).

---

## 1. Les cinq étapes

Chaque match simulé passe par les mêmes cinq étapes, toujours dans cet ordre :

| Étape | Ce qui se passe | Expliqué dans |
|---|---|---|
| 1 | lire les notes **actuelles** des deux clubs (elles changent pendant la saison) | [`elo.md`](elo.md) |
| 2 | transformer l'écart de notes en trois chances : victoire à domicile, nul, victoire à l'extérieur | [`logistic_regression.md`](logistic_regression.md) |
| 3 | lancer un dé pour choisir le résultat | section 2 ci-dessous |
| 4 | choisir un score qui correspond au résultat | [`scorelines.md`](scorelines.md) |
| 5 | mettre à jour les deux notes | section 3 ci-dessous |

En mode expert, chaque nombre de chaque étape est aussi écrit dans un journal, pour qu'une personne puisse suivre le match ligne par ligne.

---

## 2. Étape 3 : un nombre au hasard choisit le résultat

Imaginez une règle graduée de 0 à 1, coupée en trois morceaux. Chaque morceau est aussi long que la chance d'un résultat :

```
 0                       0.622        0.816               1
 |------ domicile -------|--- nul ----|---- extérieur ----|
```

Pour Arsenal qui reçoit l'Atalanta, les chances sont 62.2 % victoire à domicile, 19.4 % nul et 18.4 % victoire à l'extérieur. Le morceau « domicile » va donc de 0 à 0.622, le morceau « nul » de 0.622 à 0.816 (0.622 + 0.194), et le morceau « extérieur » de 0.816 à 1.

L'ordinateur tire ensuite un nombre au hasard $u$ entre 0 et 1, où toutes les valeurs ont la même chance, et regarde dans quel morceau il tombe :

| $u$ | Tombe dans | Résultat |
|---|---|---|
| 0.30 | le morceau « domicile » (sous 0.622) | Arsenal gagnent |
| 0.6394 | le morceau « nul » (entre 0.622 et 0.816) | nul |
| 0.90 | le morceau « extérieur » (au-dessus de 0.816) | l'Atalanta gagne |

Pourquoi est-ce juste ? Parce que la chance de tomber dans un morceau est exactement sa longueur. Sur beaucoup de matchs, $u$ tombe sous 0.622 dans 62.2 % d'entre eux, donc Arsenal gagnent 62.2 % du temps, exactement comme le modèle l'a dit.

---

## 3. Étape 5 : les deux notes bougent

Après le résultat, les deux notes bougent avec la règle d'Elo de [`elo.md`](elo.md), section 4. La taille du pas, $K$, dépend de la compétition et du tour :

| Compétition | phase de ligue | barrage | huitièmes | quarts | demies | finale |
|---|---|---|---|---|---|---|
| Ligue des champions | 24.00 | 24.72 | 25.44 | 25.92 | 26.40 | 26.88 |
| Ligue Europa | 22.40 | 23.07 | 23.74 | 24.19 | 24.64 | 25.09 |
| Ligue Conférence | 21.20 | 21.84 | 22.47 | 22.90 | 23.32 | 23.74 |

Ce qu'un club gagne, l'autre le perd : les deux changements font toujours 0 au total.

Ces nouvelles notes servent pour le **prochain** match du club dans la même saison. Un club qui enchaîne les victoires devient donc plus fort pendant la compétition, et un club qui perd sans arrêt devient plus faible. Chaque nouvelle saison simulée repart des notes d'origine.

---

## 4. Un exemple complet : Arsenal-Atalanta

Phase de ligue de Ligue des champions, avec le générateur de hasard démarré à partir du nombre 42. Voici le vrai journal expert :

```
-- MD1: Arsenal v Atalanta
   x = R_home - R_away = 1787.880 - 1720.120 = 67.760
   x' = (x - -0.151) / 88.495 = 0.767
   z_home = +0.5692 * x' +0.3562 = 0.793
   z_draw = -0.0308 * x' -0.3459 = -0.370
   z_away = -0.5384 * x' -0.0103 = -0.423
   p_home = 0.622   p_draw = 0.194   p_away = 0.184
   u = 0.6394  ->  DRAW  (home if u < 0.622, draw if u < 0.816, else away)
   scoreline 0-0  (P = 0.231 given draw)
   Elo: E_home = 1/(1+10^((1720.1-1787.9)/400)) = 0.596   S_home = 0.5   K = 24.00
        Arsenal: 1787.9 -> 1785.6 (-2.3)   Atalanta: 1720.1 -> 1722.4 (+2.3)
```

Ligne par ligne, avec des mots simples :

1. L'écart de notes vaut 67.76 points.
2. Le modèle le transforme en trois chances : 62.2 %, 19.4 %, 18.4 %.
3. Le nombre au hasard vaut 0.6394 : au-dessus de 0.622, sous 0.816, donc le résultat est un **nul**.
4. Parmi les vrais nuls, 0-0 arrive 23.1 % du temps ; cette fois le score est 0-0.
5. Arsenal devaient prendre 0.596 du point et n'ont pris que 0.5, donc ils perdent 2.3 points ; l'Atalanta en gagne 2.3.

Si $u$ avait valu 0.30, Arsenal auraient gagné et pris 9.70 points. S'il avait valu 0.90, l'Atalanta aurait gagné et Arsenal auraient perdu 14.30. Un favori perd plus pour une défaite qu'il ne gagne pour une victoire, car la victoire était attendue.

---

## 5. La finale, sur terrain neutre

Le modèle de match a appris sur de vrais matchs, où l'équipe à domicile a un avantage. Une finale se joue dans un stade neutre, donc personne ne devrait avoir cet avantage. Pour la finale, le moteur interroge le modèle deux fois, une fois avec chaque club « à domicile », et fait la moyenne ([`logistic_regression.md`](logistic_regression.md), section 9). Pour Arsenal et l'Atalanta : 54.8 % Arsenal, 21.2 % nul, 23.9 % Atalanta.

---

## 6. À essayer en Python

Un match, des notes aux nouvelles notes, avec les vrais nombres du modèle de match.

```python
import math
import random

# Les 8 nombres du modèle de match (voir logistic_regression.md)
AVERAGE_GAP, TYPICAL_GAP = -0.1508, 88.4953
SLOPE = {"home": 0.5692, "draw": -0.0308, "away": -0.5384}
START = {"home": 0.3562, "draw": -0.3459, "away": -0.0103}

# Combien de fois chaque score est arrivé dans de vrais matchs (les principaux ; la vraie table les a tous)
SCORES = {"home": {(1, 0): 377, (2, 0): 341, (2, 1): 399, (3, 0): 212, (3, 1): 204},
          "draw": {(0, 0): 225, (1, 1): 458, (2, 2): 237, (3, 3): 50, (4, 4): 5},
          "away": {(0, 1): 321, (0, 2): 237, (1, 2): 322, (0, 3): 136, (1, 3): 139}}

def play(home, away, ratings, k, rng):
    r_home, r_away = ratings[home], ratings[away]
    # 1. trois chances
    x = (r_home - r_away - AVERAGE_GAP) / TYPICAL_GAP
    powered = {o: math.exp(SLOPE[o] * x + START[o]) for o in SLOPE}
    total = sum(powered.values())
    p = {o: v / total for o, v in powered.items()}
    # 2. un nombre au hasard choisit le résultat
    u = rng.random()
    if u < p["home"]:
        result = "home"
    elif u < p["home"] + p["draw"]:
        result = "draw"
    else:
        result = "away"
    # 3. un score pour ce résultat, choisi selon sa fréquence réelle
    table = SCORES[result]
    goals = rng.choices(list(table), weights=list(table.values()))[0]
    # 4. mise à jour Elo
    e_home = 1 / (1 + 10 ** ((r_away - r_home) / 400))
    s_home = {"home": 1.0, "draw": 0.5, "away": 0.0}[result]
    ratings[home] = r_home + k * (s_home - e_home)
    ratings[away] = r_away - k * (s_home - e_home)
    print(f"chances {p['home']:.3f} / {p['draw']:.3f} / {p['away']:.3f}, u = {u:.4f} -> {result}")
    print(f"{home} {goals[0]}-{goals[1]} {away}")
    print(f"{home} {r_home:.2f} -> {ratings[home]:.2f}, {away} {r_away:.2f} -> {ratings[away]:.2f}")

ratings = {"Arsenal": 1787.88, "Atalanta": 1720.12}
play("Arsenal", "Atalanta", ratings, k=24, rng=random.Random(42))
```

Résultat (le même que le journal du vrai moteur plus haut) :

```
chances 0.622 / 0.194 / 0.184, u = 0.6394 -> draw
Arsenal 0-0 Atalanta
Arsenal 1787.88 -> 1785.57, Atalanta 1720.12 -> 1722.43
```

Remplacez `42` par un autre nombre pour rejouer le match avec un autre lancer de dé.

---

## 7. Ce que le code utilise

### Modules Python

| Module | Fourni avec Python ? | Ce qu'il fait ici |
|---|---|---|
| `math` | oui | `math.exp` pour les trois chances (étape 2) |
| `json` | oui | lit les réglages de $K$ dans `data/reference/coefs.json` |
| `functools` (`lru_cache`) | oui | lit `coefs.json` une fois, pas une fois par saison |
| `pathlib` | oui | le chemin de `coefs.json` |

Il utilise aussi trois autres parties du projet :

| Depuis | Quoi |
|---|---|
| `model/elo_score_updating.py` | `expected_score` et `update_rating` (étape 5) |
| `model/predictor.py` | le modèle de match (étape 2) et `format_trace` pour le journal |
| `model/scorelines.py` | le tireur de scores (étape 4) et `outcome_of` |

### Fonctions et classes de `model/match_engine.py`

| Nom | En une ligne |
|---|---|
| `MatchEngine` | garde tout ce dont une saison a besoin : les notes, le modèle, le tireur de scores, le générateur de hasard, le journal |
| `MatchEngine.play` | joue un match ; choisit le chemin rapide ou le chemin complet |
| `MatchEngine._play_fast` | les cinq étapes écrites en quelques lignes, utilisées quand rien n'est journalisé (la plupart du temps) |
| `MatchEngine._play_full` | les mêmes cinq étapes par les fonctions nommées, utilisées en mode expert et pour la finale |
| `MatchEngine._log` | écrit le journal expert d'un match |
| `MatchEngine.section`, `note` | ajoutent un titre ou une ligne au journal, seulement en mode expert |
| `Match` | une fiche d'un match joué et de chaque nombre qui l'a produit |
| `load_k_table` | lit les valeurs de $K$ d'une compétition (section 3) |

**Pourquoi deux façons de jouer un match ?** Une simulation de 1 000 saisons joue environ 189 000 matchs, et c'est là que passe presque tout le temps. Le chemin rapide fait les mêmes calculs en moins d'étapes et prend environ 1.5 microseconde par match, contre 3.4 pour le chemin complet et 16.8 avec le journal. Les deux utilisent les nombres au hasard exactement dans le même ordre, donc avec la même graine ils donnent exactement le même résultat.

Comment marche chaque ligne : [`code/match_engine_code.md`](code/match_engine_code.md).

---

## 8. Ce qui peut mal tourner

- **Les deux modèles ne sont pas d'accord sur l'avantage du terrain.** Le modèle de match sait que jouer à domicile aide ; la mise à jour Elo, non (deux clubs égaux attendent tous deux 0.5). L'équipe à domicile d'un match entre clubs égaux gagne donc en moyenne environ 1.7 point de note. En phase de ligue, cela s'annule (4 matchs à domicile et 4 à l'extérieur chacun). En match aller-retour, pas tout à fait : le club qui reçoit au match aller gagne un peu avant le retour. Sur 60 000 confrontations simulées entre clubs égaux, le club qui reçoit au retour s'est qualifié 49.1 % du temps au lieu de 50 %.
- **Le score ne fait pas bouger les notes.** Un 5-0 et un 1-0 comptent pareil.
- **La prolongation et les tirs au but ne font pas bouger les notes.** Seul le résultat après 90 minutes compte.
- **Le score ne dépend pas de l'écart de notes**, seulement du résultat (voir [`scorelines.md`](scorelines.md)).
- **Trois notes par défaut pour une même idée** : 1500 ici et dans le classement, 1450 dans le programme Elo.

### Bugs connus

- **Ce n'est plus un bug : « l'appli a besoin de pandas ».** `elo_score_updating.py` n'importe pandas et numpy qu'à l'intérieur de `run()`, donc ce fichier peut importer ses deux fonctions Elo sans eux. Vérifié en 1.1.0 : `model.simulation` s'importe avec pandas et scikit-learn bloqués, et la version Windows les exclut tous les deux.
- **Sur le chemin rapide, les chances ne sont pas gardées** (`Match.probs` vaut `None`). Tout code futur qui les lirait sur un match simulé normal planterait.

---

## 9. Idées pour plus tard

- **L'avantage du terrain dans Elo** : donner environ 50 à 70 points de plus à l'équipe à domicile pour calculer le score attendu, et rien pour la finale. Cela corrigerait le petit effet de la section 8.
- **Faire un peu compter le score** : faire grandir le pas de note doucement avec la différence de buts, pour qu'un 4-0 compte plus qu'un 1-0, mais pas quatre fois plus.

---

## 10. Mots à connaître

| Mot | Sens |
|---|---|
| résultat | victoire à domicile, nul ou victoire à l'extérieur après 90 minutes |
| score | les buts, domicile d'abord : « 2-1 » |
| nombre au hasard $u$ | un nombre entre 0 et 1 où toutes les valeurs ont la même chance |
| graine (seed) | le nombre de départ du générateur de hasard : même graine, même saison |
| $K$ | de combien un match peut faire bouger une note |
| terrain neutre | un match où aucun club n'est à domicile ; ici seulement la finale |
| mode expert | un réglage de l'appli qui écrit chaque nombre de chaque match dans un journal |

---