# The draw: who plays whom

> Before any match can be played, every club needs its list of opponents. This part makes that list for the Champions League, the Europa League or the Conference League, following all of UEFA's rules, and checks the result again before handing it over.

*Version française : [plus bas](#le-tirage--qui-joue-contre-qui).*

## In short

- **What goes in:** the pots (four lists of nine clubs, or six lists of six for the Conference League), each club's country, and optionally some "forbidden home matches" chosen by the user.
- **What comes out:** every match of the league phase, written as "home club, away club": 144 matches (108 for the Conference League).
- **Where it is used:** the draw screen of the app animates it; then the matchday planner ([`matchdays.md`](matchdays.md)) decides on which day each match is played.
- **Code:** `model/draw_ucl.py` (Champions League and Europa League) and `model/draw_uecl.py` (Conference League). Line-by-line walkthrough: [`code/draw_code.md`](code/draw_code.md).

---

## 1. The rules of the draw

Since 2024/25, the league phase is one big table of 36 clubs. The clubs are split into **pots** by strength (pot 1 holds the strongest).

**Champions League and Europa League:** 4 pots of 9 clubs. Each club plays **8 matches**:

- 2 opponents from each pot (from its own pot too);
- of those 2, one at home and one away;
- so 4 home matches and 4 away matches.

The rules every draw must respect:

| Rule | In words |
|---|---|
| 1 | every club plays exactly 8 matches |
| 2 | one home and one away match against each pot |
| 3 | no opponent from the same country (an English club never meets another English club) |
| 4 | at most 2 opponents from any one country |
| 5 | no club is met twice |
| 6 | if A hosts B, then B visits A: both lists agree |
| 7 | the user's bans: if the user says "Genk must not host Brann", Genk never hosts Brann (Brann hosting Genk stays allowed) |

How many matches? 36 clubs × 8 matches = 288, but every match is counted twice (once by each club), so there are 288 ÷ 2 = **144 matches**.

**Conference League:** 6 pots of 6 clubs, **6 matches** per club, one opponent from each pot. The pots are paired (1 with 2, 3 with 4, 5 with 6): a club plays one pot of each pair at home and the other away, which gives exactly 3 home and 3 away matches. 36 × 6 ÷ 2 = **108 matches**.

---

## 2. Why it is hard

It sounds easy: pick opponents at random until everyone has 8. But the rules fight each other.

Imagine you have already drawn most matches. Barcelona still need one opponent from pot 2, away. The only pot-2 clubs left that still need a pot-1 home match are Atlético Madrid (Spanish, so forbidden) and a club Barcelona already play. **Dead end.** Every earlier choice now has to be questioned.

And trying every possible draw is out of the question. A rough count gives about a 1 followed by **89 zeros** possible ways to pair the clubs. Even a computer checking a billion draws per second would need far longer than the age of the universe.

So the program needs a smarter method.

---

## 3. How it works: like solving a sudoku

The method is the one many people use for a sudoku.

### Step 1: list every game still to draw

At the start, each club needs one home game and one away game against each pot. Each of those needs is called a **slot**. For example:

- "Liverpool still needs to **travel to** a club from **pot 2**";
- "Juventus still needs to **host** a club from **pot 1**".

36 clubs × 4 pots × 2 (home and away) = **288 slots**. Each match fills two slots at once: one for each club.

### Step 2: fill the hardest slot first

For every open slot, the program counts how many clubs could legally fill it (right pot, different country, not met yet, country limit not reached, not banned by the user, and the other club also still needs this game).

It then works on the slot with the **fewest** possible clubs. In a sudoku, you also start with the box that has only one possible number: it costs nothing, and if a box has zero possibilities, you learn at once that something went wrong earlier.

This rule has a name: **"most constrained first"** (in computer science, MRV, for "minimum remaining values").

### Step 3: try a club, go on, undo if stuck

The program shuffles the possible clubs (this is where the randomness of the draw comes from), takes the first one, writes the match, and moves on to the next hardest slot.

If later it reaches a slot with **no possible club**, it goes back: it removes the last match it wrote and tries the next club instead. If no club works there either, it goes back one more step, and so on. This is called **backtracking**.

### Step 4: start again if it takes too long

A bad choice very early can trap the search for a very long time. So each attempt has a limit of 200 000 steps. If it is reached, the program throws everything away and starts a new draw from scratch, with new random choices. It allows up to 50 fresh starts.

In practice, without user bans, a draw almost never needs to go back: on 100 test draws, all 100 finished at the first attempt, in about 144 steps (one per match).

### Step 5: check everything again

When the draw is complete, a separate checker reads the finished list and checks all 7 rules from scratch. It does not trust anything the search wrote along the way. If a bug had slipped into the search, the checker would catch it and stop with a clear message, instead of handing over a wrong draw.

---

## 4. A full example by hand

Six clubs, two pots of three. Each club plays one home and one away game against each pot, so 4 matches each and 12 matches in total. Lyon and Lens are both French, so they can never meet.

| Pot 1 | Country | Pot 2 | Country |
|---|---|---|---|
| Lyon | France | Lens | France |
| Sevilla | Spain | Mainz | Germany |
| Napoli | Italy | Braga | Portugal |

The first three steps of the real program:

| Step | Hardest slot | Possible clubs | Choice |
|---|---|---|---|
| 1 | Braga still needs to travel to a pot-2 club | Mainz, Lens (2 choices; no slot has fewer) | Mainz hosts Braga |
| 2 | Braga still needs to host a pot-2 club | only Lens (Braga already play Mainz) | Braga hosts Lens |
| 3 | Lens still needs to host a pot-2 club | only Mainz | Lens hosts Mainz |

Steps 2 and 3 had only one possible club: they were "forced", exactly like a sudoku box with one possible number. The whole draw finished in 12 steps, without ever going back:

```
Inside pot 1:  Lyon hosts Sevilla, Sevilla hosts Napoli, Napoli hosts Lyon
Inside pot 2:  Mainz hosts Braga, Braga hosts Lens, Lens hosts Mainz

Pot 1 hosts pot 2        Pot 2 hosts pot 1
Lyon    hosts Braga      Lens  hosts Sevilla
Sevilla hosts Mainz      Mainz hosts Lyon
Napoli  hosts Lens       Braga hosts Napoli
```

Check: every club hosts 2 and visits 2, plays each pot once at home and once away, and Lyon never meets Lens.

---

## 5. Try it in Python

A small version of the same method for the six clubs above: slots, hardest first, try and undo.

```python
import random

POTS = [["Lyon", "Sevilla", "Napoli"], ["Lens", "Mainz", "Braga"]]
COUNTRY = {"Lyon": "France", "Sevilla": "Spain", "Napoli": "Italy",
           "Lens": "France", "Mainz": "Germany", "Braga": "Portugal"}
POT_OF = {club: p for p, pot in enumerate(POTS) for club in pot}

# A "slot" is one game a club still needs: (club, pot of the opponent, at home?)
slots = {(club, p, home) for club in COUNTRY for p in range(len(POTS)) for home in (True, False)}
played = {club: set() for club in COUNTRY}
fixtures = []                      # (home club, away club)

def options(slot):
    club, p, home = slot
    good = []
    for other in POTS[p]:
        if other == club or COUNTRY[other] == COUNTRY[club]:
            continue                                   # not itself, not same country
        if other in played[club]:
            continue                                   # no rematch
        if (other, POT_OF[club], not home) not in slots:
            continue                                   # the other club must still need this game
        good.append(other)
    return good

def fill(rng):
    if not slots:
        return True                                    # every game is drawn
    slot = min(sorted(slots), key=lambda s: len(options(s)))   # hardest slot first
    club, p, home = slot
    choices = options(slot)
    rng.shuffle(choices)
    for other in choices:
        mirror = (other, POT_OF[club], not home)       # the same game, seen by the other club
        slots.discard(slot); slots.discard(mirror)
        played[club].add(other); played[other].add(club)
        fixtures.append((club, other) if home else (other, club))
        if fill(rng):
            return True
        fixtures.pop()                                 # dead end: undo and try the next club
        played[club].discard(other); played[other].discard(club)
        slots.add(slot); slots.add(mirror)
    return False

fill(random.Random(1))
for home, away in sorted(fixtures):
    print(f"{home} hosts {away}")
print(len(fixtures), "games")
```

Output:

```
Braga hosts Lens
Braga hosts Napoli
Lens hosts Mainz
Lens hosts Sevilla
Lyon hosts Braga
Lyon hosts Sevilla
Mainz hosts Braga
Mainz hosts Lyon
Napoli hosts Lens
Napoli hosts Lyon
Sevilla hosts Mainz
Sevilla hosts Napoli
12 games
```

Change `random.Random(1)` to `random.Random(2)`: you get another valid draw. The same number always gives the same draw; this number is called the **seed**.

---

## 6. The Conference League version

The Conference League has another shape, so it has its own file, `model/draw_uecl.py`. The idea is the same (slots, hardest first, undo, restart, check); what changes:

| | Champions League, Europa League | Conference League |
|---|---|---|
| Pots | 4 of 9 | 6 of 6 |
| Games against each pot | 2: one home, one away | 1: home **or** away, and the direction is part of the draw |
| Home / away | 4 / 4 | 3 / 3, thanks to the paired pots |
| When a match is drawn | 2 slots close (one per club) | up to 6 slots close: both directions for both clubs against that pot, plus the paired pot's slot that must now go the other way |

The two files repeat several parts (reading the countries, printing, checking). A change made in one is easy to forget in the other; moving the shared parts into one file would be cleaner.

---

## 7. What the code uses

### Python modules

All come with Python; nothing needs to be installed.

| Module | What it does here |
|---|---|
| `random` | shuffles the possible clubs; `random.Random(seed)` gives a private random generator, so the same seed always gives the same draw |
| `csv` | reads each club's country from `data/processed/countries_filled_25.csv` |
| `collections` (`defaultdict`) | counts opponents per country, starting at 0 for a country never seen |
| `functools` (`lru_cache`) | remembers the country file after the first read, so it is not read again for every draw |
| `itertools` (`chain`) | walks through a club's home and away opponents as one list |
| `pathlib` | builds the path to the country file |
| `time` | measures how long a draw takes (only in the demo at the bottom of the file) |

It also uses `model/names.py` ([`names.md`](names.md)) when a club's name is spelt differently in the pots and in the country file.

### Functions in `model/draw_ucl.py`

| Function | In one line |
|---|---|
| `generate_draw` | the entry point: prepares everything, runs the draw, checks it, returns the result |
| `draw` | runs up to 50 attempts (step 4) |
| `fill` | the search itself: hardest slot first, try, undo (steps 2 and 3) |
| `options` | lists the clubs that can legally fill one slot |
| `link`, `unlink` | write a match into both clubs' lists, and remove it again |
| `verify` | the final check of all 7 rules (step 5) |
| `build_teams` | prepares an empty record for every club |
| `load_countries` | reads each club's country |
| `fixtures` | returns the finished draw as a list of (home, away) matches |
| `show` | prints the draw pot by pot |

`model/draw_uecl.py` has the same functions, plus `paired_pot` (which pot goes with which) and `faced_from` (how many opponents a club already has from one country). The app reaches both files through `interface/draw_engine.py`, which also runs the draw in the background so the window never freezes.

How each line works: [`code/draw_code.md`](code/draw_code.md).

### Settings

| Setting | Value | Meaning |
|---|---|---|
| `MAX_PER_COUNTRY` | 2 | at most 2 opponents from one country |
| `MAX_ATTEMPTS` | 50 | fresh starts before giving up |
| `NODE_BUDGET` | 200 000 | steps allowed in one attempt |

### Speed

About 80 ms for a Champions League draw and its check, about twice as long for the Conference League.

---

## 8. What can go wrong

- **Not every valid draw is equally likely.** Because the program fills the hardest slot first and keeps the first choice that works, some valid draws come out a little more often than others. A perfectly fair draw would give each valid draw the same chance. For a simulation this matters very little.
- **If the user's bans make the draw impossible**, the program stops after 50 attempts with the message "no valid draw found", and says how many bans were in force. Removing some bans fixes it.
- **"No valid draw found" is not a proof** that no draw exists: the search stops early, so a valid draw might hide in a part it never explored.
- **The pots in the code are the 2024/25 ones.** Other seasons are loaded from template files in the app.

### Known bugs

- **Two ways of reporting a wrong competition name.** The Conference League file says clearly "draw_uecl only draws UECL"; the other file only raises a bare `KeyError`.

---

## 9. Ideas for later

- **One shared file** for the parts both engines repeat.
- **A fairer draw**: measure, on a tiny example where every valid draw can be listed, how often each one comes out, and correct the method if some are clearly favoured.

---

## 10. Words to know

| Word | Meaning |
|---|---|
| pot | a group of clubs of similar strength used in the draw |
| league phase | the first stage: 36 clubs in one table, each with 8 (or 6) different opponents |
| slot | one game a club still needs, for example "away against a pot-2 club" |
| most constrained first | always work on the slot with the fewest possible clubs |
| backtracking | trying a choice, going on, and undoing it when it leads to a dead end |
| attempt | one full search from an empty draw |
| seed | a number that fixes the random choices: same seed, same draw |

---
---

# Le tirage : qui joue contre qui

> Avant de jouer le moindre match, chaque club a besoin de sa liste d'adversaires. Cette partie fabrique cette liste pour la Ligue des champions, la Ligue Europa ou la Ligue Conférence, en respectant toutes les règles de l'UEFA, puis vérifie le résultat avant de le rendre.

## En bref

- **Ce qui entre :** les chapeaux (quatre listes de neuf clubs, ou six listes de six pour la Ligue Conférence), le pays de chaque club, et éventuellement des « matchs à domicile interdits » choisis par l'utilisateur.
- **Ce qui sort :** chaque match de la phase de ligue, écrit « club à domicile, club à l'extérieur » : 144 matchs (108 pour la Ligue Conférence).
- **Où c'est utilisé :** l'écran du tirage de l'appli l'anime ; ensuite le planificateur des journées ([`matchdays.md`](matchdays.md)) décide quel jour se joue chaque match.
- **Code :** `model/draw_ucl.py` (Ligue des champions et Ligue Europa) et `model/draw_uecl.py` (Ligue Conférence). Explication ligne par ligne : [`code/draw_code.md`](code/draw_code.md).

---

## 1. Les règles du tirage

Depuis 2024/25, la phase de ligue est un grand classement de 36 clubs. Les clubs sont répartis en **chapeaux** selon leur force (le chapeau 1 contient les plus forts).

**Ligue des champions et Ligue Europa :** 4 chapeaux de 9 clubs. Chaque club joue **8 matchs** :

- 2 adversaires de chaque chapeau (y compris le sien) ;
- de ces 2, un à domicile et un à l'extérieur ;
- donc 4 matchs à domicile et 4 à l'extérieur.

Les règles que chaque tirage doit respecter :

| Règle | En mots |
|---|---|
| 1 | chaque club joue exactement 8 matchs |
| 2 | un match à domicile et un à l'extérieur contre chaque chapeau |
| 3 | aucun adversaire du même pays (un club anglais ne rencontre jamais un autre club anglais) |
| 4 | au plus 2 adversaires d'un même pays |
| 5 | aucun club n'est rencontré deux fois |
| 6 | si A reçoit B, alors B se déplace chez A : les deux listes sont d'accord |
| 7 | les interdictions de l'utilisateur : s'il dit « Genk ne doit pas recevoir Brann », Genk ne reçoit jamais Brann (Brann qui reçoit Genk reste permis) |

Combien de matchs ? 36 clubs × 8 matchs = 288, mais chaque match est compté deux fois (une fois par club), donc il y a 288 ÷ 2 = **144 matchs**.

**Ligue Conférence :** 6 chapeaux de 6 clubs, **6 matchs** par club, un adversaire de chaque chapeau. Les chapeaux vont par paires (1 avec 2, 3 avec 4, 5 avec 6) : un club joue un chapeau de chaque paire à domicile et l'autre à l'extérieur, ce qui donne exactement 3 matchs à domicile et 3 à l'extérieur. 36 × 6 ÷ 2 = **108 matchs**.

---

## 2. Pourquoi c'est difficile

Ça a l'air facile : choisir des adversaires au hasard jusqu'à ce que chacun en ait 8. Mais les règles se gênent entre elles.

Imagine que la plupart des matchs sont déjà tirés. Barcelone a encore besoin d'un adversaire du chapeau 2, à l'extérieur. Les seuls clubs du chapeau 2 qui ont encore besoin d'un match à domicile contre le chapeau 1 sont l'Atlético Madrid (espagnol, donc interdit) et un club que Barcelone joue déjà. **Impasse.** Il faut alors remettre en question les choix d'avant.

Et essayer tous les tirages possibles est hors de question. Un calcul grossier donne environ un 1 suivi de **89 zéros** façons possibles d'associer les clubs. Même un ordinateur qui vérifierait un milliard de tirages par seconde aurait besoin de bien plus que l'âge de l'univers.

Le programme a donc besoin d'une méthode plus maligne.

---

## 3. Comment ça marche : comme un sudoku

La méthode est celle que beaucoup de gens utilisent pour un sudoku.

### Étape 1 : lister chaque match encore à tirer

Au départ, chaque club a besoin d'un match à domicile et d'un à l'extérieur contre chaque chapeau. Chacun de ces besoins s'appelle une **case** (*slot*). Par exemple :

- « Liverpool doit encore **se déplacer** chez un club du **chapeau 2** » ;
- « la Juventus doit encore **recevoir** un club du **chapeau 1** ».

36 clubs × 4 chapeaux × 2 (domicile et extérieur) = **288 cases**. Chaque match remplit deux cases à la fois : une par club.

### Étape 2 : remplir d'abord la case la plus difficile

Pour chaque case ouverte, le programme compte combien de clubs pourraient la remplir en respectant les règles (bon chapeau, pays différent, pas encore rencontré, limite par pays pas atteinte, pas interdit par l'utilisateur, et l'autre club a lui aussi encore besoin de ce match).

Il travaille ensuite sur la case qui a le **moins** de clubs possibles. Dans un sudoku, on commence aussi par la case où un seul chiffre est possible : ça ne coûte rien, et si une case n'a aucune possibilité, on apprend tout de suite qu'une erreur a été faite avant.

Cette règle a un nom : **« le plus contraint d'abord »** (en informatique, MRV, pour *minimum remaining values*).

### Étape 3 : essayer un club, continuer, défaire si on est bloqué

Le programme mélange les clubs possibles (c'est de là que vient le hasard du tirage), prend le premier, écrit le match, et passe à la case la plus difficile suivante.

Si plus tard il tombe sur une case **sans aucun club possible**, il revient en arrière : il efface le dernier match écrit et essaie le club suivant à la place. Si aucun club ne marche là non plus, il recule d'un pas de plus, et ainsi de suite. On appelle cela le **retour sur trace** (*backtracking*).

### Étape 4 : recommencer si c'est trop long

Un mauvais choix très tôt peut piéger la recherche très longtemps. Chaque essai a donc une limite de 200 000 pas. Si elle est atteinte, le programme jette tout et recommence un tirage à zéro, avec de nouveaux choix au hasard. Il s'autorise jusqu'à 50 nouveaux départs.

En pratique, sans interdictions de l'utilisateur, un tirage n'a presque jamais besoin de revenir en arrière : sur 100 tirages de test, les 100 ont fini au premier essai, en environ 144 pas (un par match).

### Étape 5 : tout revérifier

Quand le tirage est complet, un vérificateur séparé relit la liste finie et contrôle les 7 règles depuis le début. Il ne fait confiance à rien de ce que la recherche a écrit en chemin. Si un bug s'était glissé dans la recherche, le vérificateur l'attraperait et s'arrêterait avec un message clair, au lieu de rendre un tirage faux.

---

## 4. Un exemple complet à la main

Six clubs, deux chapeaux de trois. Chaque club joue un match à domicile et un à l'extérieur contre chaque chapeau, donc 4 matchs chacun et 12 matchs au total. Lyon et Lens sont tous les deux français, donc ils ne peuvent jamais se rencontrer.

| Chapeau 1 | Pays | Chapeau 2 | Pays |
|---|---|---|---|
| Lyon | France | Lens | France |
| Sevilla | Espagne | Mainz | Allemagne |
| Napoli | Italie | Braga | Portugal |

Les trois premières étapes du vrai programme :

| Étape | Case la plus difficile | Clubs possibles | Choix |
|---|---|---|---|
| 1 | Braga doit encore se déplacer chez un club du chapeau 2 | Mainz, Lens (2 choix ; aucune case n'en a moins) | Mainz reçoit Braga |
| 2 | Braga doit encore recevoir un club du chapeau 2 | seulement Lens (Braga joue déjà Mainz) | Braga reçoit Lens |
| 3 | Lens doit encore recevoir un club du chapeau 2 | seulement Mainz | Lens reçoit Mainz |

Les étapes 2 et 3 n'avaient qu'un seul club possible : elles étaient « forcées », exactement comme une case de sudoku avec un seul chiffre possible. Tout le tirage a fini en 12 pas, sans jamais revenir en arrière :

```
Dans le chapeau 1 :  Lyon reçoit Sevilla, Sevilla reçoit Napoli, Napoli reçoit Lyon
Dans le chapeau 2 :  Mainz reçoit Braga, Braga reçoit Lens, Lens reçoit Mainz

Le chapeau 1 reçoit le chapeau 2     Le chapeau 2 reçoit le chapeau 1
Lyon    reçoit Braga                 Lens  reçoit Sevilla
Sevilla reçoit Mainz                 Mainz reçoit Lyon
Napoli  reçoit Lens                  Braga reçoit Napoli
```

Vérification : chaque club reçoit 2 fois et se déplace 2 fois, joue chaque chapeau une fois à domicile et une fois à l'extérieur, et Lyon ne rencontre jamais Lens.

---

## 5. À essayer en Python

Une petite version de la même méthode pour les six clubs ci-dessus : cases, la plus difficile d'abord, essayer et défaire.

```python
import random

POTS = [["Lyon", "Sevilla", "Napoli"], ["Lens", "Mainz", "Braga"]]
COUNTRY = {"Lyon": "France", "Sevilla": "Spain", "Napoli": "Italy",
           "Lens": "France", "Mainz": "Germany", "Braga": "Portugal"}
POT_OF = {club: p for p, pot in enumerate(POTS) for club in pot}

# Une "case" est un match dont un club a encore besoin : (club, chapeau de l'adversaire, à domicile ?)
slots = {(club, p, home) for club in COUNTRY for p in range(len(POTS)) for home in (True, False)}
played = {club: set() for club in COUNTRY}
fixtures = []                      # (club à domicile, club à l'extérieur)

def options(slot):
    club, p, home = slot
    good = []
    for other in POTS[p]:
        if other == club or COUNTRY[other] == COUNTRY[club]:
            continue                                   # pas lui-même, pas le même pays
        if other in played[club]:
            continue                                   # pas de deuxième rencontre
        if (other, POT_OF[club], not home) not in slots:
            continue                                   # l'autre club doit encore avoir besoin de ce match
        good.append(other)
    return good

def fill(rng):
    if not slots:
        return True                                    # tous les matchs sont tirés
    slot = min(sorted(slots), key=lambda s: len(options(s)))   # la case la plus difficile d'abord
    club, p, home = slot
    choices = options(slot)
    rng.shuffle(choices)
    for other in choices:
        mirror = (other, POT_OF[club], not home)       # le même match, vu par l'autre club
        slots.discard(slot); slots.discard(mirror)
        played[club].add(other); played[other].add(club)
        fixtures.append((club, other) if home else (other, club))
        if fill(rng):
            return True
        fixtures.pop()                                 # impasse : défaire et essayer le club suivant
        played[club].discard(other); played[other].discard(club)
        slots.add(slot); slots.add(mirror)
    return False

fill(random.Random(1))
for home, away in sorted(fixtures):
    print(f"{home} hosts {away}")
print(len(fixtures), "games")
```

Résultat :

```
Braga hosts Lens
Braga hosts Napoli
Lens hosts Mainz
Lens hosts Sevilla
Lyon hosts Braga
Lyon hosts Sevilla
Mainz hosts Braga
Mainz hosts Lyon
Napoli hosts Lens
Napoli hosts Lyon
Sevilla hosts Mainz
Sevilla hosts Napoli
12 games
```

Remplace `random.Random(1)` par `random.Random(2)` : tu obtiens un autre tirage valide. Le même nombre donne toujours le même tirage ; ce nombre s'appelle la **graine** (*seed*).

---

## 6. La version Ligue Conférence

La Ligue Conférence a une autre forme, donc elle a son propre fichier, `model/draw_uecl.py`. L'idée est la même (cases, la plus difficile d'abord, défaire, recommencer, vérifier) ; ce qui change :

| | Ligue des champions, Ligue Europa | Ligue Conférence |
|---|---|---|
| Chapeaux | 4 de 9 | 6 de 6 |
| Matchs contre chaque chapeau | 2 : un à domicile, un à l'extérieur | 1 : à domicile **ou** à l'extérieur, et le sens fait partie du tirage |
| Domicile / extérieur | 4 / 4 | 3 / 3, grâce aux chapeaux en paires |
| Quand un match est tiré | 2 cases se ferment (une par club) | jusqu'à 6 cases se ferment : les deux sens pour les deux clubs contre ce chapeau, plus la case du chapeau associé qui doit maintenant aller dans l'autre sens |

Les deux fichiers répètent plusieurs parties (lecture des pays, affichage, vérification). Un changement fait dans l'un est facile à oublier dans l'autre ; regrouper les parties communes dans un seul fichier serait plus propre.

---

## 7. Ce que le code utilise

### Modules Python

Tous sont fournis avec Python ; rien à installer.

| Module | Ce qu'il fait ici |
|---|---|
| `random` | mélange les clubs possibles ; `random.Random(seed)` donne un générateur de hasard privé, pour que la même graine donne toujours le même tirage |
| `csv` | lit le pays de chaque club dans `data/processed/countries_filled_25.csv` |
| `collections` (`defaultdict`) | compte les adversaires par pays, en partant de 0 pour un pays jamais vu |
| `functools` (`lru_cache`) | garde en mémoire le fichier des pays après la première lecture, pour ne pas le relire à chaque tirage |
| `itertools` (`chain`) | parcourt les adversaires à domicile et à l'extérieur d'un club comme une seule liste |
| `pathlib` | construit le chemin du fichier des pays |
| `time` | mesure la durée d'un tirage (seulement dans la démo en bas du fichier) |

Il utilise aussi `model/names.py` ([`names.md`](names.md)) quand le nom d'un club est écrit différemment dans les chapeaux et dans le fichier des pays.

### Fonctions de `model/draw_ucl.py`

| Fonction | En une ligne |
|---|---|
| `generate_draw` | le point d'entrée : prépare tout, lance le tirage, le vérifie, renvoie le résultat |
| `draw` | lance jusqu'à 50 essais (étape 4) |
| `fill` | la recherche elle-même : la case la plus difficile d'abord, essayer, défaire (étapes 2 et 3) |
| `options` | liste les clubs qui peuvent remplir une case en respectant les règles |
| `link`, `unlink` | écrivent un match dans les listes des deux clubs, et l'effacent |
| `verify` | la vérification finale des 7 règles (étape 5) |
| `build_teams` | prépare une fiche vide pour chaque club |
| `load_countries` | lit le pays de chaque club |
| `fixtures` | renvoie le tirage fini sous forme de liste de matchs (domicile, extérieur) |
| `show` | affiche le tirage chapeau par chapeau |

`model/draw_uecl.py` a les mêmes fonctions, plus `paired_pot` (quel chapeau va avec quel autre) et `faced_from` (combien d'adversaires un club a déjà d'un même pays). L'appli atteint les deux fichiers par `interface/draw_engine.py`, qui lance aussi le tirage en arrière-plan pour que la fenêtre ne se fige jamais.

Comment marche chaque ligne : [`code/draw_code.md`](code/draw_code.md).

### Réglages

| Réglage | Valeur | Sens |
|---|---|---|
| `MAX_PER_COUNTRY` | 2 | au plus 2 adversaires d'un même pays |
| `MAX_ATTEMPTS` | 50 | nouveaux départs avant d'abandonner |
| `NODE_BUDGET` | 200 000 | pas permis dans un essai |

### Vitesse

Environ 80 ms pour un tirage de Ligue des champions et sa vérification, environ deux fois plus pour la Ligue Conférence.

---

## 8. Ce qui peut mal tourner

- **Tous les tirages valides n'ont pas la même chance.** Comme le programme remplit d'abord la case la plus difficile et garde le premier choix qui marche, certains tirages valides sortent un peu plus souvent que d'autres. Un tirage parfaitement équitable donnerait la même chance à chaque tirage valide. Pour une simulation, cela compte très peu.
- **Si les interdictions de l'utilisateur rendent le tirage impossible**, le programme s'arrête après 50 essais avec le message « no valid draw found », et dit combien d'interdictions étaient actives. En retirer quelques-unes règle le problème.
- **« No valid draw found » n'est pas une preuve** qu'aucun tirage n'existe : la recherche s'arrête tôt, donc un tirage valide pourrait se cacher dans une partie jamais explorée.
- **Les chapeaux écrits dans le code sont ceux de 2024/25.** Les autres saisons sont chargées depuis des fichiers modèles dans l'appli.

### Bugs connus

- **Deux façons de signaler un mauvais nom de compétition.** Le fichier de la Ligue Conférence dit clairement « draw_uecl only draws UECL » ; l'autre fichier ne lève qu'une `KeyError` sans explication.

---

## 9. Idées pour plus tard

- **Un fichier commun** pour les parties que les deux moteurs répètent.
- **Un tirage plus équitable** : mesurer, sur un tout petit exemple où l'on peut lister tous les tirages valides, combien de fois chacun sort, et corriger la méthode si certains sont nettement favorisés.

---

## 10. Mots à connaître

| Mot | Sens |
|---|---|
| chapeau | un groupe de clubs de force proche, utilisé pour le tirage |
| phase de ligue | le premier tour : 36 clubs dans un seul classement, chacun avec 8 (ou 6) adversaires différents |
| case (slot) | un match dont un club a encore besoin, par exemple « à l'extérieur contre un club du chapeau 2 » |
| le plus contraint d'abord | toujours travailler sur la case qui a le moins de clubs possibles |
| retour sur trace (backtracking) | essayer un choix, continuer, et le défaire s'il mène à une impasse |
| essai | une recherche complète à partir d'un tirage vide |
| graine (seed) | un nombre qui fixe les choix au hasard : même graine, même tirage |

---
