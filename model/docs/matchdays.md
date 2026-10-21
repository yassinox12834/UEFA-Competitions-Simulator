# The matchday planner: which match is played on which day

> The draw says who plays whom, but not when. This part gives each match a matchday so that no club ever plays twice on the same day.

*Version française : [plus bas](#le-planificateur-des-journées--quel-match-se-joue-quel-jour).*

## In short

- **What goes in:** a finished draw (144 matches, or 108 for the Conference League).
- **What comes out:** 8 matchdays of 18 matches (6 matchdays for the Conference League). Every club plays exactly once on every matchday.
- **Where it is used:** right after the draw; the league phase ([`league_phase.md`](league_phase.md)) then plays the days in order.
- **Code:** `model/matchdays_ucl.py` (used by all three competitions) and `model/matchdays_uecl.py` (an extra check for the Conference League). Line-by-line walkthrough: [`code/matchdays_code.md`](code/matchdays_code.md).

---

## 1. The problem

Each club plays 8 matches and there are 8 matchdays. So each club must play **exactly once every matchday**: no day off, never twice.

On each matchday, all 36 clubs play, two per match, so there are 36 ÷ 2 = 18 matches per day. And 8 days × 18 matches = 144: every match of the draw gets a day.

It is like planning a school timetable: each teacher (club) gives 8 lessons (matches), there are 8 time slots (matchdays), and a teacher cannot be in two classrooms at the same time.

Why is it not trivial? Imagine Liverpool v Juventus on day 1 and Juventus v Benfica on day 2. Now Benfica v Liverpool cannot be on day 1 (Liverpool are busy) or day 2 (Benfica are busy). Each choice removes options for other matches, and a few bad early choices can leave a match with no free day at all.

---

## 2. How it works: the same method as the draw

The planner uses the same method as the draw ([`draw.md`](draw.md), section 3), with "a day" instead of "an opponent":

1. For every match not placed yet, count its **free days**: days on which neither club already plays.
2. Pick the match with the **fewest free days** (the most constrained first). A match with only one free day is forced; a match with zero free days shows at once that an earlier choice was wrong.
3. Try its free days in random order: place the match, then go on with the next match.
4. If the program gets stuck later, it **undoes** the last placement and tries another day (backtracking).
5. Each attempt may take up to 200 000 steps. If it runs out, the program starts again from an empty calendar with new random choices, up to 30 times.

For the Conference League, a separate checker then reads the finished calendar and checks everything again: 6 days, 18 matches a day, all 36 clubs every day, nobody twice, and exactly the same matches as the draw, none missing and none invented.

---

## 3. A full example by hand

Four clubs, A, B, C and D. Each plays the three others: 6 matches (AB, AC, AD, BC, BD, CD) on 3 days. Each day must hold 2 matches, so that all four clubs play.

| Step | Free days of each match left | Picked (fewest free days) | Placed on |
|---|---|---|---|
| 1 | all six: days 1, 2, 3 | AB (first in alphabetical order) | day 1 |
| 2 | AC 2 or 3, AD 2 or 3, BC 2 or 3, BD 2 or 3, CD 1, 2 or 3 | AC (2 free days) | day 2 |
| 3 | AD: only 3 | AD (forced) | day 3 |
| 4 | BC only 3, BD only 2, CD only 1 | BC | day 3 |
| 5 | BD only 2, CD only 1 | BD | day 2 |
| 6 | CD only 1 | CD | day 1 |

Result: day 1 = AB and CD; day 2 = AC and BD; day 3 = AD and BC. Six steps, no going back.

**What "fewest free days first" avoided.** At step 2, CD still had three free days. A simpler program that just took "the next match in the list" might put CD on day 2. Then AC, AD, BC and BD would all have only day 3 left. The first would go there, and the next one would find no free day: a dead end, and the program would have to undo. Picking AC first (2 free days, not 3) avoids the trap.

---

## 4. Try it in Python

The same four clubs, with the same method: fewest free days first, try, undo.

```python
import random

matches = [("A", "B"), ("A", "C"), ("A", "D"), ("B", "C"), ("B", "D"), ("C", "D")]
NUM_DAYS = 3
busy = {club: set() for club in "ABCD"}     # days on which each club already plays
day_of = {}                                  # match -> day

def free_days(match):
    home, away = match
    return [d for d in range(NUM_DAYS) if d not in busy[home] and d not in busy[away]]

def plan(rng):
    left = [m for m in matches if m not in day_of]
    if not left:
        return True
    match = min(sorted(left), key=lambda m: len(free_days(m)))   # fewest free days first
    days = free_days(match)
    rng.shuffle(days)
    for day in days:
        home, away = match
        busy[home].add(day); busy[away].add(day); day_of[match] = day
        if plan(rng):
            return True
        busy[home].discard(day); busy[away].discard(day); del day_of[match]   # undo
    return False

plan(random.Random(0))
for day in range(NUM_DAYS):
    print(f"Day {day + 1}:", [f"{h} v {a}" for (h, a), d in sorted(day_of.items()) if d == day])
```

Output:

```
Day 1: ['A v B', 'C v D']
Day 2: ['A v D', 'B v C']
Day 3: ['A v C', 'B v D']
```

The days are not the same as in section 3, because the random order in which free days are tried is different. Both calendars are valid: every club plays once a day.

---

## 5. Does a calendar always exist?

Think of the clubs as dots, and of each match as a line between two dots. Choosing a day for a match is like painting its line in one of 8 colours, with one rule: two lines that touch the same dot (two matches of the same club) must have different colours. Mathematicians call this **edge colouring**.

A theorem (Vizing, 1964) says that 8 or 9 colours are always enough when every dot has 8 lines. We need exactly 8, and that is not guaranteed by any theorem for our kind of draw. In practice, it has always worked: 300 Champions League draws and 300 Conference League draws all got a calendar, almost always at the first attempt.

---

## 6. How fast is it?

Measured on 300 draws per competition:

| | solved at the first attempt | second | third | typical time | slowest |
|---|---|---|---|---|---|
| Champions League (144 matches) | 280 | 18 | 2 | 15 ms | 5.6 s |
| Conference League (108 matches) | 298 | 2 | 0 | 6 ms | 2.1 s |

The slow cases are attempts that get stuck: they use all 200 000 steps (a few seconds) before restarting, and the restart then usually succeeds at once. With a limit of 5 000 steps instead, the same 300 draws never failed, and the slowest took 0.31 s. Restarting early is often better than insisting.

---

## 7. What the code uses

### Python modules

All come with Python; nothing needs to be installed.

| Module | What it does here |
|---|---|
| `random` | shuffles the free days; a private `random.Random(seed)` makes the same seed give the same calendar |
| `collections` (`defaultdict`, `Counter`) | `defaultdict(set)` keeps the busy days of each club; `Counter` counts matches in the Conference League check |
| `sys`, `pathlib` | let the file be run directly as a script by finding the project folder |
| `time` | times the demo at the bottom of the file |

### Functions

| Function | File | In one line |
|---|---|---|
| `generate_matchdays` | `matchdays_ucl.py` | the entry point: lists the matches, runs up to 30 attempts, returns the days |
| `_schedule_matchdays_once` | `matchdays_ucl.py` | one attempt: fewest free days first, try, undo |
| `verify_matchdays` | `matchdays_uecl.py` | rechecks a finished Conference League calendar |
| `generate_uecl_matchdays` | `matchdays_uecl.py` | draw, calendar and check in one call |

How each line works: [`code/matchdays_code.md`](code/matchdays_code.md).

---

## 8. What can go wrong

- **Only one rule is checked**: no club twice on the same day. Nothing spreads home and away matches over time: about half of the clubs get 3 home (or 3 away) matches in a row at some point, and about 1 in 10 get 4 in a row.
- **No other calendar rules**: two clubs of the same city on the same evening, and so on, are not handled.
- **The order of the days matters a little** for the simulation: ratings change after every match, so the same matches in another order give slightly different chances later.
- **A calendar is not proved to exist** (section 5). If one ever failed, the program would stop with an error after 30 attempts.

### Known bugs

- **The step limit is far too high** (section 6). Lowering it from 200 000 to 5 000 would make the slowest case about 18 times faster. Note: it would change the calendar of the few draws that needed more than 5 000 steps.
- **A junk line in a comment** of `_schedule_matchdays_once` ("SHuuuu...t up/down"). It should be deleted.
- **A typo in the error message**: it prints "8-:matchday" instead of "8-matchday".

---

## 9. Ideas for later

- **Restart earlier**: 5 000 steps per attempt and up to 100 attempts.
- **Balance home and away**: add a rule such as "never 3 matches in a row at the same ground". The method stays the same; only the "free day" test grows.

---

## 10. Words to know

| Word | Meaning |
|---|---|
| matchday | one round of the league phase, when every club plays once |
| free day | a day on which neither club of a match already plays |
| most constrained first | always place next the match with the fewest free days |
| backtracking | trying a choice, going on, and undoing it if it leads to a dead end |
| edge colouring | painting lines between dots so that lines touching the same dot have different colours; here, colours are days |
| step limit (node budget) | how many steps one attempt may take before starting again |


---
---

# Le planificateur des journées : quel match se joue quel jour

> Le tirage dit qui joue contre qui, mais pas quand. Cette partie donne une journée à chaque match pour qu'aucun club ne joue jamais deux fois le même jour.

## En bref

- **Ce qui entre :** un tirage fini (144 matchs, ou 108 pour la Ligue Conférence).
- **Ce qui sort :** 8 journées de 18 matchs (6 journées pour la Ligue Conférence). Chaque club joue exactement une fois à chaque journée.
- **Où c'est utilisé :** juste après le tirage ; la phase de ligue ([`league_phase.md`](league_phase.md)) joue ensuite les journées dans l'ordre.
- **Code :** `model/matchdays_ucl.py` (utilisé par les trois compétitions) et `model/matchdays_uecl.py` (une vérification en plus pour la Ligue Conférence). Explication ligne par ligne : [`code/matchdays_code.md`](code/matchdays_code.md).

---

## 1. Le problème

Chaque club joue 8 matchs et il y a 8 journées. Chaque club doit donc jouer **exactement une fois à chaque journée** : aucun jour de repos, jamais deux fois.

À chaque journée, les 36 clubs jouent, deux par match, donc il y a 36 ÷ 2 = 18 matchs par jour. Et 8 jours × 18 matchs = 144 : chaque match du tirage reçoit un jour.

C'est comme faire l'emploi du temps d'une école : chaque professeur (club) donne 8 cours (matchs), il y a 8 créneaux (journées), et un professeur ne peut pas être dans deux salles en même temps.

Pourquoi ce n'est pas évident ? Imagine Liverpool-Juventus le jour 1 et Juventus-Benfica le jour 2. Maintenant Benfica-Liverpool ne peut pas être le jour 1 (Liverpool est occupé) ni le jour 2 (Benfica est occupé). Chaque choix enlève des possibilités à d'autres matchs, et quelques mauvais choix au début peuvent laisser un match sans aucun jour libre.

---

## 2. Comment ça marche : la même méthode que le tirage

Le planificateur utilise la même méthode que le tirage ([`draw.md`](draw.md), section 3), avec « un jour » à la place d'« un adversaire » :

1. Pour chaque match pas encore placé, compter ses **jours libres** : les jours où aucun des deux clubs ne joue déjà.
2. Choisir le match qui a **le moins de jours libres** (le plus contraint d'abord). Un match avec un seul jour libre est forcé ; un match avec zéro jour libre montre tout de suite qu'un choix précédent était mauvais.
3. Essayer ses jours libres dans un ordre au hasard : placer le match, puis continuer avec le match suivant.
4. Si le programme se retrouve bloqué plus tard, il **défait** le dernier placement et essaie un autre jour (retour sur trace).
5. Chaque essai a droit à 200 000 pas au plus. S'il les épuise, le programme recommence à partir d'un calendrier vide avec de nouveaux choix au hasard, jusqu'à 30 fois.

Pour la Ligue Conférence, un vérificateur séparé relit ensuite le calendrier fini et revérifie tout : 6 journées, 18 matchs par jour, les 36 clubs chaque jour, personne deux fois, et exactement les mêmes matchs que le tirage, aucun manquant et aucun inventé.

---

## 3. Un exemple complet à la main

Quatre clubs, A, B, C et D. Chacun joue les trois autres : 6 matchs (AB, AC, AD, BC, BD, CD) sur 3 jours. Chaque jour doit contenir 2 matchs, pour que les quatre clubs jouent.

| Étape | Jours libres de chaque match restant | Choisi (le moins de jours libres) | Placé le |
|---|---|---|---|
| 1 | les six : jours 1, 2, 3 | AB (premier dans l'ordre alphabétique) | jour 1 |
| 2 | AC 2 ou 3, AD 2 ou 3, BC 2 ou 3, BD 2 ou 3, CD 1, 2 ou 3 | AC (2 jours libres) | jour 2 |
| 3 | AD : seulement 3 | AD (forcé) | jour 3 |
| 4 | BC seulement 3, BD seulement 2, CD seulement 1 | BC | jour 3 |
| 5 | BD seulement 2, CD seulement 1 | BD | jour 2 |
| 6 | CD seulement 1 | CD | jour 1 |

Résultat : jour 1 = AB et CD ; jour 2 = AC et BD ; jour 3 = AD et BC. Six pas, aucun retour en arrière.

**Ce que « le moins de jours libres d'abord » a évité.** À l'étape 2, CD avait encore trois jours libres. Un programme plus simple qui prendrait juste « le match suivant de la liste » pourrait mettre CD le jour 2. Alors AC, AD, BC et BD n'auraient plus que le jour 3. Le premier y irait, et le suivant ne trouverait aucun jour libre : une impasse, et le programme devrait défaire. Choisir AC d'abord (2 jours libres, pas 3) évite le piège.

---

## 4. À essayer en Python

Les quatre mêmes clubs, avec la même méthode : le moins de jours libres d'abord, essayer, défaire.

```python
import random

matches = [("A", "B"), ("A", "C"), ("A", "D"), ("B", "C"), ("B", "D"), ("C", "D")]
NUM_DAYS = 3
busy = {club: set() for club in "ABCD"}     # jours où chaque club joue déjà
day_of = {}                                  # match -> jour

def free_days(match):
    home, away = match
    return [d for d in range(NUM_DAYS) if d not in busy[home] and d not in busy[away]]

def plan(rng):
    left = [m for m in matches if m not in day_of]
    if not left:
        return True
    match = min(sorted(left), key=lambda m: len(free_days(m)))   # le moins de jours libres d'abord
    days = free_days(match)
    rng.shuffle(days)
    for day in days:
        home, away = match
        busy[home].add(day); busy[away].add(day); day_of[match] = day
        if plan(rng):
            return True
        busy[home].discard(day); busy[away].discard(day); del day_of[match]   # défaire
    return False

plan(random.Random(0))
for day in range(NUM_DAYS):
    print(f"Day {day + 1}:", [f"{h} v {a}" for (h, a), d in sorted(day_of.items()) if d == day])
```

Résultat :

```
Day 1: ['A v B', 'C v D']
Day 2: ['A v D', 'B v C']
Day 3: ['A v C', 'B v D']
```

Les jours ne sont pas les mêmes qu'à la section 3, car l'ordre au hasard dans lequel les jours libres sont essayés est différent. Les deux calendriers sont valides : chaque club joue une fois par jour.

---

## 5. Un calendrier existe-t-il toujours ?

Imagine les clubs comme des points, et chaque match comme un trait entre deux points. Choisir un jour pour un match, c'est comme peindre son trait d'une des 8 couleurs, avec une règle : deux traits qui touchent le même point (deux matchs du même club) doivent avoir des couleurs différentes. Les mathématiciens appellent cela une **coloration des arêtes**.

Un théorème (Vizing, 1964) dit que 8 ou 9 couleurs suffisent toujours quand chaque point a 8 traits. Il nous en faut exactement 8, et aucun théorème ne le garantit pour notre type de tirage. En pratique, cela a toujours marché : 300 tirages de Ligue des champions et 300 de Ligue Conférence ont tous reçu un calendrier, presque toujours au premier essai.

---

## 6. À quelle vitesse ?

Mesuré sur 300 tirages par compétition :

| | réussi au premier essai | deuxième | troisième | temps habituel | le plus lent |
|---|---|---|---|---|---|
| Ligue des champions (144 matchs) | 280 | 18 | 2 | 15 ms | 5.6 s |
| Ligue Conférence (108 matchs) | 298 | 2 | 0 | 6 ms | 2.1 s |

Les cas lents sont des essais qui restent bloqués : ils utilisent les 200 000 pas (quelques secondes) avant de recommencer, et le nouvel essai réussit alors en général tout de suite. Avec une limite de 5 000 pas, les mêmes 300 tirages n'ont jamais échoué, et le plus lent a pris 0.31 s. Recommencer tôt vaut souvent mieux qu'insister.

---

## 7. Ce que le code utilise

### Modules Python

Tous sont fournis avec Python ; rien à installer.

| Module | Ce qu'il fait ici |
|---|---|
| `random` | mélange les jours libres ; un `random.Random(seed)` privé fait que la même graine donne le même calendrier |
| `collections` (`defaultdict`, `Counter`) | `defaultdict(set)` garde les jours occupés de chaque club ; `Counter` compte les matchs dans la vérification de la Ligue Conférence |
| `sys`, `pathlib` | permettent de lancer le fichier directement comme un script en trouvant le dossier du projet |
| `time` | chronomètre la démo en bas du fichier |

### Fonctions

| Fonction | Fichier | En une ligne |
|---|---|---|
| `generate_matchdays` | `matchdays_ucl.py` | le point d'entrée : liste les matchs, lance jusqu'à 30 essais, renvoie les journées |
| `_schedule_matchdays_once` | `matchdays_ucl.py` | un essai : le moins de jours libres d'abord, essayer, défaire |
| `verify_matchdays` | `matchdays_uecl.py` | revérifie un calendrier fini de Ligue Conférence |
| `generate_uecl_matchdays` | `matchdays_uecl.py` | tirage, calendrier et vérification en un seul appel |

Comment marche chaque ligne : [`code/matchdays_code.md`](code/matchdays_code.md).

---

## 8. Ce qui peut mal tourner

- **Une seule règle est vérifiée** : aucun club deux fois le même jour. Rien ne répartit les matchs à domicile et à l'extérieur dans le temps : environ la moitié des clubs ont à un moment 3 matchs à domicile (ou 3 à l'extérieur) d'affilée, et environ 1 sur 10 en a 4 d'affilée.
- **Pas d'autres règles de calendrier** : deux clubs de la même ville le même soir, etc., ne sont pas gérés.
- **L'ordre des journées compte un peu** pour la simulation : les notes changent après chaque match, donc les mêmes matchs dans un autre ordre donnent des chances un peu différentes plus tard.
- **L'existence d'un calendrier n'est pas prouvée** (section 5). Si un jour il n'y en avait pas, le programme s'arrêterait avec une erreur après 30 essais.

### Bugs connus

- **La limite de pas est bien trop haute** (section 6). La faire passer de 200 000 à 5 000 rendrait le cas le plus lent environ 18 fois plus rapide. Attention : cela changerait le calendrier des quelques tirages qui avaient besoin de plus de 5 000 pas.
- **Une ligne parasite dans un commentaire** de `_schedule_matchdays_once` (« SHuuuu...t up/down »). Elle devrait être supprimée.
- **Une faute dans le message d'erreur** : il affiche « 8-:matchday » au lieu de « 8-matchday ».

---

## 9. Idées pour plus tard

- **Recommencer plus tôt** : 5 000 pas par essai et jusqu'à 100 essais.
- **Équilibrer domicile et extérieur** : ajouter une règle comme « jamais 3 matchs d'affilée dans le même stade ». La méthode reste la même ; seul le test du « jour libre » s'agrandit.

---

## 10. Mots à connaître

| Mot | Sens |
|---|---|
| journée | un tour de la phase de ligue, où chaque club joue une fois |
| jour libre | un jour où aucun des deux clubs d'un match ne joue déjà |
| le plus contraint d'abord | toujours placer ensuite le match qui a le moins de jours libres |
| retour sur trace | essayer un choix, continuer, et le défaire s'il mène à une impasse |
| coloration des arêtes | peindre des traits entre des points pour que les traits qui touchent le même point aient des couleurs différentes ; ici, les couleurs sont les jours |
| limite de pas (node budget) | combien de pas un essai peut faire avant de recommencer |

---
