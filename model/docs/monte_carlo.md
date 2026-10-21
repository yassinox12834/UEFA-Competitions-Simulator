# The simulation and the Monte Carlo

> This part runs a whole season from the draw to the final, and then repeats that season many times with new random numbers. By counting how often each club reaches each round, it turns many made-up seasons into chances: "PSG win the competition about 21 % of the time".

*Version française : [plus bas](#la-simulation-et-le-monte-carlo).*

## In short

- **What goes in:** a finished draw and its matchdays ([`draw.md`](draw.md), [`matchdays.md`](matchdays.md)), the two-leg method, a seed, and how many seasons to play (0, 200, 1 000 or 10 000).
- **What comes out:** one complete season to look at, and a table of chances: for every club, how often it reached the top 8, the top 24, the round of 16, the quarter-finals, the semi-finals, the final, and how often it won.
- **Code:** `model/simulation.py`, and `interface/sim_engine.py` for the link with the app's window. Line-by-line walkthrough: [`code/simulation_code.md`](code/simulation_code.md).

> **Note:** the Monte Carlo does not change the season shown on screen. That season is one story; the Monte Carlo only estimates the chances, to give an idea of what is likely.

---

## 1. One season

One season goes through every other part of this folder, in order:

```
 1. give every club its rating                       names.md, elo.md
 2. play the league phase, day by day                league_phase.md, match_engine.md
 3. rank the 36 clubs                                league_phase.md
 4. play-offs, round of 16, quarter-finals,
    semi-finals, final                               knockout.md, extra_time.md, penalties.md
 5. return everything (and the expert log if asked)
```

A Champions League season is 189 matches: 144 in the league phase, 16 + 16 + 8 + 4 knockout legs, and the final.

Everything random in a season (results, scores, coins, penalties) comes from **one** random generator started from the **seed**. Same seed, same season, to the last goal. That makes any strange result easy to replay and check.

---

## 2. Why repeat the season?

One season is a story, not a forecast. In one simulated season, Club Brugge might finish second: that is luck.

To get a forecast, play the same competition many times, each time with new random numbers, and **count**:

> If PSG win 41 of 200 seasons, their chance of winning is about 41 ÷ 200 = 20.5 %.

This method of "estimating a chance by repeating a random experiment many times and counting" is called a **Monte Carlo** simulation, after the casino in Monaco, because it relies on chance.

### The rounds that are counted

| Name | How a club gets there |
|---|---|
| top 8 | finish 1st to 8th in the league phase (straight to the round of 16) |
| top 24 | finish 1st to 24th (still in the competition after the league phase) |
| round of 16 | be one of the last 16 clubs |
| quarter-finals | be one of the last 8 |
| semi-finals | be one of the last 4 |
| final | be one of the last 2 |
| winner | win the final |

"Reaching" a round means getting **at least** that far: a club that loses in the semi-final has reached the top 24, the round of 16, the quarter-finals and the semi-finals, but not the final. So for every club, the chances can only go down from left to right: you cannot play more finals than semi-finals.

---

## 3. How much luck is left in a chance?

200 seasons do not give the exact answer. Run another 200 and PSG might win 37 or 45 times instead of 41. The question is: **how far from the truth is the number on screen, usually?**

The answer is the **standard error**:

$$\text{standard error} = \sqrt{\frac{p \times (1 - p)}{N}}$$

| Symbol | In plain words |
|---|---|
| $p$ | the chance shown on screen, for example 0.205 |
| $N$ | the number of seasons played, for example 200 |
| $\sqrt{\ }$ | the square root |

For PSG with 200 seasons: $\sqrt{0.205 \times 0.795 / 200} = 0.029$. A useful rule: the true chance is very probably (19 times out of 20) within **about two standard errors** of the screen value. So "PSG win 20.5 %" really means "somewhere between about 15 % and 26 %".

| Seasons played | Typical luck (two standard errors) for a chance near 50 % | near 5 % |
|---|---|---|
| 200 | ± 7 points | ± 3 points |
| 1 000 | ± 3 points | ± 1.4 points |
| 10 000 | ± 1 point | ± 0.4 points |

Notice: **10 times more seasons only makes the result about 3 times more precise** (because of the square root). Precision is expensive.

**Comparing two clubs.** At 200 seasons, PSG show 20.5 % and Barcelona 17.0 %. The gap (3.5 points) is smaller than the luck in it, so at 200 seasons we cannot say PSG are more likely to win. At 1 000 seasons the order starts to be believable.

**A zero is not "impossible".** If a club wins 0 of 1 000 seasons, its true chance is very probably below about 3 ÷ 1 000 = 0.3 %, not exactly 0. This shortcut is called the **rule of three**.

---

## 4. A real result

Champions League, all seeds set to 1, 1 000 seasons (under a second on a test computer):

| Club | Rating at the start | Average points | Top 8 | Top 24 | Round of 16 | Quarter-finals | Semi-finals | Final | Winner |
|---|---|---|---|---|---|---|---|---|---|
| Paris Saint-Germain | 1852.84 | 17.7 | 72.4 % | 99.0 % | 93.7 % | 73.2 % | 50.4 % | 34.6 % | 20.6 % |
| Barcelona | 1841.33 | 17.0 | 62.8 % | 98.7 % | 91.4 % | 66.0 % | 43.0 % | 27.2 % | 17.1 % |
| Bayern Munich | 1811.07 | 15.2 | 44.8 % | 94.9 % | 82.4 % | 52.9 % | 31.9 % | 17.2 % | 9.6 % |
| Inter Milan | 1818.07 | 16.8 | 61.8 % | 98.8 % | 89.2 % | 57.6 % | 34.7 % | 19.6 % | 9.1 % |
| Liverpool | 1802.84 | 15.6 | 49.0 % | 95.5 % | 83.6 % | 52.1 % | 28.2 % | 15.4 % | 7.3 % |
| Real Madrid | 1787.62 | 15.8 | 54.0 % | 96.0 % | 82.2 % | 48.4 % | 26.0 % | 14.1 % | 6.3 % |

Inter have a higher rating and more points than Bayern, but a slightly lower chance of winning (9.1 % against 9.6 %). The gap, 0.5 points, is far smaller than the luck in it (about ±1.8 points): this order is noise, not a finding.

---

## 5. What the number means, exactly

"PSG win 20.6 %" is a chance **with some things kept fixed**:

1. this draw and these matchdays (the same in every season);
2. the starting ratings (the same in every season);
3. the match model, the score picker, the shoot-out rules and the two-leg method.

Only the match results change between seasons. So it means "given this draw, and if the ratings are exactly right". The real uncertainty is bigger, because the ratings are only estimates: PSG's 1852.84 could really be 1820 or 1880.

---

## 6. Try it in Python

A tiny competition of 4 clubs (two semi-finals and a final, no draws), repeated many times. For such a small case, the exact answer can also be worked out by hand: PSG win **39.6 %**.

```python
import math
import random
from collections import Counter

RATINGS = {"PSG": 1850, "Inter": 1820, "Arsenal": 1790, "Celtic": 1700}

def win_chance(a, b):
    """Elo expected score, used here as the chance that a beats b (no draws)."""
    return 1 / (1 + 10 ** ((RATINGS[b] - RATINGS[a]) / 400))

def play(a, b, rng):
    return a if rng.random() < win_chance(a, b) else b

def one_season(rng):
    finalist_1 = play("PSG", "Celtic", rng)       # semi-final 1
    finalist_2 = play("Inter", "Arsenal", rng)    # semi-final 2
    return play(finalist_1, finalist_2, rng)      # final

rng = random.Random(1)
for n in (200, 1_000, 10_000):
    titles = Counter(one_season(rng) for _ in range(n))
    p = titles["PSG"] / n
    se = math.sqrt(p * (1 - p) / n)              # how much luck is in p
    print(f"{n:>6} seasons: PSG win {p:.3f}, give or take {1.96 * se:.3f}")
```

Output:

```
   200 seasons: PSG win 0.425, give or take 0.069
  1000 seasons: PSG win 0.393, give or take 0.030
 10000 seasons: PSG win 0.390, give or take 0.010
```

With 200 seasons the estimate is 42.5 %, a bit far from the true 39.6 %, but inside its "give or take". With more seasons it gets closer, and the "give or take" shrinks.

---

## 7. Speed: using several processor cores

A Champions League season takes about 0.7 ms on a test computer, so 1 000 seasons take under a second. From 2 000 seasons, the program splits the work across up to 8 **processes**, separate copies of Python each running on its own processor core, so 10 000 seasons finish about twice as fast on a 2-core computer (3.8 s instead of 7.4 s).

To make sure the result does not depend on how the work is split, every season's seed is drawn **before** any season is played: season number 37 always uses seed number 37, whichever process plays it. So 1 process and 8 processes give exactly the same counts.

The app runs the simulation in the background, so the window never freezes, and a **Cancel** button can stop a long Monte Carlo.

---

## 8. What the code uses

### Python modules

| Module | Comes with Python? | What it does here |
|---|---|---|
| `random` | yes | one random generator per season, started from its seed |
| `concurrent.futures` (`ProcessPoolExecutor`) | yes | runs the seasons on several processor cores |
| `os` | yes | `os.cpu_count()`: how many cores the computer has |
| `json` | yes | reads the ratings file |
| `time` | yes | measures how long a season takes |
| `datetime` | yes | the date in the saved log's name and header |
| `pathlib` | yes | file paths |
| `threading` (in `interface/sim_engine.py`) | yes | runs the simulation in the background while the window stays responsive |

It also uses every other part of the model: `names.py`, `match_engine.py`, `predictor.py`, `scorelines.py`, `league_phase.py`, `knockout.py`.

### Functions and classes in `model/simulation.py`

| Name | In one line |
|---|---|
| `simulate` | plays one complete season |
| `monte_carlo` | plays many seasons and counts how far each club got |
| `SimConfig` | the user's choices: method, expert mode, seed |
| `Resources` | the three files a simulation needs (ratings, match model, score table), read once and shared |
| `Resources.seeds_for` | gives each club of the draw its rating, and remembers the answer |
| `seed_ratings` | finds each club's rating through `names.py`; 1500 if not found |
| `SimulationResult` | the record of one season; `stage_reached` says how far each club got |
| `MonteCarloResult` | the counts of a Monte Carlo; `probability` and `rows` turn them into chances |
| `summary_lines`, `describe_tie` | write the season as plain text |
| `write_log` | saves the text and the expert log to `data/processed/sim_<competition>_<date>.txt` |
| `Cancelled` | the signal used to stop a Monte Carlo early |

In `interface/sim_engine.py`: `SimJob` runs `simulate` then `monte_carlo` in the background; `resources()` keeps one `Resources` for the whole app.

How to try it from the project folder (a Champions League season with seed 1, then 100 seasons):

```bash
python -m model.simulation UCL
```

How each line works: [`code/simulation_code.md`](code/simulation_code.md).

---

## 9. What can go wrong

- **One draw for all seasons.** The chances depend on this draw. To answer "before the draw, how likely is PSG to win?", each season would need its own draw, about 100 times slower.
- **The ratings are treated as exact.** All the spread comes from match luck, none from "we are not sure PSG is really 1852". So the chances are too confident: favourites look safer, and outsiders more hopeless, than they should.
- **No "give or take" on screen.** A 0.5-point gap at 200 seasons looks as meaningful as a 10-point gap.

### Known bugs

- **With several processes, custom ratings are ignored.** The background processes reload the ratings from the file instead of using the ratings passed in. Tested: with every rating set to 1500, 1 process and 2 processes gave very different counts. Fix: pass the ratings to the processes, or refuse several processes when custom ratings are given.
- **`SimConfig` uses Python's shared random generator even when a seed is given.** Harmless for the results (each season has its own generator), but it changes the state of `random` for any other code.
- **If the processes fail to start, the work starts again from zero** in a single process, and the progress bar jumps back.
- **`probability(club, ...)` fails for a club spelt the ratings-file way** ("Bayern München"): the counts use the pot spelling ("Bayern Munich").

---

## 10. Ideas for later

- **"Give or take" on screen**, next to each chance.
- **Uncertain ratings**: at the start of each season, move every rating a little at random (for example by up to about ±60 points). The chances would become more honest.
- **Stop when precise enough**: play seasons in blocks of 200 and stop when the "give or take" of the column you care about is small enough.
- **Chances before the draw**: an option to redo the draw in every season.

---

## 11. Words to know

| Word | Meaning |
|---|---|
| Monte Carlo | estimating a chance by repeating a random experiment many times and counting |
| season (run) | one complete simulated competition, from matchday 1 to the final |
| seed | the starting number of the random generator: same seed, same season |
| standard error | how far the number on screen usually is from the true chance |
| rule of three | 0 successes in $N$ tries means the true chance is very probably below about $3 / N$ |
| process | a separate copy of Python running on its own processor core |


---
---

# La simulation et le Monte Carlo

> Cette partie joue une saison entière, du tirage à la finale, puis la répète de nombreuses fois avec de nouveaux nombres au hasard. En comptant combien de fois chaque club atteint chaque tour, elle transforme beaucoup de saisons inventées en chances : « le PSG gagne la compétition environ 21 % du temps ».

## En bref

- **Ce qui entre :** un tirage fini et ses journées ([`draw.md`](draw.md), [`matchdays.md`](matchdays.md)), la méthode aller-retour, une graine, et combien de saisons jouer (0, 200, 1 000 ou 10 000).
- **Ce qui sort :** une saison complète à regarder, et un tableau de chances : pour chaque club, combien de fois il a atteint le top 8, le top 24, les huitièmes, les quarts, les demies, la finale, et combien de fois il a gagné.
- **Code :** `model/simulation.py`, et `interface/sim_engine.py` pour le lien avec la fenêtre de l'appli. Explication ligne par ligne : [`code/simulation_code.md`](code/simulation_code.md).

> **Note :** le Monte Carlo ne change pas la saison affichée à l'écran. Cette saison est une histoire ; le Monte Carlo ne fait qu'estimer les chances, pour donner une idée de ce qui est probable.

---

## 1. Une saison

Une saison passe par toutes les autres parties de ce dossier, dans l'ordre :

```
 1. donner sa note à chaque club                     names.md, elo.md
 2. jouer la phase de ligue, journée par journée     league_phase.md, match_engine.md
 3. classer les 36 clubs                             league_phase.md
 4. barrages, huitièmes, quarts, demies, finale      knockout.md, extra_time.md, penalties.md
 5. tout renvoyer (et le journal expert si demandé)
```

Une saison de Ligue des champions, c'est 189 matchs : 144 en phase de ligue, 16 + 16 + 8 + 4 matchs à élimination directe, et la finale.

Tout ce qui est au hasard dans une saison (résultats, scores, pièces, tirs au but) vient d'**un seul** générateur de hasard démarré à partir de la **graine**. Même graine, même saison, jusqu'au dernier but. Cela permet de rejouer et vérifier facilement n'importe quel résultat étrange.

---

## 2. Pourquoi répéter la saison ?

Une saison est une histoire, pas une prévision. Dans une saison simulée, Club Bruges peut finir deuxième : c'est de la chance.

Pour obtenir une prévision, on joue la même compétition de nombreuses fois, à chaque fois avec de nouveaux nombres au hasard, et on **compte** :

> Si le PSG gagne 41 saisons sur 200, sa chance de gagner est d'environ 41 ÷ 200 = 20.5 %.

Cette méthode, « estimer une chance en répétant une expérience au hasard de nombreuses fois et en comptant », s'appelle une simulation de **Monte Carlo**, d'après le casino de Monaco, car elle repose sur le hasard.

### Les tours comptés

| Nom | Comment un club y arrive |
|---|---|
| top 8 | finir 1er à 8e de la phase de ligue (directement en huitièmes) |
| top 24 | finir 1er à 24e (toujours en course après la phase de ligue) |
| huitièmes | faire partie des 16 derniers clubs |
| quarts | faire partie des 8 derniers |
| demies | faire partie des 4 derniers |
| finale | faire partie des 2 derniers |
| vainqueur | gagner la finale |

« Atteindre » un tour veut dire aller **au moins** jusque-là : un club éliminé en demi-finale a atteint le top 24, les huitièmes, les quarts et les demies, mais pas la finale. Pour chaque club, les chances ne peuvent donc que baisser de gauche à droite : on ne peut pas jouer plus de finales que de demi-finales.

---

## 3. Combien de hasard reste-t-il dans une chance ?

200 saisons ne donnent pas la réponse exacte. Relance 200 saisons et le PSG pourrait gagner 37 ou 45 fois au lieu de 41. La question est : **à quelle distance de la vérité se trouve habituellement le nombre affiché ?**

La réponse est l'**erreur type** :

$$\text{erreur type} = \sqrt{\frac{p \times (1 - p)}{N}}$$

| Symbole | Avec des mots simples |
|---|---|
| $p$ | la chance affichée à l'écran, par exemple 0.205 |
| $N$ | le nombre de saisons jouées, par exemple 200 |
| $\sqrt{\ }$ | la racine carrée |

Pour le PSG avec 200 saisons : $\sqrt{0.205 \times 0.795 / 200} = 0.029$. Une règle utile : la vraie chance est très probablement (19 fois sur 20) à **environ deux erreurs types** du nombre affiché. « Le PSG gagne 20.5 % » veut donc vraiment dire « quelque part entre environ 15 % et 26 % ».

| Saisons jouées | Hasard habituel (deux erreurs types) pour une chance proche de 50 % | proche de 5 % |
|---|---|---|
| 200 | ± 7 points | ± 3 points |
| 1 000 | ± 3 points | ± 1.4 point |
| 10 000 | ± 1 point | ± 0.4 point |

À remarquer : **10 fois plus de saisons ne rend le résultat qu'environ 3 fois plus précis** (à cause de la racine carrée). La précision coûte cher.

**Comparer deux clubs.** À 200 saisons, le PSG affiche 20.5 % et Barcelone 17.0 %. L'écart (3.5 points) est plus petit que le hasard qu'il contient, donc à 200 saisons on ne peut pas dire que le PSG a plus de chances de gagner. À 1 000 saisons, l'ordre commence à être crédible.

**Un zéro ne veut pas dire « impossible ».** Si un club gagne 0 saison sur 1 000, sa vraie chance est très probablement sous environ 3 ÷ 1 000 = 0.3 %, pas exactement 0. Ce raccourci s'appelle la **règle de trois**.

---

## 4. Un vrai résultat

Ligue des champions, toutes les graines à 1, 1 000 saisons (moins d'une seconde sur un ordinateur de test) :

| Club | Note au départ | Points en moyenne | Top 8 | Top 24 | Huitièmes | Quarts | Demies | Finale | Vainqueur |
|---|---|---|---|---|---|---|---|---|---|
| Paris Saint-Germain | 1852.84 | 17.7 | 72.4 % | 99.0 % | 93.7 % | 73.2 % | 50.4 % | 34.6 % | 20.6 % |
| Barcelone | 1841.33 | 17.0 | 62.8 % | 98.7 % | 91.4 % | 66.0 % | 43.0 % | 27.2 % | 17.1 % |
| Bayern Munich | 1811.07 | 15.2 | 44.8 % | 94.9 % | 82.4 % | 52.9 % | 31.9 % | 17.2 % | 9.6 % |
| Inter Milan | 1818.07 | 16.8 | 61.8 % | 98.8 % | 89.2 % | 57.6 % | 34.7 % | 19.6 % | 9.1 % |
| Liverpool | 1802.84 | 15.6 | 49.0 % | 95.5 % | 83.6 % | 52.1 % | 28.2 % | 15.4 % | 7.3 % |
| Real Madrid | 1787.62 | 15.8 | 54.0 % | 96.0 % | 82.2 % | 48.4 % | 26.0 % | 14.1 % | 6.3 % |

L'Inter a une meilleure note et plus de points que le Bayern, mais une chance de gagner un peu plus faible (9.1 % contre 9.6 %). L'écart, 0.5 point, est bien plus petit que le hasard qu'il contient (environ ±1.8 point) : cet ordre est du bruit, pas une découverte.

---

## 5. Ce que le nombre veut dire exactement

« Le PSG gagne 20.6 % » est une chance **avec certaines choses gardées fixes** :

1. ce tirage et ces journées (les mêmes à chaque saison) ;
2. les notes de départ (les mêmes à chaque saison) ;
3. le modèle de match, le tireur de scores, les règles des tirs au but et la méthode aller-retour.

Seuls les résultats des matchs changent d'une saison à l'autre. Cela veut donc dire « avec ce tirage, et si les notes sont parfaitement justes ». La vraie incertitude est plus grande, car les notes ne sont que des estimations : le 1852.84 du PSG pourrait en réalité valoir 1820 ou 1880.

---

## 6. À essayer en Python

Une toute petite compétition de 4 clubs (deux demi-finales et une finale, pas de nul), répétée de nombreuses fois. Dans un cas aussi petit, la réponse exacte peut aussi se calculer à la main : le PSG gagne **39.6 %**.

```python
import math
import random
from collections import Counter

RATINGS = {"PSG": 1850, "Inter": 1820, "Arsenal": 1790, "Celtic": 1700}

def win_chance(a, b):
    """Score attendu Elo, utilisé ici comme la chance que a batte b (pas de nul)."""
    return 1 / (1 + 10 ** ((RATINGS[b] - RATINGS[a]) / 400))

def play(a, b, rng):
    return a if rng.random() < win_chance(a, b) else b

def one_season(rng):
    finalist_1 = play("PSG", "Celtic", rng)       # demi-finale 1
    finalist_2 = play("Inter", "Arsenal", rng)    # demi-finale 2
    return play(finalist_1, finalist_2, rng)      # finale

rng = random.Random(1)
for n in (200, 1_000, 10_000):
    titles = Counter(one_season(rng) for _ in range(n))
    p = titles["PSG"] / n
    se = math.sqrt(p * (1 - p) / n)              # combien de hasard dans p
    print(f"{n:>6} seasons: PSG win {p:.3f}, give or take {1.96 * se:.3f}")
```

Résultat :

```
   200 seasons: PSG win 0.425, give or take 0.069
  1000 seasons: PSG win 0.393, give or take 0.030
 10000 seasons: PSG win 0.390, give or take 0.010
```

Avec 200 saisons, l'estimation vaut 42.5 %, un peu loin des 39.6 % exacts, mais à l'intérieur de sa marge (« give or take »). Avec plus de saisons, elle se rapproche, et la marge rétrécit.

---

## 7. La vitesse : utiliser plusieurs cœurs du processeur

Une saison de Ligue des champions prend environ 0.7 ms sur un ordinateur de test, donc 1 000 saisons prennent moins d'une seconde. À partir de 2 000 saisons, le programme répartit le travail sur jusqu'à 8 **processus**, des copies séparées de Python qui tournent chacune sur son propre cœur, donc 10 000 saisons finissent environ deux fois plus vite sur un ordinateur à 2 cœurs (3.8 s au lieu de 7.4 s).

Pour que le résultat ne dépende pas de la façon dont le travail est réparti, la graine de chaque saison est tirée **avant** de jouer la moindre saison : la saison numéro 37 utilise toujours la graine numéro 37, quel que soit le processus qui la joue. Ainsi 1 processus et 8 processus donnent exactement les mêmes comptes.

L'appli lance la simulation en arrière-plan, pour que la fenêtre ne se fige jamais, et un bouton **Annuler** peut arrêter un long Monte Carlo.

---

## 8. Ce que le code utilise

### Modules Python

| Module | Fourni avec Python ? | Ce qu'il fait ici |
|---|---|---|
| `random` | oui | un générateur de hasard par saison, démarré à partir de sa graine |
| `concurrent.futures` (`ProcessPoolExecutor`) | oui | fait tourner les saisons sur plusieurs cœurs |
| `os` | oui | `os.cpu_count()` : combien de cœurs a l'ordinateur |
| `json` | oui | lit le fichier des notes |
| `time` | oui | mesure la durée d'une saison |
| `datetime` | oui | la date dans le nom et l'en-tête du journal enregistré |
| `pathlib` | oui | chemins de fichiers |
| `threading` (dans `interface/sim_engine.py`) | oui | fait tourner la simulation en arrière-plan pendant que la fenêtre reste réactive |

Il utilise aussi toutes les autres parties du modèle : `names.py`, `match_engine.py`, `predictor.py`, `scorelines.py`, `league_phase.py`, `knockout.py`.

### Fonctions et classes de `model/simulation.py`

| Nom | En une ligne |
|---|---|
| `simulate` | joue une saison complète |
| `monte_carlo` | joue de nombreuses saisons et compte jusqu'où chaque club est allé |
| `SimConfig` | les choix de l'utilisateur : méthode, mode expert, graine |
| `Resources` | les trois fichiers dont une simulation a besoin (notes, modèle de match, table des scores), lus une fois et partagés |
| `Resources.seeds_for` | donne sa note à chaque club du tirage, et garde la réponse en mémoire |
| `seed_ratings` | trouve la note de chaque club grâce à `names.py` ; 1500 s'il est introuvable |
| `SimulationResult` | la fiche d'une saison ; `stage_reached` dit jusqu'où chaque club est allé |
| `MonteCarloResult` | les comptes d'un Monte Carlo ; `probability` et `rows` les transforment en chances |
| `summary_lines`, `describe_tie` | écrivent la saison en texte simple |
| `write_log` | enregistre le texte et le journal expert dans `data/processed/sim_<compétition>_<date>.txt` |
| `Cancelled` | le signal utilisé pour arrêter un Monte Carlo avant la fin |

Dans `interface/sim_engine.py` : `SimJob` lance `simulate` puis `monte_carlo` en arrière-plan ; `resources()` garde un seul `Resources` pour toute l'appli.

Pour l'essayer depuis le dossier du projet (une saison de Ligue des champions avec la graine 1, puis 100 saisons) :

```bash
python -m model.simulation UCL
```

Comment marche chaque ligne : [`code/simulation_code.md`](code/simulation_code.md).

---

## 9. Ce qui peut mal tourner

- **Un seul tirage pour toutes les saisons.** Les chances dépendent de ce tirage. Pour répondre à « avant le tirage, quelle chance a le PSG de gagner ? », chaque saison aurait besoin de son propre tirage, environ 100 fois plus lent.
- **Les notes sont traitées comme exactes.** Tout l'écart vient du hasard des matchs, rien de « on n'est pas sûr que le PSG vaille vraiment 1852 ». Les chances sont donc trop sûres d'elles : les favoris semblent plus en sécurité, et les outsiders plus désespérés, qu'ils ne devraient.
- **Pas de marge à l'écran.** Un écart de 0.5 point à 200 saisons a l'air aussi important qu'un écart de 10 points.

### Bugs connus

- **Avec plusieurs processus, les notes personnalisées sont ignorées.** Les processus en arrière-plan relisent les notes depuis le fichier au lieu d'utiliser celles qu'on leur donne. Testé : avec toutes les notes à 1500, 1 processus et 2 processus ont donné des comptes très différents. Correction : donner les notes aux processus, ou refuser plusieurs processus quand des notes personnalisées sont fournies.
- **`SimConfig` utilise le générateur de hasard partagé de Python même quand une graine est donnée.** Sans effet sur les résultats (chaque saison a son propre générateur), mais cela change l'état de `random` pour tout autre code.
- **Si les processus n'arrivent pas à démarrer, le travail recommence à zéro** dans un seul processus, et la barre de progression revient en arrière.
- **`probability(club, ...)` échoue pour un club écrit comme dans le fichier des notes** (« Bayern München ») : les comptes utilisent l'orthographe des chapeaux (« Bayern Munich »).

---

## 10. Idées pour plus tard

- **Une marge à l'écran**, à côté de chaque chance.
- **Des notes incertaines** : au début de chaque saison, faire bouger un peu chaque note au hasard (par exemple d'environ ±60 points au plus). Les chances deviendraient plus honnêtes.
- **S'arrêter quand c'est assez précis** : jouer des blocs de 200 saisons et s'arrêter quand la marge de la colonne qui t'intéresse est assez petite.
- **Les chances avant le tirage** : une option pour refaire le tirage à chaque saison.

---

## 11. Mots à connaître

| Mot | Sens |
|---|---|
| Monte Carlo | estimer une chance en répétant une expérience au hasard de nombreuses fois et en comptant |
| saison (run) | une compétition simulée complète, de la journée 1 à la finale |
| graine (seed) | le nombre de départ du générateur de hasard : même graine, même saison |
| erreur type | la distance habituelle entre le nombre affiché et la vraie chance |
| règle de trois | 0 succès en $N$ essais veut dire que la vraie chance est très probablement sous environ $3 / N$ |
| processus | une copie séparée de Python qui tourne sur son propre cœur |

---

