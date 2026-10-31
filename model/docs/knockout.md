# The knockout phase: play-offs, bracket and final

> After the league phase, this part plays everything until a champion is crowned: the play-offs, the round of 16, the quarter-finals, the semi-finals and the final. It works the same way for all three competitions.

*Version française : [plus bas](#la-phase-à-élimination-directe--barrages-tableau-et-finale).*

## In short

- **What goes in:** the final league table ([`league_phase.md`](league_phase.md)).
- **What comes out:** every knockout tie, with its matches, any extra time or penalty shoot-out, and the champion.
- **The choice the user makes:** how a two-legged tie is settled: "legs" (the default), "aggregate" (the real UEFA rule) or "oneshot". Section 3 explains the three.
- **Code:** `model/knockout.py`. Line-by-line walkthrough: [`code/knockout_code.md`](code/knockout_code.md).

---

## 1. Who goes where

This copies the real format used by UEFA since 2024/25:

| League position | What happens |
|---|---|
| 1st to 8th | straight to the round of 16 |
| 9th to 24th | a two-legged **play-off** to reach the round of 16 |
| 25th to 36th | out |

A **two-legged tie** is two matches between the same clubs, one at each ground. In this project, the club called **A** always plays the **second** match (the second leg) at home.

---

## 2. The bracket

```
 PLAY-OFFS (8 ties)
   9th/10th  v 23rd/24th
   11th/12th v 21st/22nd
   13th/14th v 19th/20th
   15th/16th v 17th/18th
        |
 ROUND OF 16
   1st/2nd meet the winners of 15th/16th v 17th/18th
   3rd/4th meet the winners of 13th/14th v 19th/20th
   5th/6th meet the winners of 11th/12th v 21st/22nd
   7th/8th meet the winners of 9th/10th  v 23rd/24th
        |
 QUARTER-FINALS                       SEMI-FINALS              FINAL
   QF1 = tie of 1st v tie of 8th      SF1 = QF1 v QF2          SF1 v SF2,
   QF2 = tie of 3rd v tie of 5th      SF2 = QF3 v QF4          one match,
   QF3 = tie of 2nd v tie of 7th                               neutral ground
   QF4 = tie of 4th v tie of 6th
```

How to read it: "9th/10th v 23rd/24th" means the clubs that finished 9th and 10th meet the clubs that finished 23rd and 24th. A coin decides who plays whom inside that group: either 9th v 24th and 10th v 23rd, or 9th v 23rd and 10th v 24th.

"Tie of 1st" means "the round-of-16 tie that contains the club ranked 1st".

The best clubs get the easiest paths: 1st and 2nd meet winners of the 15th/16th v 17th/18th play-offs. And 1st and 2nd are in opposite halves of the bracket, so they can only meet in the final.

**Who plays the second leg at home?**

| Round | Second-leg host |
|---|---|
| Play-off | the better-ranked club (9th to 16th) |
| Round of 16 | the top-8 club |
| Quarter-final, semi-final | decided by a coin |
| Final | nobody: one match at a neutral ground |

---

## 3. Three ways to settle a two-legged tie

### "legs" (the default): a point per match

Each leg is treated as its own match: **1 point for a win, 0.5 for a draw**. Over the two legs, the club with more points goes through.

- Win and draw: 1.5 points against 0.5, through.
- One win each, or two draws: **level**, 1 point each. Then the winner is picked at random, but the stronger club has more chance: its chance is its Elo expected score ([`elo.md`](elo.md), section 3). A realistic penalty shoot-out is then created for that winner ([`penalties.md`](penalties.md)).

Goals do not count: winning 5-0 then losing 0-1 is "level", one win each. The idea behind this method is that every leg is a match with a real result, and a level tie keeps the stronger club's edge.

### "aggregate" (the real UEFA rule): goals over both legs

Add each club's goals over the two matches. More goals goes through. If level: **extra time** at the end of the second leg ([`extra_time.md`](extra_time.md)), then a **penalty shoot-out** if still level. The old "away goals" rule is not used: UEFA abolished it in 2021.

### "oneshot": one decision for the whole tie

No legs are played. The program works out each club's chance of winning one match, averaged over both grounds, and drops the draws:

$$\text{chance that A goes through} = \frac{\text{A's chance of winning one match}}{\text{A's chance} + \text{B's chance}}$$

Arsenal and Atalanta: Arsenal win one match 54.8 % of the time, Atalanta 23.9 % (the rest are draws). So Arsenal go through with 54.8 ÷ (54.8 + 23.9) = **69.6 %**. Dropping the draws is like saying "replay until someone wins". One random number decides, and the bracket shows the percentage instead of scores.

### The same tie, two different winners

Real example from a simulated season. Juventus host the second leg against Manchester City:

```
Leg 1: Manchester City 2-1 Juventus
Leg 2: Juventus 3-1 Manchester City
```

- **"legs"**: one win each, so level. City won the Elo pick and the shoot-out (6-5): **City** go through.
- **"aggregate"**: Juventus scored 1 + 3 = 4, City 2 + 1 = 3: **Juventus** go through, with no extra time.

---

## 4. The three methods compared

40 000 simulated quarter-finals for each row. A plays the second leg at home.

| Ratings (A v B) | "legs" | "aggregate" | "oneshot" | a single match at a neutral ground |
|---|---|---|---|---|
| 1600 v 1600 (equal) | A goes through 48.9 % (shoot-out 31.0 %) | 49.0 % (extra time 12.9 %, shoot-out 6.1 %) | 50.3 % | 50.3 % |
| 1700 v 1600 | 78.7 % (shoot-out 24.5 %) | 75.7 % (extra time 10.2 %, shoot-out 4.8 %) | 77.7 % | 72.4 % |
| 1800 v 1600 | 94.0 % (shoot-out 12.1 %) | 91.1 % (extra time 5.0 %, shoot-out 2.3 %) | 92.4 % | 86.7 % |

What the table shows:

- **"legs" helps the stronger club the most.** About a third of its ties are decided by the Elo pick, which keeps the favourite's edge, while "aggregate" sends level ties to extra time and to penalties, which are closer to 50/50.
- **Two matches help the stronger club more than one.** At +100 points: 75.7 % to 78.7 % over two legs, 72.4 % in one match. Two samples of the same strength gap let less luck through.
- **"oneshot" sits in between**, and is the fastest because no match is played.

### A small surprise: hosting the second leg is slightly worse here

Between two equal clubs, A should go through 50 % of the time. It goes through 48.9 % ("legs") and 49.0 % ("aggregate"). The gap is too big to be luck. The reason: the Elo update has no home advantage, so the club that hosts the first leg gains on average about 1.8 rating points from it, and is a little stronger in the second leg ([`match_engine.md`](match_engine.md), section 8). Football folklore says the opposite. The effect is one percentage point.

---

## 5. Try it in Python

The "legs" and "aggregate" rules on the Juventus v Manchester City tie, and the "oneshot" formula on Arsenal v Atalanta.

```python
def result(home_goals, away_goals):
    """1 for a home win, 0.5 for a draw, 0 for a home defeat."""
    return 1.0 if home_goals > away_goals else 0.5 if home_goals == away_goals else 0.0

def legs_method(a, b, leg1, leg2):
    """leg1 is played at b's ground, leg2 at a's ground. Scores are (home, away)."""
    points_a = (1 - result(*leg1)) + result(*leg2)
    points_b = result(*leg1) + (1 - result(*leg2))
    if points_a == points_b:
        return f"level on leg points ({points_a:g}-{points_b:g}): Elo pick, then a shoot-out"
    return a if points_a > points_b else b

def aggregate_method(a, b, leg1, leg2):
    goals_a = leg1[1] + leg2[0]          # a is away in leg 1, at home in leg 2
    goals_b = leg1[0] + leg2[1]
    if goals_a == goals_b:
        return f"level on aggregate ({goals_a}-{goals_b}): extra time, then penalties"
    return f"{a if goals_a > goals_b else b} ({goals_a}-{goals_b} on aggregate)"

# Juventus host the second leg. Leg 1: Manchester City 2-1 Juventus. Leg 2: Juventus 3-1 Manchester City.
leg1, leg2 = (2, 1), (3, 1)
print("legs:     ", legs_method("Juventus", "Manchester City", leg1, leg2))
print("aggregate:", aggregate_method("Juventus", "Manchester City", leg1, leg2))

# oneshot: Arsenal's and Atalanta's chances of winning one match, averaged over both grounds
p_a, p_b = 0.548, 0.239
print("oneshot:   Arsenal go through with chance", round(p_a / (p_a + p_b), 3))
```

Output:

```
legs:      level on leg points (1-1): Elo pick, then a shoot-out
aggregate: Juventus (4-3 on aggregate)
oneshot:   Arsenal go through with chance 0.696
```

---

## 6. A real bracket

Champions League, all seeds set to 1, method "legs". The top of the table: 1 Barcelona, 2 Club Brugge, 3 Sporting CP, 4 Liverpool, 5 Red Star Belgrade, 6 Inter, 7 PSV, 8 Monaco, 9 Arsenal, 10 Real Madrid, ... 23 AC Milan, 24 Feyenoord. (One season is one story: Club Brugge second is luck, not a forecast. Forecasts come from repeating the season many times: [`monte_carlo.md`](monte_carlo.md).)

Play-off group 9th/10th v 23rd/24th; the coin gave Arsenal v Feyenoord and Real Madrid v AC Milan:

```
Feyenoord 3-0 Arsenal  |  Arsenal 1-2 Feyenoord  (legs 0-2)  ->  Feyenoord
AC Milan 1-2 Real Madrid  |  Real Madrid 3-0 AC Milan  (legs 2-0)  ->  Real Madrid
```

Those winners then met 7th and 8th in the round of 16. The quarter-finals: Barcelona v Feyenoord, Sporting v Red Star, PSG v PSV, Liverpool v Bayer Leverkusen. Final: Liverpool 1-3 Barcelona.

---

## 7. What the code uses

### Python modules

None from outside the project. It uses two parts of the project:

| From | What |
|---|---|
| `model/penalties.py` | the penalty shoot-outs ([`penalties.md`](penalties.md)) |
| `model/elo_score_updating.py` | `expected_score` (the Elo pick of "legs") and `update_rating` (the single rating step of "oneshot") |

Every match goes through the match engine ([`match_engine.md`](match_engine.md)), and extra time through the score picker ([`scorelines.md`](scorelines.md)).

### Functions and classes in `model/knockout.py`

| Name | In one line |
|---|---|
| `play_knockout` | the entry point: from the league table to the champion |
| `draw_playoffs` | makes the 8 play-off ties (section 2) |
| `draw_r16` | makes the 8 round-of-16 ties from the play-off winners |
| `play_tie` | plays one two-legged tie with the chosen method |
| `play_final` | plays the final: one match at a neutral ground, then extra time and penalties if needed |
| `Tie` | a record of one tie: the clubs, the matches, the scores, extra time, shoot-out, winner |

Smaller helpers: `_play_legs`, `_play_aggregate`, `_play_oneshot` (one per method), `_two_legs` (plays both legs), `_settle_level` (extra time, then penalties), `_next_round` (pairs the winners for the next round), `_pair_up` (the coin inside a group), `_rank_of` (finds a club's league position), `_log_shootout` (writes the penalty sheet in the log).

The app draws the bracket in `interface/canvas_views.py` and shows the details of a tie in `interface/sim_view.py`.

How each line works: [`code/knockout_code.md`](code/knockout_code.md).

---

## 8. What can go wrong

- **"legs" ignores goals**: 5-0 then 0-1 is a level tie.
- **Hosting the second leg is slightly worse** in the simulation (section 4).
- **The home order of quarter-finals and semi-finals is a coin**, standing in for the real draw.
- **"oneshot" moves the ratings once per tie**, the other methods twice (two legs), so ratings change at a different speed depending on the method.
- **No other draw rules after the league phase** are modelled.

### Known bugs

None in the logic. One rough edge: a tie built by hand, without league positions, shows `None` as the position in the log instead of failing.

---

## 9. Ideas for later

- **A tiebreaker for "legs"**: on level leg points, use the goal difference over the two legs before the Elo pick. That would fix the 5-0 / 0-1 case.
- **Fix the second-leg effect at its source** by adding home advantage to Elo ([`match_engine.md`](match_engine.md), section 9).
- **Compare the methods on screen**: show the chance of winning the competition under all three methods side by side.

---

## 10. Words to know

| Word | Meaning |
|---|---|
| two-legged tie | two matches between the same clubs, one at each ground |
| leg | one of those two matches |
| aggregate | total goals over both legs |
| away-goals rule | an old rule (abolished in 2021): more goals scored away goes through |
| play-off | the extra round for the clubs ranked 9th to 24th |
| bracket | the fixed tree of who meets whom from the quarter-finals to the final |
| seeded | placed so as to avoid the strongest opponents |


---
---

# La phase à élimination directe : barrages, tableau et finale

> Après la phase de ligue, cette partie joue tout jusqu'au sacre d'un champion : les barrages, les huitièmes de finale, les quarts, les demies et la finale. Elle marche de la même façon pour les trois compétitions.

## En bref

- **Ce qui entre :** le classement final de la phase de ligue ([`league_phase.md`](league_phase.md)).
- **Ce qui sort :** chaque confrontation à élimination directe, avec ses matchs, une éventuelle prolongation ou séance de tirs au but, et le champion.
- **Le choix de l'utilisateur :** comment se décide une confrontation aller-retour : « legs » (par défaut), « aggregate » (la vraie règle de l'UEFA) ou « oneshot ». La section 3 explique les trois.
- **Code :** `model/knockout.py`. Explication ligne par ligne : [`code/knockout_code.md`](code/knockout_code.md).

---

## 1. Qui va où

Cela copie le vrai format utilisé par l'UEFA depuis 2024/25 :

| Place dans la phase de ligue | Ce qui se passe |
|---|---|
| 1er à 8e | directement en huitièmes de finale |
| 9e à 24e | un **barrage** aller-retour pour atteindre les huitièmes |
| 25e à 36e | éliminés |

Une **confrontation aller-retour** est deux matchs entre les mêmes clubs, un dans chaque stade. Dans ce projet, le club appelé **A** joue toujours le **deuxième** match (le match retour) à domicile.

---

## 2. Le tableau

```
 BARRAGES (8 confrontations)
   9e/10e  contre 23e/24e
   11e/12e contre 21e/22e
   13e/14e contre 19e/20e
   15e/16e contre 17e/18e
        |
 HUITIÈMES DE FINALE
   1er/2e rencontrent les vainqueurs de 15e/16e contre 17e/18e
   3e/4e  rencontrent les vainqueurs de 13e/14e contre 19e/20e
   5e/6e  rencontrent les vainqueurs de 11e/12e contre 21e/22e
   7e/8e  rencontrent les vainqueurs de 9e/10e  contre 23e/24e
        |
 QUARTS DE FINALE                       DEMI-FINALES             FINALE
   QF1 = confr. du 1er contre celle du 8e   SF1 = QF1 contre QF2   SF1 contre SF2,
   QF2 = confr. du 3e contre celle du 5e    SF2 = QF3 contre QF4   un seul match,
   QF3 = confr. du 2e contre celle du 7e                           terrain neutre
   QF4 = confr. du 4e contre celle du 6e
```

Comment le lire : « 9e/10e contre 23e/24e » veut dire que les clubs finis 9e et 10e rencontrent les clubs finis 23e et 24e. Une pièce décide qui joue qui dans ce groupe : soit 9e contre 24e et 10e contre 23e, soit 9e contre 23e et 10e contre 24e.

« Confrontation du 1er » veut dire « la confrontation des huitièmes qui contient le club classé 1er ».

Les meilleurs clubs ont les chemins les plus faciles : le 1er et le 2e rencontrent les vainqueurs des barrages 15e/16e contre 17e/18e. Et le 1er et le 2e sont dans des moitiés opposées du tableau, donc ils ne peuvent se rencontrer qu'en finale.

**Qui reçoit au match retour ?**

| Tour | Club qui reçoit au retour |
|---|---|
| Barrage | le mieux classé (9e à 16e) |
| Huitièmes | le club du top 8 |
| Quarts, demies | décidé à pile ou face |
| Finale | personne : un seul match sur terrain neutre |

---

## 3. Trois façons de décider une confrontation aller-retour

### « legs » (par défaut) : un point par match

Chaque match est traité comme un match à part : **1 point pour une victoire, 0.5 pour un nul**. Sur les deux matchs, le club qui a le plus de points se qualifie.

- Une victoire et un nul : 1.5 point contre 0.5, qualifié.
- Une victoire chacun, ou deux nuls : **égalité**, 1 point chacun. Le vainqueur est alors tiré au hasard, mais le club le plus fort a plus de chances : sa chance est son score attendu Elo ([`elo.md`](elo.md), section 3). Une séance de tirs au but réaliste est ensuite créée pour ce vainqueur ([`penalties.md`](penalties.md)).

Les buts ne comptent pas : gagner 5-0 puis perdre 0-1, c'est « égalité », une victoire chacun. L'idée de cette méthode est que chaque match a un vrai résultat, et qu'une égalité garde l'avantage du club le plus fort.

### « aggregate » (la vraie règle de l'UEFA) : les buts sur les deux matchs

Additionner les buts de chaque club sur les deux matchs. Le plus de buts se qualifie. En cas d'égalité : **prolongation** à la fin du match retour ([`extra_time.md`](extra_time.md)), puis **tirs au but** si l'égalité dure. L'ancienne règle des « buts à l'extérieur » n'est pas utilisée : l'UEFA l'a supprimée en 2021.

### « oneshot » : une seule décision pour toute la confrontation

Aucun match n'est joué. Le programme calcule la chance de chaque club de gagner un match, en moyenne sur les deux stades, et enlève les nuls :

$$\text{chance que A se qualifie} = \frac{\text{chance de A de gagner un match}}{\text{chance de A} + \text{chance de B}}$$

Arsenal et l'Atalanta : Arsenal gagnent un match 54.8 % du temps, l'Atalanta 23.9 % (le reste, ce sont des nuls). Arsenal se qualifient donc avec 54.8 ÷ (54.8 + 23.9) = **69.6 %**. Enlever les nuls revient à dire « on rejoue jusqu'à ce que quelqu'un gagne ». Un nombre au hasard décide, et le tableau montre le pourcentage au lieu des scores.

### La même confrontation, deux vainqueurs différents

Vrai exemple d'une saison simulée. La Juventus reçoit Manchester City au match retour :

```
Aller : Manchester City 2-1 Juventus
Retour : Juventus 3-1 Manchester City
```

- **« legs »** : une victoire chacun, donc égalité. City a gagné le tirage Elo et les tirs au but (6-5) : **City** se qualifie.
- **« aggregate »** : la Juventus a marqué 1 + 3 = 4, City 2 + 1 = 3 : la **Juventus** se qualifie, sans prolongation.

---

## 4. Les trois méthodes comparées

40 000 quarts de finale simulés par ligne. A reçoit au match retour.

| Notes (A contre B) | « legs » | « aggregate » | « oneshot » | un seul match sur terrain neutre |
|---|---|---|---|---|
| 1600 contre 1600 (égaux) | A se qualifie 48.9 % (tirs au but 31.0 %) | 49.0 % (prolongation 12.9 %, tirs au but 6.1 %) | 50.3 % | 50.3 % |
| 1700 contre 1600 | 78.7 % (tirs au but 24.5 %) | 75.7 % (prolongation 10.2 %, tirs au but 4.8 %) | 77.7 % | 72.4 % |
| 1800 contre 1600 | 94.0 % (tirs au but 12.1 %) | 91.1 % (prolongation 5.0 %, tirs au but 2.3 %) | 92.4 % | 86.7 % |

Ce que montre le tableau :

- **« legs » aide le plus le club le plus fort.** Environ un tiers de ses confrontations sont décidées par le tirage Elo, qui garde l'avantage du favori, alors que « aggregate » envoie les égalités en prolongation et aux tirs au but, plus proches de 50/50.
- **Deux matchs aident le club le plus fort davantage qu'un seul.** À +100 points : 75.7 % à 78.7 % sur deux matchs, 72.4 % sur un seul. Deux essais du même écart de force laissent passer moins de hasard.
- **« oneshot » est entre les deux**, et c'est la plus rapide car aucun match n'est joué.

### Une petite surprise : recevoir au retour est un peu désavantageux ici

Entre deux clubs égaux, A devrait se qualifier 50 % du temps. Il se qualifie 48.9 % (« legs ») et 49.0 % (« aggregate »). L'écart est trop grand pour être du hasard. La raison : la mise à jour Elo n'a pas d'avantage du terrain, donc le club qui reçoit au match aller y gagne en moyenne environ 1.8 point de note, et il est un peu plus fort au retour ([`match_engine.md`](match_engine.md), section 8). Les supporters disent souvent l'inverse. L'effet est d'un point de pourcentage.

---

## 5. À essayer en Python

Les règles « legs » et « aggregate » sur la confrontation Juventus-Manchester City, et la formule « oneshot » sur Arsenal-Atalanta.

```python
def result(home_goals, away_goals):
    """1 pour une victoire à domicile, 0.5 pour un nul, 0 pour une défaite à domicile."""
    return 1.0 if home_goals > away_goals else 0.5 if home_goals == away_goals else 0.0

def legs_method(a, b, leg1, leg2):
    """leg1 se joue chez b, leg2 chez a. Les scores sont (domicile, extérieur)."""
    points_a = (1 - result(*leg1)) + result(*leg2)
    points_b = result(*leg1) + (1 - result(*leg2))
    if points_a == points_b:
        return f"level on leg points ({points_a:g}-{points_b:g}): Elo pick, then a shoot-out"
    return a if points_a > points_b else b

def aggregate_method(a, b, leg1, leg2):
    goals_a = leg1[1] + leg2[0]          # a est à l'extérieur à l'aller, à domicile au retour
    goals_b = leg1[0] + leg2[1]
    if goals_a == goals_b:
        return f"level on aggregate ({goals_a}-{goals_b}): extra time, then penalties"
    return f"{a if goals_a > goals_b else b} ({goals_a}-{goals_b} on aggregate)"

# La Juventus reçoit au retour. Aller : Manchester City 2-1 Juventus. Retour : Juventus 3-1 Manchester City.
leg1, leg2 = (2, 1), (3, 1)
print("legs:     ", legs_method("Juventus", "Manchester City", leg1, leg2))
print("aggregate:", aggregate_method("Juventus", "Manchester City", leg1, leg2))

# oneshot : chances d'Arsenal et de l'Atalanta de gagner un match, en moyenne sur les deux stades
p_a, p_b = 0.548, 0.239
print("oneshot:   Arsenal go through with chance", round(p_a / (p_a + p_b), 3))
```

Résultat :

```
legs:      level on leg points (1-1): Elo pick, then a shoot-out
aggregate: Juventus (4-3 on aggregate)
oneshot:   Arsenal go through with chance 0.696
```

---

## 6. Un vrai tableau

Ligue des champions, toutes les graines à 1, méthode « legs ». Le haut du classement : 1 Barcelone, 2 Club Bruges, 3 Sporting CP, 4 Liverpool, 5 Étoile rouge de Belgrade, 6 Inter, 7 PSV, 8 Monaco, 9 Arsenal, 10 Real Madrid, ... 23 AC Milan, 24 Feyenoord. (Une saison, c'est une histoire : Club Bruges deuxième, c'est de la chance, pas une prévision. Les prévisions viennent de la répétition de la saison de nombreuses fois : [`monte_carlo.md`](monte_carlo.md).)

Groupe de barrage 9e/10e contre 23e/24e ; la pièce a donné Arsenal-Feyenoord et Real Madrid-AC Milan :

```
Feyenoord 3-0 Arsenal  |  Arsenal 1-2 Feyenoord  (legs 0-2)  ->  Feyenoord
AC Milan 1-2 Real Madrid  |  Real Madrid 3-0 AC Milan  (legs 2-0)  ->  Real Madrid
```

Ces vainqueurs ont ensuite rencontré le 7e et le 8e en huitièmes. Les quarts : Barcelone-Feyenoord, Sporting-Étoile rouge, PSG-PSV, Liverpool-Bayer Leverkusen. Finale : Liverpool 1-3 Barcelone.

---

## 7. Ce que le code utilise

### Modules Python

Aucun en dehors du projet. Il utilise deux parties du projet :

| Depuis | Quoi |
|---|---|
| `model/penalties.py` | les séances de tirs au but ([`penalties.md`](penalties.md)) |
| `model/elo_score_updating.py` | `expected_score` (le tirage Elo de « legs ») et `update_rating` (le pas de note unique de « oneshot ») |

Chaque match passe par le moteur de match ([`match_engine.md`](match_engine.md)), et la prolongation par le tireur de scores ([`scorelines.md`](scorelines.md)).

### Fonctions et classes de `model/knockout.py`

| Nom | En une ligne |
|---|---|
| `play_knockout` | le point d'entrée : du classement de la phase de ligue au champion |
| `draw_playoffs` | crée les 8 confrontations de barrage (section 2) |
| `draw_r16` | crée les 8 confrontations des huitièmes à partir des vainqueurs des barrages |
| `play_tie` | joue une confrontation aller-retour avec la méthode choisie |
| `play_final` | joue la finale : un match sur terrain neutre, puis prolongation et tirs au but si besoin |
| `Tie` | la fiche d'une confrontation : les clubs, les matchs, les scores, la prolongation, les tirs au but, le vainqueur |

Petites fonctions : `_play_legs`, `_play_aggregate`, `_play_oneshot` (une par méthode), `_two_legs` (joue les deux matchs), `_settle_level` (prolongation, puis tirs au but), `_next_round` (associe les vainqueurs pour le tour suivant), `_pair_up` (la pièce dans un groupe), `_rank_of` (trouve la place d'un club au classement), `_log_shootout` (écrit la feuille de tirs au but dans le journal).

L'appli dessine le tableau dans `interface/canvas_views.py` et montre le détail d'une confrontation dans `interface/sim_view.py`.

Comment marche chaque ligne : [`code/knockout_code.md`](code/knockout_code.md).

---

## 8. Ce qui peut mal tourner

- **« legs » ignore les buts** : 5-0 puis 0-1, c'est une égalité.
- **Recevoir au retour est un peu désavantageux** dans la simulation (section 4).
- **L'ordre domicile/extérieur des quarts et des demies est tiré à pile ou face**, à la place du vrai tirage.
- **« oneshot » fait bouger les notes une fois par confrontation**, les autres méthodes deux fois (deux matchs), donc les notes changent à une vitesse différente selon la méthode.
- **Aucune autre règle de tirage après la phase de ligue** n'est modélisée.

### Bugs connus

Aucun dans la logique. Un petit défaut : une confrontation créée à la main, sans places au classement, affiche `None` comme place dans le journal au lieu d'échouer.

---

## 9. Idées pour plus tard

- **Un critère de départage pour « legs »** : en cas d'égalité de points, utiliser la différence de buts sur les deux matchs avant le tirage Elo. Cela corrigerait le cas 5-0 / 0-1.
- **Corriger l'effet du match retour à sa source** en ajoutant l'avantage du terrain à Elo ([`match_engine.md`](match_engine.md), section 9).
- **Comparer les méthodes à l'écran** : montrer côte à côte la chance de gagner la compétition avec chacune des trois méthodes.

---

## 10. Mots à connaître

| Mot | Sens |
|---|---|
| confrontation aller-retour | deux matchs entre les mêmes clubs, un dans chaque stade |
| match aller, match retour | les deux matchs de la confrontation |
| score cumulé (aggregate) | le total des buts sur les deux matchs |
| règle des buts à l'extérieur | une ancienne règle (supprimée en 2021) : le plus de buts marqués à l'extérieur se qualifie |
| barrage | le tour en plus pour les clubs classés 9e à 24e |
| tableau | l'arbre fixe de qui rencontre qui des quarts à la finale |
| tête de série | placé de façon à éviter les adversaires les plus forts |

---

