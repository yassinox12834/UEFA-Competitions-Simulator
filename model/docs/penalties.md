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

In European men's football, about **75 kicks in 100** are scored in a shoot-out: 74.8 % over 14 189 shoot-out kicks (study [arXiv:2310.04797](https://arxiv.org/abs/2310.04797), 1 759 shoot-outs). So every kick goes in with a chance of 0.748.

No **pressure** rule: in the same study, a kick that could lose the shoot-out was scored about 74 % of the time, a kick that could win it about 76 %, and any other kick about 75 %. Up to 1.3.0 a fifth kick that the kicker **had** to score went in with only 0.66 (0.76 minus 0.10); the data do not support that, so it is now 0.748 like the others (`PRESSURE_DROP = 0`). Smaller samples of World Cup and Euro shoot-outs do show a large effect (62 % for a kick that avoids defeat, 92 % for a kick that wins, Geir Jordet), but those are national teams in tournaments; for UEFA club competitions the large club sample is the one that applies.

There is no difference between clubs or players: a shoot-out between a giant and a small club is the same coin.

---

## 3. Sudden death: how long can it last?

In one round of sudden death, the round is decided when exactly one of the two scores:

- A scores and B misses: 0.748 × 0.252 = 0.19;
- A misses and B scores: 0.252 × 0.748 = 0.19;
- so a round is decided about **37.7 %** of the time, and level 62.3 % of the time.

Something that happens 37.7 % of the time takes on average 1 ÷ 0.377 = **2.7 rounds** to happen. It is the same idea as waiting for a 6 with a die: on average 6 rolls.

Sudden death is perfectly fair: in a decided round, A and B win with the same chance (0.19 each), whoever kicks first.

---

## 4. Is kicking first an advantage?

No: the two clubs are treated the same way, so the club kicking first wins half the time (50.1 % over 400 000 simulated shoot-outs; the 0.1 is noise). This agrees with the two largest studies (1 759 and 7 116 shoot-outs) and with 268 UEFA club shoot-outs, which find no first-kicker advantage. Older, smaller samples had found about 60 % (129 shoot-outs) and 53 % (540 shoot-outs, not significant).

A coin still decides **who** kicks first, so each club has exactly 50 % before it is thrown, and the model no longer rewards winning the toss.

### The scores it produces

| Score | 5-4 | 4-3 | 4-2 | 5-3 | 6-5 | 3-2 | 3-1 | 4-1 | 7-6 | 8-7 |
|---|---|---|---|---|---|---|---|---|---|---|
| Chance | 19.1 % | 19.0 % | 16.7 % | 9.9 % | 7.0 % | 5.5 % | 5.3 % | 4.5 % | 4.2 % | 2.5 % |

- About 29 % of shoot-outs go to sudden death (30 % in the real sample: 530 of 1 759).
- On average 10.8 kicks are taken (10.75 in the real sample).
- A shoot-out still level after 40 rounds of sudden death is so rare (about 1 in 170 million) that it never happens in practice; the code stops it there anyway.

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

After four rounds, Arsenal 2, Atalanta 3. Arsenal's fifth kick had to be scored (chance 0.748, like every kick): scored, 3-3. Atalanta's fifth (0.748): scored, 3-4, over.

---

## 7. Try it in Python

The same rules as the real code, played 100 000 times.

```python
import random
from collections import Counter

P_SCORE = 0.748       # 74.8 kicks in 100 go in

def shootout(rng):
    a = b = 0                                     # goals of the club kicking first (a) and second (b)
    for rnd in range(5):                          # five kicks each
        left = 4 - rnd                            # kicks a still has after this one
        a += rng.random() < P_SCORE
        if a > b + left + 1 or b > a + left:      # b cannot catch up, or a cannot
            return a, b
        b += rng.random() < P_SCORE
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
club kicking first wins 0.499
5-4 0.192
4-3 0.190
4-2 0.166
5-3 0.098
6-5 0.071
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
| `P_SCORE` | 0.748 | chance that a kick goes in (74.8 % of 14 189 real shoot-out kicks) |
| `PRESSURE_DROP` | 0 | how much harder a must-score fifth kick is (0.1 up to 1.3.0; the club data show no drop) |
| `MAX_ROUNDS` | 40 | safety limit for sudden death |

The app draws the kick sheet in a tie's detail card (`interface/canvas_views.py`).

How each line works: [`code/penalties_code.md`](code/penalties_code.md).

---

## 9. What can go wrong

- **One chance for every kicker**: no goalkeepers, no good or bad takers, no difference between clubs.
- **No pressure at all, on purpose.** `PRESSURE_DROP = 0`: the 1 759-shoot-out club sample shows no drop for kicks that must be scored. Tournament samples of national teams do (62 % against 92 %), so a simulator of World Cups would want it back.
- **No link to the ratings** under "aggregate" and in the final: a shoot-out between a giant and an outsider is 50/50. That is what the data say: in 268 UEFA club shoot-outs (2000 to 2025) the club with the higher Elo rating did not win more often (about 47 % when the gap was above 100 points; Csató and Petróczy, [arXiv:2510.17641](https://arxiv.org/abs/2510.17641)).

### Known bugs

- **Fixed in 1.1.0: the text at the top of the file was out of date.** It now says the club kicking first wins 51.3 %, while each club still wins half of its shoot-outs, since a coin picks who kicks first. (Superseded: with no pressure rule, the club kicking first wins 50 %.)
- **Fixed in 1.1.0: `PRESSURE_DROP` was hidden inside a function.** It now sits next to `P_SCORE` at the top of the file.
- **Fixed in 1.1.0: the comment on `MAX_ROUNDS` was wrong.** It now says about 10⁻⁸ (0.6352⁴⁰). (Now 0.623⁴⁰, about 6 × 10⁻⁹.)
- **Fixed in 1.1.0: a confusing variable name.** The two chances in `_kick_once` are now `q_first` and `q_second`.

---

## 10. Ideas for later

- **Pressure back, for national teams**: if the simulator ever covers World Cups or Euros, lower every must-score kick to about 0.62 and raise a winning kick to about 0.92 (Jordet), which the club data do not show.
- **A link to strength**: not for club competitions, where 268 UEFA shoot-outs show no effect. It would only be worth testing for domestic cups, where one study found about 8 points of winning chance per division of difference (Krumer).

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
>Update: the pressure rule is gone, because the club data do not show it (see sections 2 and 9).
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

Dans le football européen masculin, environ **75 tirs sur 100** sont marqués pendant une séance : 74.8 % sur 14 189 tirs de séances (étude [arXiv:2310.04797](https://arxiv.org/abs/2310.04797), 1 759 séances). Chaque tir entre donc avec une chance de 0.748.

Pas de règle de **pression** : dans la même étude, un tir qui pouvait faire perdre la séance a été marqué environ 74 % du temps, un tir qui pouvait la gagner environ 76 %, et tout autre tir environ 75 %. Jusqu'à la 1.3.0, un cinquième tir que le tireur **devait** marquer entrait avec seulement 0.66 (0.76 moins 0.10) ; les données ne le confirment pas, donc il vaut maintenant 0.748 comme les autres (`PRESSURE_DROP = 0`). De plus petits échantillons de séances de Coupe du monde et d'Euro montrent bien un grand effet (62 % pour un tir qui évite la défaite, 92 % pour un tir qui gagne, Geir Jordet), mais ce sont des équipes nationales en tournoi ; pour les compétitions de clubs de l'UEFA, c'est le grand échantillon de clubs qui s'applique.

Il n'y a pas de différence entre les clubs ou les joueurs : une séance entre un géant et un petit club, c'est la même pièce.

---

## 3. La mort subite : combien de temps peut-elle durer ?

Dans un tour de mort subite, le tour est décidé quand exactement l'un des deux marque :

- A marque et B rate : 0.748 × 0.252 = 0.19 ;
- A rate et B marque : 0.252 × 0.748 = 0.19 ;
- un tour est donc décidé environ **37.7 %** du temps, et à égalité 62.3 % du temps.

Une chose qui arrive 37.7 % du temps met en moyenne 1 ÷ 0.377 = **2.7 tours** à arriver. C'est la même idée qu'attendre un 6 avec un dé : 6 lancers en moyenne.

La mort subite est parfaitement équitable : dans un tour décidé, A et B gagnent avec la même chance (0.19 chacun), quel que soit celui qui tire en premier.

---

## 4. Tirer en premier, est-ce un avantage ?

Non : les deux clubs sont traités pareil, donc le club qui tire en premier gagne une fois sur deux (50.1 % sur 400 000 séances simulées ; le 0.1 est du bruit). Cela concorde avec les deux plus grandes études (1 759 et 7 116 séances) et avec 268 séances de clubs de l'UEFA, qui ne trouvent aucun avantage pour le premier tireur. Des échantillons plus anciens et plus petits avaient trouvé environ 60 % (129 séances) et 53 % (540 séances, non significatif).

Une pièce décide toujours **qui** tire en premier, donc chaque club a exactement 50 % avant le lancer, et le modèle ne récompense plus le tirage au sort.

### Les scores obtenus

| Score | 5-4 | 4-3 | 4-2 | 5-3 | 6-5 | 3-2 | 3-1 | 4-1 | 7-6 | 8-7 |
|---|---|---|---|---|---|---|---|---|---|---|
| Chance | 19.1 % | 19.0 % | 16.7 % | 9.9 % | 7.0 % | 5.5 % | 5.3 % | 4.5 % | 4.2 % | 2.5 % |

- Environ 29 % des séances vont en mort subite (30 % dans l'échantillon réel : 530 sur 1 759).
- En moyenne 10.8 tirs sont tirés (10.75 dans l'échantillon réel).
- Une séance encore à égalité après 40 tours de mort subite est si rare (environ 1 sur 170 millions) qu'elle n'arrive jamais en pratique ; le code l'arrête là de toute façon.

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

Après quatre tours, Arsenal 2, Atalanta 3. Le cinquième tir d'Arsenal devait être marqué (chance 0.748, comme chaque tir) : marqué, 3-3. Le cinquième de l'Atalanta (0.748) : marqué, 3-4, fini.

---

## 7. À essayer en Python

Les mêmes règles que le vrai code, jouées 100 000 fois.

```python
import random
from collections import Counter

P_SCORE = 0.748       # 74.8 tirs sur 100 entrent

def shootout(rng):
    a = b = 0                                     # buts du club qui tire en premier (a) et en second (b)
    for rnd in range(5):                          # cinq tirs chacun
        left = 4 - rnd                            # tirs qu'il reste à a après celui-ci
        a += rng.random() < P_SCORE
        if a > b + left + 1 or b > a + left:      # b ne peut plus rattraper, ou a ne peut plus
            return a, b
        b += rng.random() < P_SCORE
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
club kicking first wins 0.499
5-4 0.192
4-3 0.190
4-2 0.166
5-3 0.098
6-5 0.071
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
| `P_SCORE` | 0.748 | chance qu'un tir entre (74.8 % de 14 189 vrais tirs de séances) |
| `PRESSURE_DROP` | 0 | à quel point un cinquième tir obligatoire est plus dur (0.1 jusqu'à la 1.3.0 ; les données de clubs ne montrent aucune baisse) |
| `MAX_ROUNDS` | 40 | limite de sécurité pour la mort subite |

L'appli dessine la feuille de tirs dans la fiche détaillée d'une confrontation (`interface/canvas_views.py`).

Comment marche chaque ligne : [`code/penalties_code.md`](code/penalties_code.md).

---

## 9. Ce qui peut mal tourner

- **Une seule chance pour chaque tireur** : pas de gardiens, pas de bons ou mauvais tireurs, pas de différence entre clubs.
- **Aucune pression, volontairement.** `PRESSURE_DROP = 0` : l'échantillon de clubs de 1 759 séances ne montre aucune baisse pour les tirs obligatoires. Les échantillons de tournois d'équipes nationales en montrent une (62 % contre 92 %), donc un simulateur de Coupes du monde voudrait la remettre.
- **Pas de lien avec les notes** avec « aggregate » et en finale : une séance entre un géant et un outsider, c'est 50/50. C'est ce que disent les données : sur 268 séances de clubs de l'UEFA (2000 à 2025), le club le mieux classé en Elo n'a pas gagné plus souvent (environ 47 % quand l'écart dépassait 100 points ; Csató et Petróczy, [arXiv:2510.17641](https://arxiv.org/abs/2510.17641)).

### Bugs connus

- **Corrigé en 1.1.0 : le texte en haut du fichier était périmé.** Il dit maintenant que le club qui tire en premier gagne 51.3 %, tandis que chaque club gagne toujours la moitié de ses séances, puisqu'une pièce décide qui tire en premier. (Remplacé : sans règle de pression, le club qui tire en premier gagne 50 %.)
- **Corrigé en 1.1.0 : `PRESSURE_DROP` était caché dans une fonction.** Il est maintenant à côté de `P_SCORE`, en haut du fichier.
- **Corrigé en 1.1.0 : le commentaire de `MAX_ROUNDS` était faux.** Il dit maintenant environ 10⁻⁸ (0.6352⁴⁰). (Maintenant 0.623⁴⁰, environ 6 × 10⁻⁹.)
- **Corrigé en 1.1.0 : un nom de variable trompeur.** Les deux chances de `_kick_once` s'appellent maintenant `q_first` et `q_second`.

---

## 10. Idées pour plus tard

- **La pression de retour, pour les équipes nationales** : si le simulateur couvre un jour des Coupes du monde ou des Euros, baisser chaque tir obligatoire à environ 0.62 et monter un tir gagnant à environ 0.92 (Jordet), ce que les données de clubs ne montrent pas.
- **Un lien avec la force** : pas pour les compétitions de clubs, où 268 séances de l'UEFA ne montrent aucun effet. Cela ne vaudrait le coup d'être testé que pour les coupes nationales, où une étude a trouvé environ 8 points de chance de victoire par division d'écart (Krumer).

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
> Mise à jour : la règle de pression a disparu, car les données de clubs ne la montrent pas (voir les sections 2 et 9).