# Extra time

> When a knockout tie is still level after 90 minutes, 30 more minutes are played. This part makes up the score of those 30 minutes. If it is still level after that, there is a penalty shoot-out ([`penalties.md`](penalties.md)).

*Version française : [plus bas](#la-prolongation).*

## In short

- **What goes in:** a tie that is level after 90 minutes.
- **What comes out:** the score of the 30 minutes of extra time, for example 1-0, or 0-0 (then penalties).
- **Code:** `sample_extra_time` in `model/scorelines.py` and `_settle_level` in `model/knockout.py`. Line by line: [`code/scorelines_code.md`](code/scorelines_code.md) (part 7) and [`code/knockout_code.md`](code/knockout_code.md) (part 6).

---

## 1. When is extra time played?

| Situation | "legs" (default) | "aggregate" | "oneshot" |
|---|---|---|---|
| a two-legged tie is level | no: the winner is picked with the ratings, then a shoot-out | **yes**, then penalties | impossible: one random number decides |
| the final is level after 90 minutes | **yes**, then penalties | **yes**, then penalties | **yes**, then penalties |

The three methods are explained in [`knockout.md`](knockout.md), section 3.

---

## 2. The idea: a third of a match

Extra time is two halves of 15 minutes: 30 minutes, a **third** of a normal 90-minute match. So, on average, it should see about a third of the goals of a match.

The trick the program uses:

1. Pick an ordinary full-match score, as for a normal match ([`scorelines.md`](scorelines.md)), for example 2-1.
2. For **each goal** of that score, roll a die: keep the goal only on a 1 or a 2 (a chance of 1 in 3). Otherwise, drop it.
3. The goals that survive are the extra-time score.

This is called **thinning**: you take something real and keep each piece with the same small chance. If goals arrive at random at a steady pace, keeping a third of a match's goals gives exactly what 30 minutes would give.

Example: a side that scores 1.5 goals per match on average keeps 1.5 ÷ 3 = 0.5 goals on average in extra time.

### A 2-1 thinned, by hand

The home side has 2 goals to roll for, the away side 1:

| Extra-time score | How | Chance |
|---|---|---|
| 0-0 | drop both home goals, drop the away goal | 8 in 27 = 29.6 % |
| 1-0 | keep exactly one home goal, drop the away goal | 8 in 27 = 29.6 % |
| 1-1 | keep one home goal, keep the away goal | 4 in 27 = 14.8 % |
| 0-1 | drop both home goals, keep the away goal | 4 in 27 = 14.8 % |
| 2-0 | keep both home goals, drop the away goal | 2 in 27 = 7.4 % |
| 2-1 | keep all three | 1 in 27 = 3.7 % |

The six add up to 27 in 27. So a 2-1 is still level after thinning 12 times in 27 (0-0 or 1-1), and becomes an away win 4 times in 27: thinning shuffles the result a lot.

---

## 3. Try it in Python

Thin a 2-1 many times and count the results: they should match the table above.

```python
import random
from collections import Counter

def thin(goals, keep, rng):
    """Keep each goal with chance `keep`; return how many survive."""
    return sum(1 for _ in range(goals) if rng.random() < keep)

rng = random.Random(7)
results = Counter()
for _ in range(27_000):
    home, away = thin(2, 1 / 3, rng), thin(1, 1 / 3, rng)    # thin a 2-1
    results[f"{home}-{away}"] += 1

for score, n in sorted(results.items(), key=lambda item: -item[1]):
    print(score, n, f"{n / 27_000:.3f}")
```

Output:

```
1-0 7966 0.295
0-0 7918 0.293
0-1 4091 0.152
1-1 3995 0.148
2-0 2031 0.075
2-1 999 0.037
```

The shares are close to 0.296, 0.296, 0.148, 0.148, 0.074 and 0.037: the table of section 2.

---

## 4. The whole process

`sample_extra_time` does three things:

1. Pick a result, home win, draw or away win, **one third each**. It does not look at the ratings.
2. Pick a full-match score for that result, from the real table.
3. Thin it, one die roll per goal.

Over all possible scores, extra time ends:

| Score | 0-0 | 1-0 | 0-1 | 1-1 | 2-0 | 0-2 | 2-1 | 1-2 | others |
|---|---|---|---|---|---|---|---|---|---|
| Chance | 38.8 % | 18.1 % | 18.0 % | 8.4 % | 4.8 % | 4.5 % | 1.9 % | 1.9 % | 3.6 % |

- Still level (then penalties): **47.6 %**. Decided in extra time: 52.4 %.
- Average goals in extra time: 0.96.

The ratings are **not** updated after extra time: the Elo step was already taken on the 90-minute result.

---

## 5. Against real extra times

The real data has 92 matches that went to extra time:

| | Real (92 matches) | Simulation |
|---|---|---|
| 0-0 | 46.7 % | 38.8 % |
| still level, so penalties | 51.1 % | 47.6 % |
| average goals | 0.83 | 0.96 |
| the home side wins it | 33.7 % | 26.5 % |
| the away side wins it | 15.2 % | 25.9 % |

With only 92 matches, real numbers carry a lot of luck (about ±5 percentage points), so the "still level" line agrees well enough. Two differences look real:

- Real extra time has **fewer goals** than a third of a match: tired players, teams afraid to lose. Keeping about 29 % of the goals instead of 33 % would match the real average.
- In real matches, the **home side wins extra time about twice as often** as the visitor. The simulation treats them almost alike.

### How often extra time happens

Measured over 40 000 ties between two equal clubs:

| | goes to extra time | goes to penalties |
|---|---|---|
| a final (one match) | 23.0 % | 11.0 % |
| a two-legged tie, "aggregate" | 12.9 % | 6.1 % |

Penalties happen when extra time is level, about 47.6 % of the time: 23.0 % × 0.476 = 11.0 %.

---

## 6. What the code uses

| Module | Comes with Python? | What it does here |
|---|---|---|
| `random` (through the season's generator) | yes | the result, the score, and one die roll per goal |

| Function | File | In one line |
|---|---|---|
| `ScorelineSampler.sample_extra_time` | `model/scorelines.py` | the three steps of section 4 |
| `_settle_level` | `model/knockout.py` | plays extra time, decides the tie or calls the shoot-out |
| `describe_tie` | `model/simulation.py` | writes "aet 1-0" ("after extra time") in the summary |

The app's bracket adds the extra-time goals to the second leg's score, and the tie's detail card shows an "extra time" line.

---

## 7. What can go wrong

- **Extra time ignores the ratings.** The result is picked one third each, so a big favourite and an outsider are equally likely to win the 30 minutes.
- **No home advantage in extra time**, while real data suggests the home side wins it twice as often.
- **Slightly too many goals** (0.96 against 0.83), so slightly too few shoot-outs.
- **No extra time in two-legged ties under "legs"**, on purpose: a level tie goes straight to the rating pick and a shoot-out.

### Known bugs

- **The Elo program and the simulation disagree about extra time.** The program that computes the real ratings counts extra-time goals: 45 real cup matches decided in extra time count as wins. The simulation treats the same kind of match as a draw after 90 minutes. Small (45 of 4 626 matches), but the two should follow one rule. Fix: make the Elo program use the 90-minute score, then recompute the ratings and retrain the match model.

---

## 8. Ideas for later

- **Use the match model for extra time**, instead of one third each, so the stronger club and the home side get their edge.
- **Keep 29 % of the goals instead of 33 %**, to match the real average.
- **A goals model** ([`scorelines.md`](scorelines.md), section 8) would handle extra time naturally: a third of each side's average goals, times a small tiredness factor.

---

## 9. Words to know

| Word | Meaning |
|---|---|
| extra time | two halves of 15 minutes, played when a knockout tie is level after 90 minutes |
| aet | "after extra time", how a score including extra time is written |
| thinning | keeping each event with the same small chance and dropping the rest |
| shoot-out | the penalties that decide a tie still level after extra time |


---
---

# La prolongation

> Quand une confrontation à élimination directe est toujours à égalité après 90 minutes, on joue 30 minutes de plus. Cette partie invente le score de ces 30 minutes. Si l'égalité dure encore, il y a une séance de tirs au but ([`penalties.md`](penalties.md)).

## En bref

- **Ce qui entre :** une confrontation à égalité après 90 minutes.
- **Ce qui sort :** le score des 30 minutes de prolongation, par exemple 1-0, ou 0-0 (puis tirs au but).
- **Code :** `sample_extra_time` dans `model/scorelines.py` et `_settle_level` dans `model/knockout.py`. Ligne par ligne : [`code/scorelines_code.md`](code/scorelines_code.md) (partie 7) et [`code/knockout_code.md`](code/knockout_code.md) (partie 6).

---

## 1. Quand joue-t-on une prolongation ?

| Situation | « legs » (par défaut) | « aggregate » | « oneshot » |
|---|---|---|---|
| une confrontation aller-retour est à égalité | non : le vainqueur est choisi avec les notes, puis une séance de tirs au but | **oui**, puis tirs au but | impossible : un seul nombre au hasard décide |
| la finale est à égalité après 90 minutes | **oui**, puis tirs au but | **oui**, puis tirs au but | **oui**, puis tirs au but |

Les trois méthodes sont expliquées dans [`knockout.md`](knockout.md), section 3.

---

## 2. L'idée : un tiers de match

La prolongation, c'est deux mi-temps de 15 minutes : 30 minutes, un **tiers** d'un match normal de 90 minutes. Elle devrait donc voir en moyenne environ un tiers des buts d'un match.

L'astuce du programme :

1. Choisir un score de match complet ordinaire, comme pour un match normal ([`scorelines.md`](scorelines.md)), par exemple 2-1.
2. Pour **chaque but** de ce score, lancer un dé : garder le but seulement sur un 1 ou un 2 (une chance sur 3). Sinon, l'enlever.
3. Les buts qui restent forment le score de la prolongation.

On appelle cela un **amincissement** (*thinning*) : on prend quelque chose de réel et on garde chaque morceau avec la même petite chance. Si les buts arrivent au hasard à un rythme régulier, garder un tiers des buts d'un match donne exactement ce que donneraient 30 minutes.

Exemple : une équipe qui marque en moyenne 1.5 but par match garde en moyenne 1.5 ÷ 3 = 0.5 but en prolongation.

### Un 2-1 aminci, à la main

L'équipe à domicile a 2 buts à tenter, celle à l'extérieur 1 :

| Score de prolongation | Comment | Chance |
|---|---|---|
| 0-0 | enlever les deux buts à domicile, enlever le but à l'extérieur | 8 sur 27 = 29.6 % |
| 1-0 | garder exactement un but à domicile, enlever le but à l'extérieur | 8 sur 27 = 29.6 % |
| 1-1 | garder un but à domicile, garder le but à l'extérieur | 4 sur 27 = 14.8 % |
| 0-1 | enlever les deux buts à domicile, garder le but à l'extérieur | 4 sur 27 = 14.8 % |
| 2-0 | garder les deux buts à domicile, enlever le but à l'extérieur | 2 sur 27 = 7.4 % |
| 2-1 | garder les trois | 1 sur 27 = 3.7 % |

Les six font 27 sur 27. Un 2-1 reste donc à égalité après amincissement 12 fois sur 27 (0-0 ou 1-1), et devient une victoire à l'extérieur 4 fois sur 27 : l'amincissement mélange beaucoup le résultat.

---

## 3. À essayer en Python

Amincir un 2-1 de nombreuses fois et compter les résultats : ils devraient correspondre au tableau ci-dessus.

```python
import random
from collections import Counter

def thin(goals, keep, rng):
    """Garder chaque but avec la chance `keep` ; renvoyer combien restent."""
    return sum(1 for _ in range(goals) if rng.random() < keep)

rng = random.Random(7)
results = Counter()
for _ in range(27_000):
    home, away = thin(2, 1 / 3, rng), thin(1, 1 / 3, rng)    # amincir un 2-1
    results[f"{home}-{away}"] += 1

for score, n in sorted(results.items(), key=lambda item: -item[1]):
    print(score, n, f"{n / 27_000:.3f}")
```

Résultat :

```
1-0 7966 0.295
0-0 7918 0.293
0-1 4091 0.152
1-1 3995 0.148
2-0 2031 0.075
2-1 999 0.037
```

Les parts sont proches de 0.296, 0.296, 0.148, 0.148, 0.074 et 0.037 : le tableau de la section 2.

---

## 4. Tout le processus

`sample_extra_time` fait trois choses :

1. Choisir un résultat, victoire à domicile, nul ou victoire à l'extérieur, **un tiers chacun**. Il ne regarde pas les notes.
2. Choisir un score de match complet pour ce résultat, dans la vraie table.
3. L'amincir, un lancer de dé par but.

Sur tous les scores possibles, la prolongation finit :

| Score | 0-0 | 1-0 | 0-1 | 1-1 | 2-0 | 0-2 | 2-1 | 1-2 | autres |
|---|---|---|---|---|---|---|---|---|---|
| Chance | 38.8 % | 18.1 % | 18.0 % | 8.4 % | 4.8 % | 4.5 % | 1.9 % | 1.9 % | 3.6 % |

- Toujours à égalité (puis tirs au but) : **47.6 %**. Décidée en prolongation : 52.4 %.
- Nombre moyen de buts en prolongation : 0.96.

Les notes ne sont **pas** mises à jour après la prolongation : le pas Elo a déjà été fait sur le résultat après 90 minutes.

---

## 5. Face aux vraies prolongations

Les vraies données contiennent 92 matchs allés en prolongation :

| | Réel (92 matchs) | Simulation |
|---|---|---|
| 0-0 | 46.7 % | 38.8 % |
| toujours à égalité, donc tirs au but | 51.1 % | 47.6 % |
| buts en moyenne | 0.83 | 0.96 |
| l'équipe à domicile la gagne | 33.7 % | 26.5 % |
| l'équipe à l'extérieur la gagne | 15.2 % | 25.9 % |

Avec seulement 92 matchs, les vrais nombres contiennent beaucoup de hasard (environ ±5 points de pourcentage), donc la ligne « toujours à égalité » est assez d'accord. Deux différences semblent réelles :

- Les vraies prolongations ont **moins de buts** qu'un tiers de match : joueurs fatigués, équipes qui ont peur de perdre. Garder environ 29 % des buts au lieu de 33 % correspondrait à la vraie moyenne.
- Dans les vrais matchs, **l'équipe à domicile gagne la prolongation environ deux fois plus souvent** que l'équipe visiteuse. La simulation les traite presque pareil.

### À quelle fréquence il y a prolongation

Mesuré sur 40 000 confrontations entre deux clubs égaux :

| | va en prolongation | va aux tirs au but |
|---|---|---|
| une finale (un match) | 23.0 % | 11.0 % |
| une confrontation aller-retour, « aggregate » | 12.9 % | 6.1 % |

Les tirs au but arrivent quand la prolongation finit à égalité, environ 47.6 % du temps : 23.0 % × 0.476 = 11.0 %.

---

## 6. Ce que le code utilise

| Module | Fourni avec Python ? | Ce qu'il fait ici |
|---|---|---|
| `random` (par le générateur de la saison) | oui | le résultat, le score, et un lancer de dé par but |

| Fonction | Fichier | En une ligne |
|---|---|---|
| `ScorelineSampler.sample_extra_time` | `model/scorelines.py` | les trois étapes de la section 4 |
| `_settle_level` | `model/knockout.py` | joue la prolongation, décide la confrontation ou lance les tirs au but |
| `describe_tie` | `model/simulation.py` | écrit « aet 1-0 » (*after extra time*, après prolongation) dans le résumé |

Le tableau de l'appli ajoute les buts de prolongation au score du match retour, et la fiche détaillée de la confrontation affiche une ligne « prolongation ».

---

## 7. Ce qui peut mal tourner

- **La prolongation ignore les notes.** Le résultat est choisi un tiers chacun, donc un grand favori et un outsider ont autant de chances de gagner les 30 minutes.
- **Pas d'avantage du terrain en prolongation**, alors que les vraies données suggèrent que l'équipe à domicile la gagne deux fois plus souvent.
- **Un peu trop de buts** (0.96 contre 0.83), donc un peu trop peu de tirs au but.
- **Pas de prolongation en aller-retour avec « legs »**, exprès : une égalité va directement au tirage selon les notes et aux tirs au but.

### Bugs connus

- **Le programme Elo et la simulation ne sont pas d'accord sur la prolongation.** Le programme qui calcule les vraies notes compte les buts de prolongation : 45 vrais matchs de coupe décidés en prolongation comptent comme des victoires. La simulation traite le même genre de match comme un nul après 90 minutes. C'est peu (45 matchs sur 4 626), mais les deux devraient suivre une seule règle. Correction : faire utiliser au programme Elo le score après 90 minutes, puis recalculer les notes et réentraîner le modèle de match.

---

## 8. Idées pour plus tard

- **Utiliser le modèle de match pour la prolongation**, au lieu d'un tiers chacun, pour que le club le plus fort et l'équipe à domicile gardent leur avantage.
- **Garder 29 % des buts au lieu de 33 %**, pour correspondre à la vraie moyenne.
- **Un modèle de buts** ([`scorelines.md`](scorelines.md), section 8) gérerait naturellement la prolongation : un tiers des buts moyens de chaque équipe, multiplié par un petit facteur de fatigue.

---

## 9. Mots à connaître

| Mot | Sens |
|---|---|
| prolongation | deux mi-temps de 15 minutes, jouées quand une confrontation à élimination directe est à égalité après 90 minutes |
| aet | *after extra time*, après prolongation : la façon d'écrire un score qui inclut la prolongation |
| amincissement | garder chaque événement avec la même petite chance et enlever le reste |
| tirs au but | la séance qui décide une confrontation encore à égalité après la prolongation |

---
