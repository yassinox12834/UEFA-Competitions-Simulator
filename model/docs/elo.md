# Elo ratings: one number for each club's strength

> Every club gets one number that says how strong it is. After each match, the number goes up or down depending on how surprising the result was. These numbers are the starting point of the whole simulation.

*Version française : [plus bas](#les-notes-elo--un-nombre-pour-la-force-de-chaque-club).*

## In short

- **What goes in:** about 5 300 real matches (January 2024 to August 2025): league, cup, European and friendly matches.
- **What comes out:** a rating for each of 984 clubs (for example Paris Saint-Germain about 1853, a small club about 1400), saved in `data/processed/eeelo_final.json`.
- **Where it is used:** the match model ([`logistic_regression.md`](logistic_regression.md)) turns the gap between two ratings into chances of winning, and the simulation keeps updating the ratings after every simulated match.
- **Code:** `model/elo_score_updating_copy.py`. Line-by-line walkthrough: [`code/elo_code.md`](code/elo_code.md).

---

## 1. A short history

At first, chess players were ranked by hand, and a lot of it was opinion. Clubs wanted a fair and simple method.

**Arpad Elo** (1903 to 1992) was a Hungarian-born American physics teacher and a strong chess player. His idea: **a rating is a guess of your strength, and every game tells you if the guess was too high or too low.**

| Year | What happened |
|---|---|
| 1960 | The United States Chess Federation adopts Elo's method. |
| 1970 | FIDE, the world chess federation, adopts it. |
| 1990s | People start using it for football national teams. |
| 2018 | FIFA moves its men's world ranking to an Elo-style method. |
| Today | Video games, esports, tennis and club football use it or a cousin of it. |

Football has the same shape as chess: two sides, one result, and a rating that should move after each match.

Video: [The Elo Rating System for Chess and Beyond (singingbanana, YouTube)](https://www.youtube.com/watch?v=AsYfbmp0To0).

---

## 2. The idea in plain words

Think of a rating as a **guess** about a club, like a teacher's guess about a pupil's level.

- If a strong pupil gets a good mark, the teacher is not surprised: the guess barely changes.
- If a weak pupil gets a great mark, the teacher is surprised: the guess goes up a lot.
- If a strong pupil fails, the guess goes down a lot.

Elo does the same with football:

- Beat a much stronger club: your rating goes up a lot.
- Beat a much weaker club: it goes up a little.
- Lose to a much weaker club: it drops a lot.

Only the **gap** between two ratings matters. 1800 against 1700 means the same as 1600 against 1500: one club is 100 points stronger.

---

## 3. Step 1: what result do we expect?

Before the match, Elo turns the rating gap into an **expected score**: how much of the match the club "should" win, on a scale from 0 to 1.

In Elo, one match gives out exactly 1 point: the winner takes 1, the loser 0, and a draw gives 0.5 to each side. The expected score is the share of that point a club should take on average.

| Rating gap (your club minus the other) | Expected score of your club |
|---|---|
| −400 | 0.09 |
| −200 | 0.24 |
| −100 | 0.36 |
| 0 (equal clubs) | 0.50 |
| +100 | 0.64 |
| +200 | 0.76 |
| +400 | 0.91 |

How to read a row: with a gap of +100, your club should take 0.64 of the point on average. Over 100 matches like this, it would collect about 64 points, for example 54 wins and 20 draws.

The two expected scores always add up to 1: if your club expects 0.64, the other expects 0.36.

The table comes from this formula:

$$E = \frac{1}{1 + 10^{(R_{\text{other}} - R_{\text{yours}})/400}}$$

| Symbol | In plain words |
|---|---|
| $E$ | the expected score of your club, between 0 and 1 |
| $R_{\text{yours}}$ | your club's rating before the match |
| $R_{\text{other}}$ | the other club's rating before the match |
| 400 | a fixed choice of scale: with a gap of 400 points, the stronger club expects to take 10 times more of the point than the weaker one (0.91 against 0.09) |

You do not need to compute it by hand: the table above shows what it gives.

---

## 4. Step 2: update the ratings after the match

After the match, compare what happened with what was expected:

$$\text{new rating} = \text{old rating} + K \times (\text{result} - \text{expected score})$$

| Part | In plain words |
|---|---|
| result | 1 for a win, 0.5 for a draw, 0 for a defeat |
| result minus expected score | the **surprise**: positive if the club did better than expected, negative if worse |
| $K$ | how much one match can move a rating: about 20 to 27 points here (section 5) |

### Example: Arsenal 2-0 Atalanta (Champions League, $K = 24$)

| | Arsenal (home) | Atalanta |
|---|---|---|
| Rating before | 1787.88 | 1720.12 |
| Expected score | 0.596 | 0.404 |
| Result | 1 (win) | 0 (defeat) |
| Surprise | 1 − 0.596 = +0.404 | 0 − 0.404 = −0.404 |
| Change | 24 × 0.404 = **+9.69** | 24 × (−0.404) = **−9.69** |
| Rating after | 1797.57 | 1710.43 |

Arsenal were favourites, so a win is only a small surprise: +9.69 points.

### Same match, but 1-1

Both clubs get 0.5. Arsenal's surprise is 0.5 − 0.596 = −0.096, so they **lose** 2.31 points. Atalanta **gain** 2.31. A draw is a small disappointment for the favourite and a small success for the outsider.

### What one club wins, the other loses

In both examples, Arsenal's change and Atalanta's change add up to 0. This is always true when both clubs use the same $K$: the expected scores add up to 1, and the results add up to 1, so the two surprises cancel out. Points move from one club to the other; none are created or lost. This is called **zero-sum**. On the real data, after 4 626 rated matches, the total of all changes over 984 clubs is 0.00.

---

## 5. Not every match counts the same: the value of K

A Champions League final should move a rating more than a league match in August. So $K$ depends on the competition and the round:

$$K = 20 \times \text{competition weight} \times \text{round weight}$$

| Competition | Weight | Examples of rounds |
|---|---|---|
| Champions League | 1.20 | league phase 1.00, quarter-final 1.08, final 1.12 |
| Europa League | 1.12 | same round weights |
| Conference League | 1.06 | same round weights |
| Domestic league | 1.00 | |
| Domestic cup | 0.95 | |
| Friendly | 0 | friendlies do not change ratings at all |

Example: a Champions League quarter-final has $K = 20 \times 1.20 \times 1.08 = 25.92$.

The resulting values, from the smallest to the largest:

| Competition | league phase | play-off | round of 16 | quarter-final | semi-final | final |
|---|---|---|---|---|---|---|
| Champions League | 24.00 | 24.72 | 25.44 | 25.92 | 26.40 | 26.88 |
| Europa League | 22.40 | 23.07 | 23.74 | 24.19 | 24.64 | 25.09 |
| Conference League | 21.20 | 21.84 | 22.47 | 22.90 | 23.32 | 23.74 |
| Domestic league | 20.00 | | | | | |

The weights stay close to 1 on purpose. The strength of the opponent already counts through the expected score (beating a strong club already pays more), so a big "important match" bonus would count the same thing twice. There is also a ceiling: $K$ can never go above 30.

### Careful: two files, two sets of weights

The weights above are the ones in `data/reference/coefs.json`. The **simulation** reads that file.

But the program that computes the real ratings from the 5 300 real matches reads another file, `data/reference/coef_table.csv` (1 370 rows that say which competition and which round each real match belongs to). That file still holds older, much bigger weights: 3.0 for the Champions League, 2.0 for the Europa League, 1.5 for the Conference League, 0.5 for domestic cups.

| Real match | $K$ in the simulation (`coefs.json`) | $K$ when computing the real ratings (`coef_table.csv`) |
|---|---|---|
| Champions League, league phase | 24.00 | $20 \times 3.0 \times 1.0 = 60$, capped at **30** |
| Europa League, league phase | 22.40 | $20 \times 2.0 \times 1.0 = 40$, capped at **30** |
| Domestic league | 20.00 | 20.00 |
| Domestic cup, early round | 18.05 | $20 \times 0.5 \times 0.9 =$ **9** |

So every European match of the real data moves ratings at the ceiling of 30, and domestic cup matches count about half as much as intended. This is listed in the bugs (section 10).

---

## 6. Where the ratings start

Before the first match, every club needs a starting rating.

- **From its country.** Each country has a starting value: from 1319 (San Marino) to 1670 (England), 1500 in the middle. A club starts with its country's value. So Liverpool and Southampton both start at 1669.46, and the matches then separate them.
- **When the country is unknown.** 320 clubs only appear in European or friendly matches, so their country cannot be read from the data. They start at **1450**, a little below average: a club we know nothing about is more likely to be small than big.

The country is read from domestic matches only. A European match is marked "World" in the data, so it says nothing about the clubs' countries.

---

## 7. Why the matches must be in date order

Each update uses the ratings left by every match before it. So the order matters:

- Beating Arsenal before their bad run, or after it, is not worth the same.
- More importantly, the program also saves, for each match, both ratings **before** it was played. The match model learns from those rows. If the matches were shuffled, the "rating before" a September match could already include results from May. The model would learn from the future and look better than it really is. This mistake has a name: **data leakage**.

So the program sorts all matches by date first.

---

## 8. Try it in Python

```python
def expected_score(r_yours, r_other):
    return 1 / (1 + 10 ** ((r_other - r_yours) / 400))

def update(rating, k, result, expected):
    return rating + k * (result - expected)

arsenal, atalanta = 1787.88, 1720.12
e = expected_score(arsenal, atalanta)
print("Arsenal expected score:", round(e, 3))

for name, result in [("win", 1), ("draw", 0.5), ("defeat", 0)]:
    new_arsenal = update(arsenal, 24, result, e)
    new_atalanta = update(atalanta, 24, 1 - result, 1 - e)
    print(f"Arsenal {name}: {new_arsenal:.2f}, Atalanta: {new_atalanta:.2f}")
```

Output:

```
Arsenal expected score: 0.596
Arsenal win: 1797.57, Atalanta: 1710.43
Arsenal draw: 1785.57, Atalanta: 1722.43
Arsenal defeat: 1773.57, Atalanta: 1734.43
```

Notice: Arsenal win 9.69 points for a win but lose 14.31 for a defeat. A defeat was more surprising, so it moves the ratings more.

---

## 9. What the code uses

### Python modules

| Module | Comes with Python? | What it does here |
|---|---|---|
| `pandas` | no, install with `pip` | reads the 5 328 matches from the CSV file, turns timestamps into dates, sorts by date, writes the output table |
| `numpy` | no, install with `pip` | `np.sign` turns a goal difference into +1, 0 or −1; `np.nan` marks a match not played yet |
| `json` | yes | reads the starting ratings and the settings, writes the final ratings |
| `csv` | yes | reads the table of competition and round weights |
| `pathlib` | yes | builds file paths that work on Windows, macOS and Linux |
| `sys` | yes | reads the `--write` option from the command line |

### Functions in `model/elo_score_updating_copy.py`

| Function | In one line |
|---|---|
| `expected_score` | the expected score of section 3 |
| `update_rating` | the update of section 4 |
| `result_scores` | turns goals into results: 1, 0.5 or 0 for each side |
| `season_from_date` | says which season a date belongs to (a season starts in July) |
| `load_seed`, `load_country_seeds` | read the starting ratings |
| `load_k_settings`, `load_coef_table` | read the settings of section 5 |
| `build_club_country` | finds each club's country from domestic matches |
| `load_clubs` | gives every club its starting rating (section 6) |
| `find_goal_columns` | finds which columns of the data hold the goals |
| `run` | does everything in order and saves the results |
| `report` | prints a summary: how many matches were rated, biggest risers and fallers |

`expected_score` and `update_rating` are also used by the simulation: `model/match_engine.py` and `model/knockout.py` import them.

How to run it, from the project folder:

```bash
python -m model.elo_score_updating_copy           # compute and print the report
python -m model.elo_score_updating_copy --write   # also save eeelo_final.json
```

How each line works: [`code/elo_code.md`](code/elo_code.md).

### Files

| File | Role |
|---|---|
| `data/processed/fixtures_25.csv` | input: the real matches |
| `data/reference/country_seeds.json`, `team_seed.json` | input: starting ratings |
| `data/reference/coefs.json`, `coef_table.csv` | input: the weights of section 5 |
| `data/processed/eeelo_final.json` | output: the final rating of every club |
| `data/processed/match_features.csv` | output: one row per match with both ratings before it, used to train the match model |

`model/elo.py` is an old first version. Nothing uses it any more.

---

## 10. What can go wrong

- **No home advantage.** Two equal clubs both expect 0.5, wherever they play. In reality the home side wins more often. So a club gains points for normal home wins and loses some for normal away defeats.
- **The score does not count.** A 4-1 and a 1-0 move the ratings by exactly the same amount.
- **A 0-0 and a 4-4 are the same.** Both are just "a draw".
- **Guessed starts.** 320 clubs start at 1450 because their country is unknown, and the error spreads to the clubs they play.
- **Short history.** About 1.5 seasons of data. Many clubs never get far from their starting value.
- **$K = 20$ is a reasoned guess, not a measured value** (section 11 explains how to measure it).

### Known bugs

- **The real ratings use old weights.** `coef_table.csv` was not updated when `coefs.json` changed (section 5). Fix: rebuild the weight columns of `coef_table.csv` from `coefs.json`, or make the program read the weights from `coefs.json` and use the CSV only to know which competition and round a match belongs to. Then recompute the ratings with `--write` and retrain the match model.
- **The "home" column is always 0.** In the data, the "neutral venue" column is empty for most matches. Python treats an empty value as "true", so every match is marked as played on neutral ground. Nothing in the ratings uses this column, but the match model's training data does.
- **Friendlies are in the training data.** Friendlies do not change ratings ($K = 0$), but they are still written to `match_features.csv`, so the match model learns from 625 friendlies.
- **"Report only" still writes a file.** Without `--write`, `match_features.csv` is still overwritten.
- **Two default values.** 1450 here, but 1500 in the simulation, for the same idea ("a club with no known rating").
- **Extra-time goals are counted here** but not in the simulation (see [`extra_time.md`](extra_time.md)).
- **The text at the top of the file is out of date.** It mentions old file names.

---

## 11. Ideas for later

- **Home advantage inside Elo.** Give the home side about 50 to 70 extra points when computing the expected score, and 0 at a neutral ground.
- **Count the score a little.** Make $K$ grow slowly with the goal difference, so a 4-0 counts more than a 1-0, but not four times more.
- **Pull ratings back towards the average each summer.** Squads change most in summer. One idea: keep 70 % of each club's distance from the average. With an average of 1500, a club at 1800 would start the next season at 1500 + 0.7 × 300 = 1710, and a club at 1350 at 1395. The setting is already in `coefs.json` (`season_regression = 0.7`) but no code uses it yet.
- **Measure the best $K$.** Run the ratings with several values (10, 14, 18, 20, 24, 30). For each one, measure how well the expected scores predicted the real results (the "surprise" measure explained in [`logistic_regression.md`](logistic_regression.md), section 10). Too small a $K$ learns too slowly; too big a $K$ jumps after every lucky result. Keep the value in the middle that predicts best.

---

## 12. Words to know

| Word | Meaning |
|---|---|
| rating | one number for a club's strength; only gaps between ratings mean something |
| expected score | the share of the point a club should take, from 0 to 1 |
| surprise | result minus expected score |
| $K$ | how much one match can move a rating |
| zero-sum | what one club gains, the other loses; the total never changes |
| seed | a starting rating |
| data leakage | using information from after an event to describe the event; it makes a model look better than it is |

---
---

# Les notes Elo : un nombre pour la force de chaque club

> Chaque club reçoit un nombre qui dit à quel point il est fort. Après chaque match, ce nombre monte ou descend selon à quel point le résultat était surprenant. Ces nombres sont le point de départ de toute la simulation.

## En bref

- **Ce qui entre :** environ 5 300 vrais matchs (de janvier 2024 à août 2025) : championnat, coupe, Europe et matchs amicaux.
- **Ce qui sort :** une note pour chacun des 984 clubs (par exemple environ 1853 pour le Paris Saint-Germain, environ 1400 pour un petit club), enregistrée dans `data/processed/eeelo_final.json`.
- **Où c'est utilisé :** le modèle de match ([`logistic_regression.md`](logistic_regression.md)) transforme l'écart entre deux notes en chances de gagner, et la simulation continue de mettre les notes à jour après chaque match simulé.
- **Code :** `model/elo_score_updating_copy.py`. Explication ligne par ligne : [`code/elo_code.md`](code/elo_code.md).

---

## 1. Petite histoire

Au début, les joueurs d'échecs étaient classés à la main, et c'était surtout une question d'avis. Les clubs voulaient une méthode juste et simple.

**Arpad Elo** (1903 à 1992) était un professeur de physique américain né en Hongrie, et un bon joueur d'échecs. Son idée : **une note est une supposition sur ta force, et chaque partie te dit si la supposition était trop haute ou trop basse.**

| Année | Ce qui s'est passé |
|---|---|
| 1960 | La fédération d'échecs des États-Unis adopte la méthode d'Elo. |
| 1970 | La FIDE, la fédération mondiale d'échecs, l'adopte. |
| Années 1990 | On commence à l'utiliser pour les équipes nationales de football. |
| 2018 | La FIFA passe son classement mondial masculin à une méthode de type Elo. |
| Aujourd'hui | Jeux vidéo, esport, tennis et football de clubs l'utilisent, elle ou une cousine. |

Le football a la même forme que les échecs : deux camps, un résultat, et une note qui devrait bouger après chaque match.

Vidéo (en anglais) : [The Elo Rating System for Chess and Beyond (singingbanana, YouTube)](https://www.youtube.com/watch?v=AsYfbmp0To0).

---

## 2. L'idée avec des mots simples

Vois une note comme une **supposition** sur un club, comme celle d'un professeur sur le niveau d'un élève.

- Si un bon élève a une bonne note, le professeur n'est pas surpris : sa supposition bouge à peine.
- Si un élève faible a une très bonne note, le professeur est surpris : sa supposition monte beaucoup.
- Si un bon élève rate, la supposition baisse beaucoup.

Elo fait pareil avec le football :

- Battre un club beaucoup plus fort : ta note monte beaucoup.
- Battre un club beaucoup plus faible : elle monte un peu.
- Perdre contre un club beaucoup plus faible : elle baisse beaucoup.

Seul l'**écart** entre deux notes compte. 1800 contre 1700 veut dire la même chose que 1600 contre 1500 : un club a 100 points de plus.

---

## 3. Étape 1 : quel résultat attend-on ?

Avant le match, Elo transforme l'écart de notes en **score attendu** : la part du match que le club « devrait » gagner, sur une échelle de 0 à 1.

Avec Elo, un match distribue exactement 1 point : le gagnant prend 1, le perdant 0, et un nul donne 0.5 à chaque camp. Le score attendu est la part de ce point qu'un club devrait prendre en moyenne.

| Écart de notes (ton club moins l'autre) | Score attendu de ton club |
|---|---|
| −400 | 0.09 |
| −200 | 0.24 |
| −100 | 0.36 |
| 0 (clubs égaux) | 0.50 |
| +100 | 0.64 |
| +200 | 0.76 |
| +400 | 0.91 |

Comment lire une ligne : avec un écart de +100, ton club devrait prendre 0.64 du point en moyenne. Sur 100 matchs comme celui-ci, il récolterait environ 64 points, par exemple 54 victoires et 20 nuls.

Les deux scores attendus font toujours 1 au total : si ton club attend 0.64, l'autre attend 0.36.

Le tableau vient de cette formule :

$$E = \frac{1}{1 + 10^{(R_{\text{autre}} - R_{\text{toi}})/400}}$$

| Symbole | Avec des mots simples |
|---|---|
| $E$ | le score attendu de ton club, entre 0 et 1 |
| $R_{\text{toi}}$ | la note de ton club avant le match |
| $R_{\text{autre}}$ | la note de l'autre club avant le match |
| 400 | un choix d'échelle fixe : avec 400 points d'écart, le club le plus fort s'attend à prendre 10 fois plus du point que le plus faible (0.91 contre 0.09) |

Pas besoin de la calculer à la main : le tableau au-dessus montre ce qu'elle donne.

---

## 4. Étape 2 : mettre les notes à jour après le match

Après le match, on compare ce qui s'est passé avec ce qui était attendu :

$$\text{nouvelle note} = \text{ancienne note} + K \times (\text{résultat} - \text{score attendu})$$

| Partie | Avec des mots simples |
|---|---|
| résultat | 1 pour une victoire, 0.5 pour un nul, 0 pour une défaite |
| résultat moins score attendu | la **surprise** : positive si le club a fait mieux que prévu, négative s'il a fait moins bien |
| $K$ | de combien un match peut faire bouger une note : environ 20 à 27 points ici (section 5) |

### Exemple : Arsenal 2-0 Atalanta (Ligue des champions, $K = 24$)

| | Arsenal (domicile) | Atalanta |
|---|---|---|
| Note avant | 1787.88 | 1720.12 |
| Score attendu | 0.596 | 0.404 |
| Résultat | 1 (victoire) | 0 (défaite) |
| Surprise | 1 − 0.596 = +0.404 | 0 − 0.404 = −0.404 |
| Changement | 24 × 0.404 = **+9.69** | 24 × (−0.404) = **−9.69** |
| Note après | 1797.57 | 1710.43 |

Arsenal étaient favoris, donc une victoire n'est qu'une petite surprise : +9.69 points.

### Même match, mais 1-1

Les deux clubs reçoivent 0.5. La surprise d'Arsenal vaut 0.5 − 0.596 = −0.096, donc ils **perdent** 2.31 points. L'Atalanta **gagne** 2.31. Un nul est une petite déception pour le favori et un petit succès pour l'outsider.

### Ce qu'un club gagne, l'autre le perd

Dans les deux exemples, le changement d'Arsenal et celui de l'Atalanta font 0 au total. C'est toujours vrai quand les deux clubs utilisent le même $K$ : les scores attendus font 1 au total, les résultats aussi, donc les deux surprises s'annulent. Des points passent d'un club à l'autre ; aucun n'est créé ni perdu. On appelle cela un **jeu à somme nulle**. Sur les vraies données, après 4 626 matchs notés, le total de tous les changements sur 984 clubs vaut 0.00.

---

## 5. Tous les matchs ne comptent pas pareil : la valeur de K

Une finale de Ligue des champions devrait faire bouger une note plus qu'un match de championnat en août. Donc $K$ dépend de la compétition et du tour :

$$K = 20 \times \text{poids de la compétition} \times \text{poids du tour}$$

| Compétition | Poids | Exemples de tours |
|---|---|---|
| Ligue des champions | 1.20 | phase de ligue 1.00, quart de finale 1.08, finale 1.12 |
| Ligue Europa | 1.12 | mêmes poids de tour |
| Ligue Conférence | 1.06 | mêmes poids de tour |
| Championnat national | 1.00 | |
| Coupe nationale | 0.95 | |
| Match amical | 0 | les amicaux ne changent pas du tout les notes |

Exemple : un quart de finale de Ligue des champions a $K = 20 \times 1.20 \times 1.08 = 25.92$.

Les valeurs obtenues, de la plus petite à la plus grande :

| Compétition | phase de ligue | barrage | huitièmes | quarts | demies | finale |
|---|---|---|---|---|---|---|
| Ligue des champions | 24.00 | 24.72 | 25.44 | 25.92 | 26.40 | 26.88 |
| Ligue Europa | 22.40 | 23.07 | 23.74 | 24.19 | 24.64 | 25.09 |
| Ligue Conférence | 21.20 | 21.84 | 22.47 | 22.90 | 23.32 | 23.74 |
| Championnat national | 20.00 | | | | | |

Les poids restent proches de 1 exprès. La force de l'adversaire compte déjà grâce au score attendu (battre un club fort rapporte déjà plus), donc un gros bonus « match important » compterait deux fois la même chose. Il y a aussi un plafond : $K$ ne peut jamais dépasser 30.

### Attention : deux fichiers, deux jeux de poids

Les poids ci-dessus sont ceux de `data/reference/coefs.json`. La **simulation** lit ce fichier.

Mais le programme qui calcule les vraies notes à partir des 5 300 vrais matchs lit un autre fichier, `data/reference/coef_table.csv` (1 370 lignes qui disent à quelle compétition et à quel tour appartient chaque vrai match). Ce fichier contient encore d'anciens poids, beaucoup plus gros : 3.0 pour la Ligue des champions, 2.0 pour la Ligue Europa, 1.5 pour la Ligue Conférence, 0.5 pour les coupes nationales.

| Vrai match | $K$ dans la simulation (`coefs.json`) | $K$ pour calculer les vraies notes (`coef_table.csv`) |
|---|---|---|
| Ligue des champions, phase de ligue | 24.00 | $20 \times 3.0 \times 1.0 = 60$, plafonné à **30** |
| Ligue Europa, phase de ligue | 22.40 | $20 \times 2.0 \times 1.0 = 40$, plafonné à **30** |
| Championnat national | 20.00 | 20.00 |
| Coupe nationale, premier tour | 18.05 | $20 \times 0.5 \times 0.9 =$ **9** |

Chaque match européen des vraies données fait donc bouger les notes au plafond de 30, et les matchs de coupe nationale comptent environ moitié moins que prévu. C'est noté dans les bugs (section 10).

---

## 6. D'où partent les notes

Avant le premier match, chaque club a besoin d'une note de départ.

- **Selon son pays.** Chaque pays a une valeur de départ : de 1319 (Saint-Marin) à 1670 (Angleterre), 1500 au milieu. Un club part de la valeur de son pays. Liverpool et Southampton partent donc tous les deux de 1669.46, puis les matchs les séparent.
- **Quand le pays est inconnu.** 320 clubs n'apparaissent que dans des matchs européens ou amicaux, donc leur pays ne peut pas être lu dans les données. Ils partent de **1450**, un peu sous la moyenne : un club dont on ne sait rien a plus de chances d'être petit que grand.

Le pays est lu seulement dans les matchs nationaux. Un match européen est marqué « World » dans les données, donc il ne dit rien du pays des clubs.

---

## 7. Pourquoi les matchs doivent être dans l'ordre des dates

Chaque mise à jour utilise les notes laissées par tous les matchs d'avant. L'ordre compte donc :

- Battre Arsenal avant ou après leur mauvaise série ne vaut pas la même chose.
- Surtout, le programme garde aussi, pour chaque match, les deux notes **avant** qu'il soit joué. Le modèle de match apprend à partir de ces lignes. Si les matchs étaient mélangés, la « note avant » d'un match de septembre pourrait déjà contenir des résultats de mai. Le modèle apprendrait à partir du futur et paraîtrait meilleur qu'il ne l'est. Cette erreur a un nom : la **fuite de données**.

Le programme trie donc d'abord tous les matchs par date.

---

## 8. À essayer en Python

```python
def expected_score(r_yours, r_other):
    return 1 / (1 + 10 ** ((r_other - r_yours) / 400))

def update(rating, k, result, expected):
    return rating + k * (result - expected)

arsenal, atalanta = 1787.88, 1720.12
e = expected_score(arsenal, atalanta)
print("Arsenal expected score:", round(e, 3))

for name, result in [("win", 1), ("draw", 0.5), ("defeat", 0)]:
    new_arsenal = update(arsenal, 24, result, e)
    new_atalanta = update(atalanta, 24, 1 - result, 1 - e)
    print(f"Arsenal {name}: {new_arsenal:.2f}, Atalanta: {new_atalanta:.2f}")
```

Résultat :

```
Arsenal expected score: 0.596
Arsenal win: 1797.57, Atalanta: 1710.43
Arsenal draw: 1785.57, Atalanta: 1722.43
Arsenal defeat: 1773.57, Atalanta: 1734.43
```

À remarquer : Arsenal gagnent 9.69 points pour une victoire mais en perdent 14.31 pour une défaite. Une défaite était plus surprenante, donc elle fait bouger les notes davantage.

---

## 9. Ce que le code utilise

### Modules Python

| Module | Fourni avec Python ? | Ce qu'il fait ici |
|---|---|---|
| `pandas` | non, à installer avec `pip` | lit les 5 328 matchs du fichier CSV, transforme les horodatages en dates, trie par date, écrit le tableau de sortie |
| `numpy` | non, à installer avec `pip` | `np.sign` transforme une différence de buts en +1, 0 ou −1 ; `np.nan` marque un match pas encore joué |
| `json` | oui | lit les notes de départ et les réglages, écrit les notes finales |
| `csv` | oui | lit le tableau des poids des compétitions et des tours |
| `pathlib` | oui | construit des chemins de fichiers qui marchent sous Windows, macOS et Linux |
| `sys` | oui | lit l'option `--write` dans la ligne de commande |

### Fonctions de `model/elo_score_updating_copy.py`

| Fonction | En une ligne |
|---|---|
| `expected_score` | le score attendu de la section 3 |
| `update_rating` | la mise à jour de la section 4 |
| `result_scores` | transforme les buts en résultats : 1, 0.5 ou 0 pour chaque camp |
| `season_from_date` | dit à quelle saison appartient une date (une saison commence en juillet) |
| `load_seed`, `load_country_seeds` | lisent les notes de départ |
| `load_k_settings`, `load_coef_table` | lisent les réglages de la section 5 |
| `build_club_country` | trouve le pays de chaque club grâce aux matchs nationaux |
| `load_clubs` | donne à chaque club sa note de départ (section 6) |
| `find_goal_columns` | trouve quelles colonnes des données contiennent les buts |
| `run` | fait tout dans l'ordre et enregistre les résultats |
| `report` | affiche un résumé : combien de matchs ont été notés, plus fortes hausses et baisses |

`expected_score` et `update_rating` servent aussi à la simulation : `model/match_engine.py` et `model/knockout.py` les importent.

Pour le lancer, depuis le dossier du projet :

```bash
python -m model.elo_score_updating_copy           # calcule et affiche le rapport
python -m model.elo_score_updating_copy --write   # enregistre aussi eeelo_final.json
```

Comment marche chaque ligne : [`code/elo_code.md`](code/elo_code.md).

### Fichiers

| Fichier | Rôle |
|---|---|
| `data/processed/fixtures_25.csv` | entrée : les vrais matchs |
| `data/reference/country_seeds.json`, `team_seed.json` | entrée : notes de départ |
| `data/reference/coefs.json`, `coef_table.csv` | entrée : les poids de la section 5 |
| `data/processed/eeelo_final.json` | sortie : la note finale de chaque club |
| `data/processed/match_features.csv` | sortie : une ligne par match avec les deux notes d'avant, pour entraîner le modèle de match |

`model/elo.py` est une ancienne première version. Plus rien ne l'utilise.

---

## 10. Ce qui peut mal tourner

- **Pas d'avantage du terrain.** Deux clubs égaux attendent tous les deux 0.5, où qu'ils jouent. En réalité, l'équipe à domicile gagne plus souvent. Un club gagne donc des points pour des victoires normales à domicile et en perd pour des défaites normales à l'extérieur.
- **Le score ne compte pas.** Un 4-1 et un 1-0 font bouger les notes exactement autant.
- **Un 0-0 et un 4-4, c'est pareil.** Les deux sont juste « un nul ».
- **Départs devinés.** 320 clubs partent de 1450 car leur pays est inconnu, et l'erreur se propage aux clubs qu'ils affrontent.
- **Historique court.** Environ 1.5 saison de données. Beaucoup de clubs ne s'éloignent jamais beaucoup de leur valeur de départ.
- **$K = 20$ est une supposition raisonnée, pas une valeur mesurée** (la section 11 explique comment la mesurer).

### Bugs connus

- **Les vraies notes utilisent d'anciens poids.** `coef_table.csv` n'a pas été mis à jour quand `coefs.json` a changé (section 5). Correction : reconstruire les colonnes de poids de `coef_table.csv` à partir de `coefs.json`, ou faire lire les poids dans `coefs.json` et n'utiliser le CSV que pour savoir à quelle compétition et à quel tour appartient un match. Puis recalculer les notes avec `--write` et réentraîner le modèle de match.
- **La colonne « domicile » vaut toujours 0.** Dans les données, la colonne « terrain neutre » est vide pour la plupart des matchs. Python considère une valeur vide comme « vraie », donc chaque match est marqué comme joué sur terrain neutre. Rien dans les notes n'utilise cette colonne, mais les données d'entraînement du modèle de match, si.
- **Les amicaux sont dans les données d'entraînement.** Les amicaux ne changent pas les notes ($K = 0$), mais ils sont quand même écrits dans `match_features.csv`, donc le modèle de match apprend à partir de 625 amicaux.
- **« Rapport seulement » écrit quand même un fichier.** Sans `--write`, `match_features.csv` est quand même écrasé.
- **Deux valeurs par défaut.** 1450 ici, mais 1500 dans la simulation, pour la même idée (« un club sans note connue »).
- **Les buts de prolongation sont comptés ici** mais pas dans la simulation (voir [`extra_time.md`](extra_time.md)).
- **Le texte en haut du fichier est périmé.** Il cite d'anciens noms de fichiers.

---

## 11. Idées pour plus tard

- **L'avantage du terrain dans Elo.** Donner environ 50 à 70 points de plus à l'équipe à domicile pour calculer le score attendu, et 0 sur terrain neutre.
- **Compter un peu le score.** Faire grandir $K$ doucement avec la différence de buts, pour qu'un 4-0 compte plus qu'un 1-0, mais pas quatre fois plus.
- **Ramener les notes vers la moyenne chaque été.** Les effectifs changent surtout l'été. Une idée : garder 70 % de la distance de chaque club à la moyenne. Avec une moyenne de 1500, un club à 1800 commencerait la saison suivante à 1500 + 0.7 × 300 = 1710, et un club à 1350 à 1395. Le réglage est déjà dans `coefs.json` (`season_regression = 0.7`) mais aucun code ne l'utilise encore.
- **Mesurer le meilleur $K$.** Calculer les notes avec plusieurs valeurs (10, 14, 18, 20, 24, 30). Pour chacune, mesurer à quel point les scores attendus ont bien prédit les vrais résultats (la mesure de « surprise » expliquée dans [`logistic_regression.md`](logistic_regression.md), section 10). Un $K$ trop petit apprend trop lentement ; un $K$ trop grand saute après chaque résultat chanceux. Garder la valeur du milieu qui prédit le mieux.

---

## 12. Mots à connaître

| Mot | Sens |
|---|---|
| note (rating) | un nombre pour la force d'un club ; seuls les écarts entre notes ont un sens |
| score attendu | la part du point qu'un club devrait prendre, de 0 à 1 |
| surprise | résultat moins score attendu |
| $K$ | de combien un match peut faire bouger une note |
| somme nulle | ce qu'un club gagne, l'autre le perd ; le total ne change jamais |
| note de départ (seed) | la note avant le premier match |
| fuite de données | utiliser des informations d'après un événement pour décrire l'événement ; un modèle paraît alors meilleur qu'il ne l'est |

---

