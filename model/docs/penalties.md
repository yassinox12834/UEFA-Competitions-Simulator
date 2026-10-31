# Penalty shoot-outs

> When a knockout tie is still level at the end, it goes to penalties. This part plays the shoot-out kick by kick, with the real rules, so every shoot-out has a real score (4-3, 5-4 after sudden death, ...) and a kick sheet.

*Version française : [plus bas](#les-tirs-au-but).*

## In short

- **What goes in:** the two clubs, and sometimes the club that must win (see section 5).
- **What comes out:** the winner, the score, and the sheet of every kick: `o` scored, `x` missed, `-` not taken.
- **Where it is used:** at the end of a knockout tie still level after extra time ([`extra_time.md`](extra_time.md)), and for level ties under the "legs" method ([`knockout.md`](knockout.md)).
- **Code:** `model/penalties.py`. Line-by-line walkthrough: [`code/penalties_code.md`](code/penalties_code.md).

---

## 1. The rules

These are the official rules (Law 10 of the game):

1. A coin decides which club kicks first. Then the clubs take turns: A, B, A, B, ...
2. Five kicks each. The shoot-out **stops early** as soon as one club cannot catch up, even by scoring all its remaining kicks.
3. Still level after five each: **sudden death**. One kick each, again and again, until one scores and the other misses in the same round.

**Example of an early stop.** After four rounds, A leads 3-2. A scores its fifth kick: 4-2. B has only one kick left, so B can reach 3 at most. It is over: 4-2, and B's fifth kick is never taken (the sheet shows `-`).

---

## 2. How likely is a goal?

In men's club football, about **76 kicks in 100** are scored. So every kick goes in with a chance of 0.76.

One exception: **pressure**. A fifth kick that the kicker **must** score to stay alive (his club trails by one goal) goes in with a chance of only 0.66 (0.76 minus 0.10).

There is no difference between clubs or players: a shoot-out between a giant and a small club is the same coin with a memory of the score.

---

## 3. Sudden death: how long can it last?

In one round of sudden death, the round is decided when exactly one of the two scores:

- A scores and B misses: 0.76 × 0.24 = 0.18;
- A misses and B scores: 0.24 × 0.76 = 0.18;
- so a round is decided about **36.5 %** of the time, and level 63.5 % of the time.

Something that happens 36.5 % of the time takes on average 1 ÷ 0.365 = **2.7 rounds** to happen. It is the same idea as waiting for a 6 with a die: on average 6 rolls.

Sudden death is perfectly fair: in a decided round, A and B win with the same chance (0.18 each), whoever kicks first.

---

## 4. Is kicking first an advantage?

Without the pressure rule, the club kicking first would win exactly half the time.

With the pressure rule, it wins **51.3 %**. Why? The club kicking **second** more often finds itself taking a must-score fifth kick (in about 31 % of shoot-outs, against 23 % for the club kicking first), so the pressure hurts it more.

But **who** kicks first is decided by a coin, so before the coin is thrown each club still has exactly 50 %. Winning the coin toss is worth about 1.3 percentage points.

### The scores it produces

| Score | 4-3 | 5-4 | 4-2 | 5-3 | 6-5 | 3-2 | 3-1 | 4-1 | 7-6 | 8-7 |
|---|---|---|---|---|---|---|---|---|---|---|
| Chance | 20.3 % | 18.8 % | 16.4 % | 10.7 % | 6.4 % | 6.0 % | 4.7 % | 4.4 % | 3.9 % | 2.4 % |

- About 26 % of shoot-outs go to sudden death.
- On average 10.7 kicks are taken.
- A shoot-out still level after 40 rounds of sudden death is so rare (about 1 in 300 million) that it never happens in practice; the code stops it there anyway.

In the real data (41 usable shoot-outs), the most common scores were also 4-2, 4-3 and 5-4.

---

## 5. A shoot-out with a known winner

Under the "legs" method, when a tie is level, the winner is chosen **first**, with the clubs' ratings ([`knockout.md`](knockout.md), section 3). The shoot-out must then look like a real one that this club won.

The trick: play free shoot-outs and keep the first one that the chosen club wins. Like rolling a die until it shows an even number, when you need "a random even number". This is called **rejection sampling**.

Each shoot-out is won by the chosen club half the time, so it takes 2 tries on average, and more than 5 tries only about 3 times in 100.

---

## 6. A real example

Arsenal v Atalanta, quarter-final, method "legs". One win each, so level. With the ratings after both legs, Arsenal's chance was 0.586. The random number was 0.6257, above 0.586, so **Atalanta** were picked. The shoot-out created for them:

```
penalties Arsenal 3-4 Atalanta  (Arsenal kicked first)
   Arsenal   o o x x o   = 3
   Atalanta  x o o o o   = 4
```

After four rounds, Arsenal 2, Atalanta 3. Arsenal's fifth kick was a must-score (chance 0.66): scored, 3-3. Atalanta's fifth (no pressure, 0.76): scored, 3-4, over.

---

## 7. Try it in Python

The same rules as the real code, played 100 000 times.

```python
import random
from collections import Counter

P_SCORE = 0.76        # 76 kicks in 100 go in
PRESSURE = 0.10       # a fifth kick that MUST go in is harder: 0.66

def shootout(rng):
    a = b = 0                                     # goals of the club kicking first (a) and second (b)
    for rnd in range(5):                          # five kicks each
        left = 4 - rnd                            # kicks a still has after this one
        must = rnd == 4 and a + 1 == b            # a's last kick: miss it and a loses
        a += rng.random() < (P_SCORE - PRESSURE if must else P_SCORE)
        if a > b + left + 1 or b > a + left:      # b cannot catch up, or a cannot
            return a, b
        must = rnd == 4 and b + 1 == a
        b += rng.random() < (P_SCORE - PRESSURE if must else P_SCORE)
        if a > b + left or b > a + left:
            return a, b
    while True:                                   # sudden death: one kick each
        sa, sb = rng.random() < P_SCORE, rng.random() < P_SCORE
        a, b = a + sa, b + sb
        if sa != sb:
            return a, b

rng = random.Random(3)
N = 100_000
results = [shootout(rng) for _ in range(N)]
first_wins = sum(a > b for a, b in results)
print(f"club kicking first wins {first_wins / N:.3f}")
scores = Counter(f"{max(r)}-{min(r)}" for r in results)
for score, n in scores.most_common(5):
    print(score, f"{n / N:.3f}")
```

Output:

```
club kicking first wins 0.512
4-3 0.203
5-4 0.187
4-2 0.164
5-3 0.107
6-5 0.064
```

`a += (True or False)` works because in Python `True` counts as 1 and `False` as 0: adding the result of "did it go in?" counts the goals.

---

## 8. What the code uses

### Python modules

None. The file only uses Python itself; the random numbers come from the season's random generator, passed in by the caller.

### Functions and classes in `model/penalties.py`

| Name | In one line |
|---|---|
| `kick` | a free shoot-out: a coin for the order, then the kicks |
| `kick_for` | a shoot-out that a chosen club wins (section 5) |
| `_kick_once` | plays the kicks: five rounds with early stop, then sudden death |
| `Shootout` | the record of one shoot-out: who kicked first, goals, every kick, winner |
| `Shootout.score_for` | the score seen from one club: (its goals, the other's) |
| `Shootout.sheet` | the two rows of the kick sheet, `o x -` |

| Setting | Value | Meaning |
|---|---|---|
| `P_SCORE` | 0.76 | chance that a normal kick goes in |
| `PRESSURE_DROP` | 0.1 | how much harder a must-score fifth kick is |
| `MAX_ROUNDS` | 40 | safety limit for sudden death |

The app draws the kick sheet in a tie's detail card (`interface/canvas_views.py`).

How each line works: [`code/penalties_code.md`](code/penalties_code.md).

---

## 9. What can go wrong

- **One chance for every kicker**: no goalkeepers, no good or bad takers, no difference between clubs.
- **Pressure only on the fifth kick.** In sudden death, many kicks are also "score or lose", but they keep 0.76.
- **No link to the ratings** under "aggregate" and in the final: a shoot-out between a giant and an outsider is 50/50.

### Known bugs

- **Fixed in 1.1.0: the text at the top of the file was out of date.** It now says the club kicking first wins 51.3 %, while each club still wins half of its shoot-outs, since a coin picks who kicks first.
- **Fixed in 1.1.0: `PRESSURE_DROP` was hidden inside a function.** It now sits next to `P_SCORE` at the top of the file.
- **Fixed in 1.1.0: the comment on `MAX_ROUNDS` was wrong.** It now says about 10⁻⁸ (0.6352⁴⁰).
- **Fixed in 1.1.0: a confusing variable name.** The two chances in `_kick_once` are now `q_first` and `q_second`.

---

## 10. Ideas for later

- **Pressure on every must-score kick**, including in sudden death, then measure again who wins more often.
- **A small link to strength**: give stronger clubs a slightly higher chance, for example 0.80 instead of 0.76 for a club much stronger. Small, because real shoot-outs are close to a lottery.

---

## 11. Words to know

| Word | Meaning |
|---|---|
| shoot-out | the penalties that decide a level knockout tie |
| ABAB | the kicking order: A, B, A, B, ...; a coin picks A |
| sudden death | after five level rounds: one kick each until exactly one scores |
| must-score kick | a kick that ends the shoot-out against the kicker's club if missed |
| rejection sampling | getting a random result "with a condition" by drawing freely and throwing away the draws that do not meet it |
| kick sheet | the list of kicks of each club: `o` scored, `x` missed, `-` not taken |

---

## Notes

>I was slightly doubtful about the pressure on the fifth shooter in a decisive shoot-out. 
>Let me know if you want us to keep it.
>Perhaps I should create a new feature which indicates how tense and crucial the match is.
---
---

# Les tirs au but

> Quand une confrontation à élimination directe reste à égalité à la fin, on passe aux tirs au but. Cette partie joue la séance tir par tir, avec les vraies règles, pour que chaque séance ait un vrai score (4-3, 5-4 après la mort subite, ...) et une feuille de tirs.

## En bref

- **Ce qui entre :** les deux clubs, et parfois le club qui doit gagner (voir section 5).
- **Ce qui sort :** le vainqueur, le score, et la feuille de chaque tir : `o` marqué, `x` raté, `-` pas tiré.
- **Où c'est utilisé :** à la fin d'une confrontation encore à égalité après la prolongation ([`extra_time.md`](extra_time.md)), et pour les égalités avec la méthode « legs » ([`knockout.md`](knockout.md)).
- **Code :** `model/penalties.py`. Explication ligne par ligne : [`code/penalties_code.md`](code/penalties_code.md).

---

## 1. Les règles

Ce sont les règles officielles (loi 10 du jeu) :

1. Une pièce décide quel club tire en premier. Ensuite les clubs tirent à tour de rôle : A, B, A, B, ...
2. Cinq tirs chacun. La séance **s'arrête tôt** dès qu'un club ne peut plus rattraper l'autre, même en marquant tous ses tirs restants.
3. Toujours à égalité après cinq tirs chacun : **mort subite**. Un tir chacun, encore et encore, jusqu'à ce que l'un marque et l'autre rate dans le même tour.

**Exemple d'arrêt anticipé.** Après quatre tours, A mène 3-2. A marque son cinquième tir : 4-2. B n'a plus qu'un tir, donc B peut atteindre 3 au mieux. C'est fini : 4-2, et le cinquième tir de B n'est jamais tiré (la feuille affiche `-`).

---

## 2. Quelle chance de marquer ?

Dans le football de clubs masculin, environ **76 tirs sur 100** sont marqués. Chaque tir entre donc avec une chance de 0.76.

Une exception : la **pression**. Un cinquième tir que le tireur **doit** marquer pour rester en vie (son club a un but de retard) entre avec une chance de seulement 0.66 (0.76 moins 0.10).

Il n'y a pas de différence entre les clubs ou les joueurs : une séance entre un géant et un petit club, c'est la même pièce qui se souvient du score.

---

## 3. La mort subite : combien de temps peut-elle durer ?

Dans un tour de mort subite, le tour est décidé quand exactement l'un des deux marque :

- A marque et B rate : 0.76 × 0.24 = 0.18 ;
- A rate et B marque : 0.24 × 0.76 = 0.18 ;
- un tour est donc décidé environ **36.5 %** du temps, et à égalité 63.5 % du temps.

Une chose qui arrive 36.5 % du temps met en moyenne 1 ÷ 0.365 = **2.7 tours** à arriver. C'est la même idée qu'attendre un 6 avec un dé : 6 lancers en moyenne.

La mort subite est parfaitement équitable : dans un tour décidé, A et B gagnent avec la même chance (0.18 chacun), quel que soit celui qui tire en premier.

---

## 4. Tirer en premier, est-ce un avantage ?

Sans la règle de pression, le club qui tire en premier gagnerait exactement une fois sur deux.

Avec la règle de pression, il gagne **51.3 %**. Pourquoi ? Le club qui tire en **second** se retrouve plus souvent à tirer un cinquième tir obligatoire (dans environ 31 % des séances, contre 23 % pour le club qui tire en premier), donc la pression le gêne davantage.

Mais **qui** tire en premier est décidé par une pièce, donc avant le lancer de la pièce chaque club a toujours exactement 50 %. Gagner le tirage au sort vaut environ 1.3 point de pourcentage.

### Les scores obtenus

| Score | 4-3 | 5-4 | 4-2 | 5-3 | 6-5 | 3-2 | 3-1 | 4-1 | 7-6 | 8-7 |
|---|---|---|---|---|---|---|---|---|---|---|
| Chance | 20.3 % | 18.8 % | 16.4 % | 10.7 % | 6.4 % | 6.0 % | 4.7 % | 4.4 % | 3.9 % | 2.4 % |

- Environ 26 % des séances vont en mort subite.
- En moyenne 10.7 tirs sont tirés.
- Une séance encore à égalité après 40 tours de mort subite est si rare (environ 1 sur 300 millions) qu'elle n'arrive jamais en pratique ; le code l'arrête là de toute façon.

Dans les vraies données (41 séances utilisables), les scores les plus fréquents étaient aussi 4-2, 4-3 et 5-4.

---

## 5. Une séance dont on connaît le vainqueur

Avec la méthode « legs », quand une confrontation est à égalité, le vainqueur est choisi **d'abord**, avec les notes des clubs ([`knockout.md`](knockout.md), section 3). La séance doit ensuite ressembler à une vraie séance gagnée par ce club.

L'astuce : jouer des séances libres et garder la première que le club choisi gagne. Comme lancer un dé jusqu'à obtenir un nombre pair, quand on veut « un nombre pair au hasard ». On appelle cela l'**échantillonnage par rejet**.

Chaque séance est gagnée par le club choisi une fois sur deux, donc il faut 2 essais en moyenne, et plus de 5 essais seulement environ 3 fois sur 100.

---

## 6. Un vrai exemple

Arsenal-Atalanta, quart de finale, méthode « legs ». Une victoire chacun, donc égalité. Avec les notes après les deux matchs, la chance d'Arsenal valait 0.586. Le nombre au hasard valait 0.6257, au-dessus de 0.586, donc l'**Atalanta** a été choisie. La séance créée pour elle :

```
penalties Arsenal 3-4 Atalanta  (Arsenal kicked first)
   Arsenal   o o x x o   = 3
   Atalanta  x o o o o   = 4
```

Après quatre tours, Arsenal 2, Atalanta 3. Le cinquième tir d'Arsenal était obligatoire (chance 0.66) : marqué, 3-3. Le cinquième de l'Atalanta (pas de pression, 0.76) : marqué, 3-4, fini.

---

## 7. À essayer en Python

Les mêmes règles que le vrai code, jouées 100 000 fois.

```python
import random
from collections import Counter

P_SCORE = 0.76        # 76 tirs sur 100 entrent
PRESSURE = 0.10       # un cinquième tir OBLIGATOIRE est plus dur : 0.66

def shootout(rng):
    a = b = 0                                     # buts du club qui tire en premier (a) et en second (b)
    for rnd in range(5):                          # cinq tirs chacun
        left = 4 - rnd                            # tirs qu'il reste à a après celui-ci
        must = rnd == 4 and a + 1 == b            # dernier tir de a : s'il le rate, a perd
        a += rng.random() < (P_SCORE - PRESSURE if must else P_SCORE)
        if a > b + left + 1 or b > a + left:      # b ne peut plus rattraper, ou a ne peut plus
            return a, b
        must = rnd == 4 and b + 1 == a
        b += rng.random() < (P_SCORE - PRESSURE if must else P_SCORE)
        if a > b + left or b > a + left:
            return a, b
    while True:                                   # mort subite : un tir chacun
        sa, sb = rng.random() < P_SCORE, rng.random() < P_SCORE
        a, b = a + sa, b + sb
        if sa != sb:
            return a, b

rng = random.Random(3)
N = 100_000
results = [shootout(rng) for _ in range(N)]
first_wins = sum(a > b for a, b in results)
print(f"club kicking first wins {first_wins / N:.3f}")
scores = Counter(f"{max(r)}-{min(r)}" for r in results)
for score, n in scores.most_common(5):
    print(score, f"{n / N:.3f}")
```

Résultat :

```
club kicking first wins 0.512
4-3 0.203
5-4 0.187
4-2 0.164
5-3 0.107
6-5 0.064
```

`a += (True ou False)` marche car en Python `True` compte comme 1 et `False` comme 0 : ajouter le résultat de « est-ce entré ? » compte les buts.

---

## 8. Ce que le code utilise

### Modules Python

Aucun. Le fichier n'utilise que Python lui-même ; les nombres au hasard viennent du générateur de la saison, fourni par l'appelant.

### Fonctions et classes de `model/penalties.py`

| Nom | En une ligne |
|---|---|
| `kick` | une séance libre : une pièce pour l'ordre, puis les tirs |
| `kick_for` | une séance gagnée par un club choisi (section 5) |
| `_kick_once` | joue les tirs : cinq tours avec arrêt anticipé, puis mort subite |
| `Shootout` | la fiche d'une séance : qui a tiré en premier, buts, chaque tir, vainqueur |
| `Shootout.score_for` | le score vu par un club : (ses buts, ceux de l'autre) |
| `Shootout.sheet` | les deux lignes de la feuille de tirs, `o x -` |

| Réglage | Valeur | Sens |
|---|---|---|
| `P_SCORE` | 0.76 | chance qu'un tir normal entre |
| `PRESSURE_DROP` | 0.1 | à quel point un cinquième tir obligatoire est plus dur |
| `MAX_ROUNDS` | 40 | limite de sécurité pour la mort subite |

L'appli dessine la feuille de tirs dans la fiche détaillée d'une confrontation (`interface/canvas_views.py`).

Comment marche chaque ligne : [`code/penalties_code.md`](code/penalties_code.md).

---

## 9. Ce qui peut mal tourner

- **Une seule chance pour chaque tireur** : pas de gardiens, pas de bons ou mauvais tireurs, pas de différence entre clubs.
- **Pression seulement sur le cinquième tir.** En mort subite, beaucoup de tirs sont aussi « marquer ou perdre », mais ils gardent 0.76.
- **Pas de lien avec les notes** avec « aggregate » et en finale : une séance entre un géant et un outsider, c'est 50/50.

### Bugs connus

- **Corrigé en 1.1.0 : le texte en haut du fichier était périmé.** Il dit maintenant que le club qui tire en premier gagne 51.3 %, tandis que chaque club gagne toujours la moitié de ses séances, puisqu'une pièce décide qui tire en premier.
- **Corrigé en 1.1.0 : `PRESSURE_DROP` était caché dans une fonction.** Il est maintenant à côté de `P_SCORE`, en haut du fichier.
- **Corrigé en 1.1.0 : le commentaire de `MAX_ROUNDS` était faux.** Il dit maintenant environ 10⁻⁸ (0.6352⁴⁰).
- **Corrigé en 1.1.0 : un nom de variable trompeur.** Les deux chances de `_kick_once` s'appellent maintenant `q_first` et `q_second`.

---

## 10. Idées pour plus tard

- **La pression sur chaque tir obligatoire**, y compris en mort subite, puis remesurer qui gagne le plus souvent.
- **Un petit lien avec la force** : donner aux clubs plus forts une chance un peu plus haute, par exemple 0.80 au lieu de 0.76 pour un club bien plus fort. Petit, car les vraies séances ressemblent beaucoup à une loterie.

---

## 11. Mots à connaître

| Mot | Sens |
|---|---|
| tirs au but | la séance qui décide une confrontation à égalité |
| ABAB | l'ordre de tir : A, B, A, B, ... ; une pièce choisit A |
| mort subite | après cinq tours à égalité : un tir chacun jusqu'à ce qu'exactement un marque |
| tir obligatoire | un tir qui, s'il est raté, termine la séance contre le club du tireur |
| échantillonnage par rejet | obtenir un résultat au hasard « avec une condition » en tirant librement et en jetant les tirages qui ne la respectent pas |
| feuille de tirs | la liste des tirs de chaque club : `o` marqué, `x` raté, `-` pas tiré |

---

## Remarques

> J'avais quelques doutes quant à la pression exercée sur le cinquième tireur lors d'une séance de tirs décisive.
> Dis-moi si tu veux qu'on garde ça.
> Je devrais peut-être créer une nouvelle fonctionnalité qui indique à quel point le match est tendu et crucial.