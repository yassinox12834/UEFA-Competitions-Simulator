# The score picker: from a result to a score

> The match model only says "home win", "draw" or "away win". But the league table needs goals, because goal difference decides between clubs level on points. This part picks a score that fits the result, using how often each score happened in 4 642 real matches.

*Version française : [plus bas](#le-tireur-de-scores--dun-résultat-à-un-score).*

## In short

- **What goes in:** a result already chosen by the match engine, for example "draw".
- **What comes out:** a score that fits it, for example 1-1.
- **Where it is used:** after every simulated match ([`match_engine.md`](match_engine.md)), and for extra time ([`extra_time.md`](extra_time.md)).
- **Code:** `model/scorelines.py`, with the table in `data/reference/scorelines.json`. Line-by-line walkthrough: [`code/scorelines_code.md`](code/scorelines_code.md).

---

## 1. The idea: copy real football

Once the result is known, the program asks: **"among real matches that ended this way, how did they end?"** and copies that.

It uses 4 642 real matches (friendlies left out), sorted by result. The most common scores:

| Home wins (2 111 matches) | Share | Draws (975 matches) | Share | Away wins (1 556 matches) | Share |
|---|---|---|---|---|---|
| 2-1 (399) | 18.9 % | 1-1 (458) | 47.0 % | 1-2 (322) | 20.7 % |
| 1-0 (377) | 17.9 % | 2-2 (237) | 24.3 % | 0-1 (321) | 20.6 % |
| 2-0 (341) | 16.2 % | 0-0 (225) | 23.1 % | 0-2 (237) | 15.2 % |
| 3-0 (212) | 10.0 % | 3-3 (50) | 5.1 % | 1-3 (139) | 8.9 % |
| 3-1 (204) | 9.7 % | 4-4 (5) | 0.5 % | 0-3 (136) | 8.7 % |

How to read it: 458 of the 975 real draws ended 1-1, so 47.0 % of them. When the simulation has decided "draw", it will pick 1-1 about 47 % of the time.

The score is always picked **after** the result and only among scores of that result, so it can never contradict it: a home win can never become 1-1.

---

## 2. How one score is picked: a raffle

Imagine 975 raffle tickets, one per real draw: 225 tickets say "0-0", 458 say "1-1", 237 say "2-2", 50 say "3-3" and 5 say "4-4". Pick one ticket at random: 1-1 comes out 458 times in 975.

The program does the same thing without printing tickets. It lines the tickets up and adds the counts as it goes (the **running totals**):

| Score | Tickets | Running total | Ticket numbers |
|---|---|---|---|
| 0-0 | 225 | 225 | 0 to 225 |
| 1-1 | 458 | 683 | 225 to 683 |
| 2-2 | 237 | 920 | 683 to 920 |
| 3-3 | 50 | 970 | 920 to 970 |
| 4-4 | 5 | 975 | 970 to 975 |

Then it picks one random number $u$ between 0 and 1, multiplies it by 975 to get a ticket number, and looks up which score owns that ticket:

- $u = 0.37$: ticket $0.37 \times 975 = 360.75$, between 225 and 683, so **1-1**.
- $u = 0.95$: ticket $926.25$, between 920 and 970, so **3-3**.

Each score owns as many ticket numbers as it has tickets, so it comes out exactly as often as in real football.

---

## 3. Try it in Python

```python
import random
from bisect import bisect
from itertools import accumulate

# Real draws: how many ended with each score
draws = {(0, 0): 225, (1, 1): 458, (2, 2): 237, (3, 3): 50, (4, 4): 5}

scores = list(draws)                         # [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)]
running = list(accumulate(draws.values()))   # [225, 683, 920, 970, 975]
print("running totals:", running)

def pick(u):
    position = u * running[-1]               # a ticket number between 0 and 975
    return scores[bisect(running, position)]

for u in (0.37, 0.95, 0.2308):
    print(f"u = {u}: ticket {u * 975:.2f} -> {pick(u)}")

rng = random.Random(1)
counts = {s: 0 for s in scores}
for _ in range(10_000):
    counts[pick(rng.random())] += 1
print({f"{h}-{a}": n for (h, a), n in counts.items()})
```

Output:

```
running totals: [225, 683, 920, 970, 975]
u = 0.37: ticket 360.75 -> (1, 1)
u = 0.95: ticket 926.25 -> (3, 3)
u = 0.2308: ticket 225.03 -> (1, 1)
{'0-0': 2378, '1-1': 4649, '2-2': 2403, '3-3': 524, '4-4': 46}
```

Over 10 000 picks, 1-1 came out 4 649 times, 46.5 %, close to the real 47.0 %.

`accumulate` builds the running totals, and `bisect` finds in which slice a ticket number falls by halving the list again and again, like looking up a word in a dictionary, instead of reading it from the top.

---

## 4. Does it look like real football?

On 500 simulated Champions League league phases:

| | Simulation | Real matches |
|---|---|---|
| goals per match | 3.006 | 3.000 |
| home wins | 45.8 % | 45.5 % |
| draws | 19.1 % | 21.0 % |
| away wins | 35.0 % | 33.5 % |

The goals per match come from this part; the share of each result comes from the match model.

---

## 5. What it does not know: big wins and the rating gap

The table does not care **who** is playing. Given a home win, the chance of winning by 3 goals or more is 28.4 % for every match, whether Paris Saint-Germain host a small club or two equal clubs meet. Real football is different:

| Rating gap (home minus away) | Real home wins | Real share won by 3+ goals | In the simulation |
|---|---|---|---|
| −100 or less (home side much weaker) | 105 | 8.6 % | 28.4 % |
| −100 to 0 | 566 | 19.8 % | 28.4 % |
| 0 to +100 | 991 | 30.7 % | 28.4 % |
| +100 to +200 (home side much stronger) | 407 | 39.6 % | 28.4 % |

In reality, the stronger the winner, the bigger the win. The simulation flattens this. Consequence: goal difference, which decides most ties in the league table, says less about a club's strength than it should, and the rare wins of outsiders are too big.

---

## 6. What the code uses

### Python modules

| Module | Comes with Python? | What it does here |
|---|---|---|
| `bisect` | yes | finds which score owns a ticket number |
| `itertools` (`accumulate`) | yes | builds the running totals |
| `json` | yes | reads and writes `scorelines.json` |
| `random` | yes | the demo at the bottom of the file |
| `pathlib` | yes | file paths |
| `pandas` | no, install with `pip` | only to **build** the table from the real matches, once; the app never needs it |

### Functions and classes in `model/scorelines.py`

| Name | In one line |
|---|---|
| `ScorelineSampler` | holds the table, ready to pick scores |
| `ScorelineSampler.load` | reads `scorelines.json`, or a small built-in table if the file is missing |
| `ScorelineSampler.sample` | picks one score for a result (section 2) |
| `ScorelineSampler.sample_extra_time` | picks the score of 30 minutes of extra time ([`extra_time.md`](extra_time.md)) |
| `ScorelineSampler.probability` | the share of a score among scores of its result, for the expert log |
| `outcome_of` | turns a score into "home", "draw" or "away" |
| `build_table` | counts the scores of the real matches (needs pandas) |
| `save_table` | writes the counts to `scorelines.json` |

To rebuild the table from the real matches, from the project folder:

```bash
python -m model.scorelines
```

How each line works: [`code/scorelines_code.md`](code/scorelines_code.md).

### How the table is built

1. Read the real matches and remove friendlies (684 rows).
2. Use the score **after 90 minutes**, not the score after extra time; otherwise a cup match won in extra time would be filed as a win instead of a draw.
3. Remove matches without a score.
4. Any number of goals above 6 is counted as 6 (only 44 of 4 642 matches, mostly cup matches against amateur clubs, like 16-0). This keeps the table short.
5. Count each score under its result.

---

## 7. What can go wrong

- **Big wins ignore the rating gap** (section 5).
- **All levels of football are mixed**: leagues, cups against amateur clubs and European matches share one table. For European matches alone, the share of home wins by 3+ goals happens to be the same (28.3 %), so this costs little today, but by luck rather than by design.
- **No score above 6 goals** can happen in the simulation.

### Known bugs

- **Fixed in 1.1.0: capping at 6 could change the result.** The result is now read on the real score first; if the cap would make it level, the loser is put one goal behind (8-7 becomes 6-5, `cap_scoreline`). Friendlies are also left out by the same test as the Elo program (`comp_mult` 0), not only "Friendlies Clubs": 16 more friendly matches are out of the table.

---

## 8. Ideas for later

- **One table per rating gap**: four tables, one for each row of section 5, and pick from the table that matches the gap of the match. A cheap way to make strong clubs win bigger.
- **A goals model.** Instead of a table, give each side an average number of goals that depends on the rating gap, then pick each side's goals with the **Poisson law**, the usual law for things that happen at random at a steady rate. Example: a side that averages 1.6 goals per match scores 0 goals about 20 % of the time, 1 goal 32 %, 2 goals 26 %. The result (home win, draw, away win) would then come from the goals, and bigger gaps would give bigger wins on their own.

---

## 9. Words to know

| Word | Meaning |
|---|---|
| result (outcome) | home win, draw or away win |
| score (scoreline) | the goals, home first |
| running total | the counts added up as you go: 225, then 225 + 458 = 683, ... |
| goal difference | goals scored minus goals conceded |
| capping | replacing any value above a limit by the limit: with a limit of 6, 16 becomes 6 |
| Poisson law | the usual law for how many times something happens in a fixed time when it happens at random at a steady rate |


---
---

# Le tireur de scores : d'un résultat à un score

> Le modèle de match dit seulement « victoire à domicile », « nul » ou « victoire à l'extérieur ». Mais le classement a besoin de buts, car la différence de buts départage les clubs à égalité de points. Cette partie choisit un score qui correspond au résultat, à partir de la fréquence de chaque score dans 4 642 vrais matchs.

## En bref

- **Ce qui entre :** un résultat déjà choisi par le moteur de match, par exemple « nul ».
- **Ce qui sort :** un score qui lui correspond, par exemple 1-1.
- **Où c'est utilisé :** après chaque match simulé ([`match_engine.md`](match_engine.md)), et pour la prolongation ([`extra_time.md`](extra_time.md)).
- **Code :** `model/scorelines.py`, avec la table dans `data/reference/scorelines.json`. Explication ligne par ligne : [`code/scorelines_code.md`](code/scorelines_code.md).

---

## 1. L'idée : copier le vrai football

Une fois le résultat connu, le programme se demande : **« parmi les vrais matchs qui ont fini ainsi, comment ont-ils fini ? »** et copie cela.

Il utilise 4 642 vrais matchs (sans les amicaux), rangés par résultat. Les scores les plus fréquents :

| Victoires à domicile (2 111 matchs) | Part | Nuls (975 matchs) | Part | Victoires à l'extérieur (1 556 matchs) | Part |
|---|---|---|---|---|---|
| 2-1 (399) | 18.9 % | 1-1 (458) | 47.0 % | 1-2 (322) | 20.7 % |
| 1-0 (377) | 17.9 % | 2-2 (237) | 24.3 % | 0-1 (321) | 20.6 % |
| 2-0 (341) | 16.2 % | 0-0 (225) | 23.1 % | 0-2 (237) | 15.2 % |
| 3-0 (212) | 10.0 % | 3-3 (50) | 5.1 % | 1-3 (139) | 8.9 % |
| 3-1 (204) | 9.7 % | 4-4 (5) | 0.5 % | 0-3 (136) | 8.7 % |

Comment le lire : 458 des 975 vrais nuls ont fini 1-1, soit 47.0 %. Quand la simulation a décidé « nul », elle choisira 1-1 environ 47 % du temps.

Le score est toujours choisi **après** le résultat et seulement parmi les scores de ce résultat, donc il ne peut jamais le contredire : une victoire à domicile ne peut jamais devenir 1-1.

---

## 2. Comment un score est choisi : une tombola

Imaginez 975 billets de tombola, un par vrai nul : 225 billets disent « 0-0 », 458 disent « 1-1 », 237 disent « 2-2 », 50 disent « 3-3 » et 5 disent « 4-4 ». Tirez un billet au hasard : 1-1 sort 458 fois sur 975.

Le programme fait la même chose sans imprimer de billets. Il aligne les billets et additionne les nombres au fur et à mesure (les **totaux cumulés**) :

| Score | Billets | Total cumulé | Numéros de billets |
|---|---|---|---|
| 0-0 | 225 | 225 | 0 à 225 |
| 1-1 | 458 | 683 | 225 à 683 |
| 2-2 | 237 | 920 | 683 à 920 |
| 3-3 | 50 | 970 | 920 à 970 |
| 4-4 | 5 | 975 | 970 à 975 |

Puis il tire un nombre au hasard $u$ entre 0 et 1, le multiplie par 975 pour obtenir un numéro de billet, et regarde à quel score appartient ce billet :

- $u = 0.37$ : billet $0.37 \times 975 = 360.75$, entre 225 et 683, donc **1-1**.
- $u = 0.95$ : billet $926.25$, entre 920 et 970, donc **3-3**.

Chaque score possède autant de numéros qu'il a de billets, donc il sort exactement aussi souvent que dans le vrai football.

---

## 3. À essayer en Python

```python
import random
from bisect import bisect
from itertools import accumulate

# Vrais nuls : combien ont fini avec chaque score
draws = {(0, 0): 225, (1, 1): 458, (2, 2): 237, (3, 3): 50, (4, 4): 5}

scores = list(draws)                         # [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)]
running = list(accumulate(draws.values()))   # [225, 683, 920, 970, 975]
print("running totals:", running)

def pick(u):
    position = u * running[-1]               # un numéro de billet entre 0 et 975
    return scores[bisect(running, position)]

for u in (0.37, 0.95, 0.2308):
    print(f"u = {u}: ticket {u * 975:.2f} -> {pick(u)}")

rng = random.Random(1)
counts = {s: 0 for s in scores}
for _ in range(10_000):
    counts[pick(rng.random())] += 1
print({f"{h}-{a}": n for (h, a), n in counts.items()})
```

Résultat :

```
running totals: [225, 683, 920, 970, 975]
u = 0.37: ticket 360.75 -> (1, 1)
u = 0.95: ticket 926.25 -> (3, 3)
u = 0.2308: ticket 225.03 -> (1, 1)
{'0-0': 2378, '1-1': 4649, '2-2': 2403, '3-3': 524, '4-4': 46}
```

Sur 10 000 tirages, 1-1 est sorti 4 649 fois, soit 46.5 %, proche des 47.0 % réels.

`accumulate` construit les totaux cumulés, et `bisect` trouve dans quelle tranche tombe un numéro de billet en coupant la liste en deux encore et encore, comme quand on cherche un mot dans un dictionnaire, au lieu de la lire depuis le début.

---

## 4. Est-ce que ça ressemble au vrai football ?

Sur 500 phases de ligue de Ligue des champions simulées :

| | Simulation | Vrais matchs |
|---|---|---|
| buts par match | 3.006 | 3.000 |
| victoires à domicile | 45.8 % | 45.5 % |
| nuls | 19.1 % | 21.0 % |
| victoires à l'extérieur | 35.0 % | 33.5 % |

Les buts par match viennent de cette partie ; la part de chaque résultat vient du modèle de match.

---

## 5. Ce qu'il ne sait pas : les larges victoires et l'écart de notes

La table ne se soucie pas de **qui** joue. Sachant que c'est une victoire à domicile, la chance de gagner de 3 buts ou plus vaut 28.4 % pour chaque match, que le Paris Saint-Germain reçoive un petit club ou que deux clubs égaux s'affrontent. Le vrai football est différent :

| Écart de notes (domicile moins extérieur) | Vraies victoires à domicile | Vraie part gagnée de 3 buts ou plus | Dans la simulation |
|---|---|---|---|
| −100 ou moins (domicile bien plus faible) | 105 | 8.6 % | 28.4 % |
| −100 à 0 | 566 | 19.8 % | 28.4 % |
| 0 à +100 | 991 | 30.7 % | 28.4 % |
| +100 à +200 (domicile bien plus fort) | 407 | 39.6 % | 28.4 % |

En réalité, plus le vainqueur est fort, plus la victoire est large. La simulation aplatit cela. Conséquence : la différence de buts, qui départage la plupart des égalités au classement, en dit moins sur la force d'un club qu'elle ne le devrait, et les rares victoires des outsiders sont trop larges.

---

## 6. Ce que le code utilise

### Modules Python

| Module | Fourni avec Python ? | Ce qu'il fait ici |
|---|---|---|
| `bisect` | oui | trouve à quel score appartient un numéro de billet |
| `itertools` (`accumulate`) | oui | construit les totaux cumulés |
| `json` | oui | lit et écrit `scorelines.json` |
| `random` | oui | la démo en bas du fichier |
| `pathlib` | oui | chemins de fichiers |
| `pandas` | non, à installer avec `pip` | seulement pour **construire** la table à partir des vrais matchs, une fois ; l'appli n'en a jamais besoin |

### Fonctions et classes de `model/scorelines.py`

| Nom | En une ligne |
|---|---|
| `ScorelineSampler` | garde la table, prête à choisir des scores |
| `ScorelineSampler.load` | lit `scorelines.json`, ou une petite table intégrée si le fichier manque |
| `ScorelineSampler.sample` | choisit un score pour un résultat (section 2) |
| `ScorelineSampler.sample_extra_time` | choisit le score de 30 minutes de prolongation ([`extra_time.md`](extra_time.md)) |
| `ScorelineSampler.probability` | la part d'un score parmi les scores de son résultat, pour le journal expert |
| `outcome_of` | transforme un score en « home », « draw » ou « away » |
| `build_table` | compte les scores des vrais matchs (a besoin de pandas) |
| `save_table` | écrit les comptes dans `scorelines.json` |

Pour reconstruire la table à partir des vrais matchs, depuis le dossier du projet :

```bash
python -m model.scorelines
```

Comment marche chaque ligne : [`code/scorelines_code.md`](code/scorelines_code.md).

### Comment la table est construite

1. Lire les vrais matchs et retirer les amicaux (684 lignes).
2. Utiliser le score **après 90 minutes**, pas le score après prolongation ; sinon un match de coupe gagné en prolongation serait rangé comme une victoire au lieu d'un nul.
3. Retirer les matchs sans score.
4. Tout nombre de buts au-dessus de 6 compte comme 6 (seulement 44 matchs sur 4 642, surtout des matchs de coupe contre des clubs amateurs, comme 16-0). Cela garde la table courte.
5. Compter chaque score sous son résultat.

---

## 7. Ce qui peut mal tourner

- **Les larges victoires ignorent l'écart de notes** (section 5).
- **Tous les niveaux de football sont mélangés** : championnats, coupes contre des amateurs et matchs européens partagent une seule table. Pour les seuls matchs européens, la part des victoires à domicile de 3 buts ou plus est par hasard la même (28.3 %), donc cela coûte peu aujourd'hui, mais par chance et non par conception.
- **Aucun score au-dessus de 6 buts** ne peut arriver dans la simulation.

### Bugs connus

- **Corrigé en 1.1.0 : plafonner à 6 pouvait changer le résultat.** Le résultat est maintenant lu d'abord sur le vrai score ; si le plafond le rendait égal, le perdant est mis un but derrière (8-7 devient 6-5, `cap_scoreline`). Les amicaux sont aussi écartés par le même test que le programme Elo (`comp_mult` 0), pas seulement « Friendlies Clubs » : 16 matchs amicaux de plus sortent de la table.

---

## 8. Idées pour plus tard

- **Une table par écart de notes** : quatre tables, une pour chaque ligne de la section 5, et choisir dans la table qui correspond à l'écart du match. Une façon peu coûteuse de faire gagner les clubs forts plus largement.
- **Un modèle de buts.** Au lieu d'une table, donner à chaque camp un nombre moyen de buts qui dépend de l'écart de notes, puis tirer les buts de chaque camp avec la **loi de Poisson**, la loi habituelle des choses qui arrivent au hasard à un rythme régulier. Exemple : une équipe qui marque en moyenne 1.6 but par match marque 0 but environ 20 % du temps, 1 but 32 %, 2 buts 26 %. Le résultat (victoire à domicile, nul, victoire à l'extérieur) viendrait alors des buts, et les grands écarts donneraient d'eux-mêmes de plus larges victoires.

---

## 9. Mots à connaître

| Mot | Sens |
|---|---|
| résultat | victoire à domicile, nul ou victoire à l'extérieur |
| score | les buts, domicile d'abord |
| total cumulé | les nombres additionnés au fur et à mesure : 225, puis 225 + 458 = 683, ... |
| différence de buts | buts marqués moins buts encaissés |
| plafonner | remplacer toute valeur au-dessus d'une limite par la limite : avec une limite de 6, 16 devient 6 |
| loi de Poisson | la loi habituelle du nombre de fois qu'une chose arrive pendant un temps fixe, quand elle arrive au hasard à un rythme régulier |

---

