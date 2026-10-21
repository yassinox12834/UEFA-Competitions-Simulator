# The league phase: the matches and the table

> This part plays every match of the league phase, day by day, then ranks the 36 clubs in one table with UEFA's rules. The table decides who goes straight to the round of 16, who plays a play-off, and who is out.

*Version française : [plus bas](#la-phase-de-ligue--les-matchs-et-le-classement).*

## In short

- **What goes in:** the matchdays ([`matchdays.md`](matchdays.md)): 8 days of 18 matches (6 days for the Conference League).
- **What comes out:** every played match, and the table from 1st to 36th.
- **What the table decides:** 1st to 8th go straight to the round of 16; 9th to 24th play a two-legged play-off ([`knockout.md`](knockout.md)); 25th to 36th are out.
- **Code:** `model/league_phase.py`. Line-by-line walkthrough: [`code/league_phase_code.md`](code/league_phase_code.md).

---

## 1. Playing the matches

The days are played in order, and inside each day the matches are played one by one through the match engine ([`match_engine.md`](match_engine.md)). Ratings change after every match, so a club that wins on day 1 is a little stronger on day 2.

Inside a day, the matches are always played in alphabetical order. That way the same seed always gives the same season, which is the only way to reproduce a problem and fix it.

---

## 2. Points

As in every football league: **3 points for a win, 1 for a draw, 0 for a defeat.**

A club with 5 wins, 2 draws and 1 defeat has 3 × 5 + 2 = 17 points.

---

## 3. When clubs are level on points: the tiebreakers

With 36 clubs and only 8 matches each, many clubs end on the same number of points. UEFA then looks at other numbers, **one after the other**, until one is different:

| Order | Tiebreaker | In words |
|---|---|---|
| 1 | points | |
| 2 | goal difference | goals scored minus goals conceded |
| 3 | goals scored | |
| 4 | away goals scored | goals scored in away matches only |
| 5 | wins | |
| 6 | away wins | |
| 7 | opponents' points | add up the final points of the 8 clubs this club played: a harder set of opponents ranks higher |
| 8 | rating before the competition | in real life this is UEFA's club coefficient (past European results); here the club's Elo rating **before** the first match is used instead |

Two UEFA rules are left out: the opponents' goal difference and goals (they almost never decide anything), and disciplinary points (cards are not simulated). There is no head-to-head rule: in this format each pair of clubs meets at most once, so UEFA does not use it.

**Why the rating from before the competition?** The rating at the end of the league phase already contains this phase's results. Using it would let a club's results count twice: once in the points, and again in the last tiebreaker.

### How the program ranks: like a dictionary

The program gives each club a list of its numbers in that order, for example (17, 8, 15, ...) for 17 points, +8 goal difference, 15 goals, and sorts the clubs by those lists, biggest first.

Python compares two lists the way a dictionary orders words: first letters first; only if they are equal, the second letters; and so on. "car" comes before "cat" because "r" comes before "t", and the first two letters are equal.

So a later tiebreaker can only separate clubs that are equal on every earlier one, exactly like UEFA's rules.

---

## 4. A full example by hand

Four clubs, two days:

| Day | Matches |
|---|---|
| 1 | A 2-0 B, C 1-1 D |
| 2 | B 0-3 C, D 1-1 A |

| Club | Won | Drawn | Lost | Scored | Conceded | Goal difference | Points |
|---|---|---|---|---|---|---|---|
| C | 1 | 1 | 0 | 4 | 1 | +3 | 4 |
| A | 1 | 1 | 0 | 3 | 1 | +2 | 4 |
| D | 0 | 2 | 0 | 2 | 2 | 0 | 2 |
| B | 0 | 0 | 2 | 0 | 5 | −5 | 0 |

A and C both have 4 points. C has the better goal difference (+3 against +2), so **C is first**. The program's log explains it in one line: `1. C ahead of 2. A: level on points, split by goal difference (3 v 2)`.

---

## 5. Try it in Python

The same four clubs, ranked by points, then goal difference, then goals.

```python
matches = [("A", 2, 0, "B"), ("C", 1, 1, "D"),     # day 1: A 2-0 B, C 1-1 D
           ("B", 0, 3, "C"), ("D", 1, 1, "A")]     # day 2: B 0-3 C, D 1-1 A

table = {club: {"pts": 0, "gf": 0, "ga": 0} for club in "ABCD"}
for home, hg, ag, away in matches:
    for club, scored, conceded in ((home, hg, ag), (away, ag, hg)):
        row = table[club]
        row["gf"] += scored
        row["ga"] += conceded
        row["pts"] += 3 if scored > conceded else 1 if scored == conceded else 0

def sort_key(club):
    row = table[club]
    return (row["pts"], row["gf"] - row["ga"], row["gf"])   # points, then goal difference, then goals

for rank, club in enumerate(sorted(table, key=sort_key, reverse=True), start=1):
    row = table[club]
    print(rank, club, row["pts"], "pts", f"GD {row['gf'] - row['ga']:+d}", "key =", sort_key(club))
```

Output:

```
1 C 4 pts GD +3 key = (4, 3, 4)
2 A 4 pts GD +2 key = (4, 2, 3)
3 D 2 pts GD +0 key = (2, 0, 2)
4 B 0 pts GD -5 key = (0, -5, 0)
```

C and A have the same first number (4), so Python looks at the second: 3 is bigger than 2, so C comes first.

---

## 6. How often each tiebreaker decides

Measured over 2 000 simulated league phases. Take every pair of clubs next to each other in the final table (1st and 2nd, 2nd and 3rd, and so on):

| | Champions League | Conference League |
|---|---|---|
| neighbours level on points | 52.5 % of pairs | 60.0 % |
| ... then separated by goal difference | 85.7 % of those | 81.5 % |
| by goals scored | 12.5 % | 15.6 % |
| by away goals | 1.5 % | 2.4 % |
| by any later tiebreaker | less than 0.5 % | less than 0.6 % |

Goal difference does almost all the work. And at the two important cut lines (8th/9th and 24th/25th), the two clubs are level on points more than half the time: who goes straight through and who is out is often decided by a tiebreaker, not by points.

| | 8th place, average points | 24th place, average points |
|---|---|---|
| Champions League (8 matches) | 16.1 | 8.8 |
| Conference League (6 matches) | 12.3 | 6.4 |

---

## 7. What the code uses

### Python modules

None. This file only uses Python itself (classes, lists, dictionaries, `sorted`).

### Functions and classes in `model/league_phase.py`

| Name | In one line |
|---|---|
| `play_league_phase` | plays every match of every day, in order |
| `build_table` | adds up every club's results and ranks the clubs |
| `Row` | one club's line in the table: played, won, drawn, lost, goals, points, ... |
| `Row.record` | adds one match to a club's line |
| `Row.sort_key` | the list of numbers used to rank (section 3) |
| `explain_ties` | writes, for each pair level on points, which tiebreaker separated them |
| `format_table` | writes the table as plain text for the log |

The app draws the coloured table (top 8, 9 to 24, out) in `interface/canvas_views.py`.

How each line works: [`code/league_phase_code.md`](code/league_phase_code.md).

---

## 8. What can go wrong

- **Goal difference says little about strength** in the simulation, because the score picker ignores the rating gap ([`scorelines.md`](scorelines.md), section 5). And goal difference decides about 86 % of the ties.
- **Two UEFA tiebreakers are skipped** (opponents' goal difference and goals, disciplinary points). They almost never matter.
- **The default rating for an unknown club is 1500 here**, written directly in this file, while another part of the project uses 1450.

### Known bugs

- **The log gives the wrong reason for a perfect tie.** For two clubs equal on every tiebreaker, the log says "alphabetical order", but the real order is the order of the pots (Python's sort keeps the original order of equal items). Fix the text to "pot order".

---

## 9. Ideas for later

- **Show the reason on screen**: a small mark next to the points in the app's table saying which tiebreaker separated two clubs (the program already knows it for the log).
- **Better goal differences** would come from a better score picker, not from this file.

---

## 10. Words to know

| Word | Meaning |
|---|---|
| league phase | the first stage: 36 clubs in one table, 8 matches each (6 in the Conference League) |
| tiebreaker | a rule used, in order, to separate clubs level on points |
| goal difference | goals scored minus goals conceded |
| club coefficient | UEFA's ranking of a club from its European results over five seasons; replaced here by the rating before the competition |
| cut line | the border between two fates in the table: 8th/9th and 24th/25th |

---
---

# La phase de ligue : les matchs et le classement

> Cette partie joue chaque match de la phase de ligue, journée par journée, puis classe les 36 clubs dans un seul tableau avec les règles de l'UEFA. Le classement décide qui va directement en huitièmes, qui joue un barrage, et qui est éliminé.

## En bref

- **Ce qui entre :** les journées ([`matchdays.md`](matchdays.md)) : 8 journées de 18 matchs (6 journées pour la Ligue Conférence).
- **Ce qui sort :** chaque match joué, et le classement du 1er au 36e.
- **Ce que décide le classement :** du 1er au 8e, directement en huitièmes de finale ; du 9e au 24e, un barrage aller-retour ([`knockout.md`](knockout.md)) ; du 25e au 36e, éliminés.
- **Code :** `model/league_phase.py`. Explication ligne par ligne : [`code/league_phase_code.md`](code/league_phase_code.md).

---

## 1. Jouer les matchs

Les journées sont jouées dans l'ordre, et dans chaque journée les matchs sont joués un par un par le moteur de match ([`match_engine.md`](match_engine.md)). Les notes changent après chaque match, donc un club qui gagne la journée 1 est un peu plus fort la journée 2.

Dans une journée, les matchs sont toujours joués dans l'ordre alphabétique. Ainsi la même graine donne toujours la même saison, ce qui est le seul moyen de reproduire un problème pour le corriger.

---

## 2. Les points

Comme dans tout championnat : **3 points pour une victoire, 1 pour un nul, 0 pour une défaite.**

Un club avec 5 victoires, 2 nuls et 1 défaite a 3 × 5 + 2 = 17 points.

---

## 3. Quand des clubs sont à égalité de points : les critères de départage

Avec 36 clubs et seulement 8 matchs chacun, beaucoup de clubs finissent avec le même nombre de points. L'UEFA regarde alors d'autres nombres, **l'un après l'autre**, jusqu'à ce qu'un soit différent :

| Ordre | Critère | En mots |
|---|---|---|
| 1 | points | |
| 2 | différence de buts | buts marqués moins buts encaissés |
| 3 | buts marqués | |
| 4 | buts marqués à l'extérieur | buts marqués dans les matchs à l'extérieur seulement |
| 5 | victoires | |
| 6 | victoires à l'extérieur | |
| 7 | points des adversaires | additionner les points finaux des 8 clubs affrontés : des adversaires plus durs font monter le club |
| 8 | note avant la compétition | en vrai, c'est le coefficient UEFA du club (résultats européens passés) ; ici on utilise à la place la note Elo du club **avant** le premier match |

Deux règles de l'UEFA sont laissées de côté : la différence de buts et les buts des adversaires (elles ne décident presque jamais rien), et les points disciplinaires (les cartons ne sont pas simulés). Il n'y a pas de confrontation directe : dans ce format, chaque paire de clubs se rencontre au plus une fois, donc l'UEFA ne l'utilise pas.

**Pourquoi la note d'avant la compétition ?** La note à la fin de la phase de ligue contient déjà les résultats de cette phase. L'utiliser ferait compter deux fois les résultats d'un club : une fois dans les points, et encore dans le dernier critère.

### Comment le programme classe : comme un dictionnaire

Le programme donne à chaque club une liste de ses nombres dans cet ordre, par exemple (17, 8, 15, ...) pour 17 points, +8 de différence de buts, 15 buts, et trie les clubs selon ces listes, du plus grand au plus petit.

Python compare deux listes comme un dictionnaire range les mots : d'abord les premières lettres ; seulement si elles sont égales, les deuxièmes ; et ainsi de suite. « car » vient avant « cas » car « r » vient avant « s », et les deux premières lettres sont égales.

Un critère plus loin ne peut donc séparer que des clubs égaux sur tous les critères d'avant, exactement comme les règles de l'UEFA.

---

## 4. Un exemple complet à la main

Quatre clubs, deux journées :

| Journée | Matchs |
|---|---|
| 1 | A 2-0 B, C 1-1 D |
| 2 | B 0-3 C, D 1-1 A |

| Club | Gagnés | Nuls | Perdus | Marqués | Encaissés | Différence | Points |
|---|---|---|---|---|---|---|---|
| C | 1 | 1 | 0 | 4 | 1 | +3 | 4 |
| A | 1 | 1 | 0 | 3 | 1 | +2 | 4 |
| D | 0 | 2 | 0 | 2 | 2 | 0 | 2 |
| B | 0 | 0 | 2 | 0 | 5 | −5 | 0 |

A et C ont tous les deux 4 points. C a la meilleure différence de buts (+3 contre +2), donc **C est premier**. Le journal du programme l'explique en une ligne : `1. C ahead of 2. A: level on points, split by goal difference (3 v 2)`.

---

## 5. À essayer en Python

Les quatre mêmes clubs, classés par points, puis différence de buts, puis buts.

```python
matches = [("A", 2, 0, "B"), ("C", 1, 1, "D"),     # journée 1 : A 2-0 B, C 1-1 D
           ("B", 0, 3, "C"), ("D", 1, 1, "A")]     # journée 2 : B 0-3 C, D 1-1 A

table = {club: {"pts": 0, "gf": 0, "ga": 0} for club in "ABCD"}
for home, hg, ag, away in matches:
    for club, scored, conceded in ((home, hg, ag), (away, ag, hg)):
        row = table[club]
        row["gf"] += scored
        row["ga"] += conceded
        row["pts"] += 3 if scored > conceded else 1 if scored == conceded else 0

def sort_key(club):
    row = table[club]
    return (row["pts"], row["gf"] - row["ga"], row["gf"])   # points, puis différence de buts, puis buts

for rank, club in enumerate(sorted(table, key=sort_key, reverse=True), start=1):
    row = table[club]
    print(rank, club, row["pts"], "pts", f"GD {row['gf'] - row['ga']:+d}", "key =", sort_key(club))
```

Résultat :

```
1 C 4 pts GD +3 key = (4, 3, 4)
2 A 4 pts GD +2 key = (4, 2, 3)
3 D 2 pts GD +0 key = (2, 0, 2)
4 B 0 pts GD -5 key = (0, -5, 0)
```

C et A ont le même premier nombre (4), donc Python regarde le deuxième : 3 est plus grand que 2, donc C passe devant.

---

## 6. À quelle fréquence chaque critère décide

Mesuré sur 2 000 phases de ligue simulées. Prenons chaque paire de clubs voisins dans le classement final (1er et 2e, 2e et 3e, etc.) :

| | Ligue des champions | Ligue Conférence |
|---|---|---|
| voisins à égalité de points | 52.5 % des paires | 60.0 % |
| ... puis séparés par la différence de buts | 85.7 % de celles-ci | 81.5 % |
| par les buts marqués | 12.5 % | 15.6 % |
| par les buts à l'extérieur | 1.5 % | 2.4 % |
| par un critère plus loin | moins de 0.5 % | moins de 0.6 % |

La différence de buts fait presque tout le travail. Et aux deux lignes importantes (8e/9e et 24e/25e), les deux clubs sont à égalité de points plus d'une fois sur deux : qui passe directement et qui est éliminé est souvent décidé par un critère de départage, pas par les points.

| | 8e place, points en moyenne | 24e place, points en moyenne |
|---|---|---|
| Ligue des champions (8 matchs) | 16.1 | 8.8 |
| Ligue Conférence (6 matchs) | 12.3 | 6.4 |

---

## 7. Ce que le code utilise

### Modules Python

Aucun. Ce fichier n'utilise que Python lui-même (classes, listes, dictionnaires, `sorted`).

### Fonctions et classes de `model/league_phase.py`

| Nom | En une ligne |
|---|---|
| `play_league_phase` | joue chaque match de chaque journée, dans l'ordre |
| `build_table` | additionne les résultats de chaque club et classe les clubs |
| `Row` | la ligne d'un club dans le classement : joués, gagnés, nuls, perdus, buts, points, ... |
| `Row.record` | ajoute un match à la ligne d'un club |
| `Row.sort_key` | la liste de nombres utilisée pour classer (section 3) |
| `explain_ties` | écrit, pour chaque paire à égalité de points, quel critère les a séparés |
| `format_table` | écrit le classement en texte simple pour le journal |

L'appli dessine le classement en couleurs (top 8, 9 à 24, éliminés) dans `interface/canvas_views.py`.

Comment marche chaque ligne : [`code/league_phase_code.md`](code/league_phase_code.md).

---

## 8. Ce qui peut mal tourner

- **La différence de buts dit peu de choses sur la force** dans la simulation, car le tireur de scores ignore l'écart de notes ([`scorelines.md`](scorelines.md), section 5). Et la différence de buts décide environ 86 % des égalités.
- **Deux critères de l'UEFA sont sautés** (différence de buts et buts des adversaires, points disciplinaires). Ils ne comptent presque jamais.
- **La note par défaut d'un club inconnu vaut 1500 ici**, écrite directement dans ce fichier, alors qu'une autre partie du projet utilise 1450.

### Bugs connus

- **Le journal donne la mauvaise raison pour une égalité parfaite.** Pour deux clubs égaux sur tous les critères, le journal dit « alphabetical order » (ordre alphabétique), mais le vrai ordre est celui des chapeaux (le tri de Python garde l'ordre d'origine des éléments égaux). Corriger le texte en « ordre des chapeaux ».

---

## 9. Idées pour plus tard

- **Montrer la raison à l'écran** : une petite marque à côté des points dans le classement de l'appli, qui dit quel critère a séparé deux clubs (le programme le sait déjà pour le journal).
- **De meilleures différences de buts** viendraient d'un meilleur tireur de scores, pas de ce fichier.

---

## 10. Mots à connaître

| Mot | Sens |
|---|---|
| phase de ligue | le premier tour : 36 clubs dans un seul classement, 8 matchs chacun (6 en Ligue Conférence) |
| critère de départage | une règle utilisée, dans l'ordre, pour séparer des clubs à égalité de points |
| différence de buts | buts marqués moins buts encaissés |
| coefficient de club | le classement UEFA d'un club selon ses résultats européens sur cinq saisons ; remplacé ici par la note avant la compétition |
| ligne de coupure | la frontière entre deux destins dans le classement : 8e/9e et 24e/25e |

---
