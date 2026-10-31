# Name matching: one club, two spellings

> The same club is often written in two different ways inside this project. This part finds out that "Bayern Munich" and "Bayern München" are the same club, so that every club in the draw gets its strength rating.

*Version française : [plus bas](#correspondance-des-noms--un-club-deux-orthographes).*

## In short

- **What goes in:** the club names from the pots (the lists used for the draw), and the club names from the ratings file.
- **What comes out:** for each club in the pots, the matching name in the ratings file, and how it was found.
- **Where it is used:** at the start of every simulation, to give each club its rating.
- **Code:** `model/names.py`. Line-by-line walkthrough: [`code/names_code.md`](code/names_code.md).

---

## 1. The problem

The project uses two lists of clubs that were written by different people.

- **The pots** (the lists for the draw) use the names fans know: "Bayern Munich", "Inter Milan", "Brest".
- **The ratings file** comes from a football data website. It uses other names: "Bayern München", "Inter", "Stade Brestois 29".

A computer is very strict. For it, "Bayern Munich" and "Bayern München" are two different pieces of text, so it would think Bayern has no rating at all.

Think of a school with two class lists. One teacher wrote "Mo Salah", the other wrote "Mohamed Salah". A person sees at once that it is the same pupil. A computer needs rules to see it.

This part of the code is the only place in the project where the two spellings meet.

---

## 2. How it works: four tries, in order

For each club in the pots, the code tries four things, one after the other. As soon as one works, it stops.

### Try 1: the exact same name

Is the name written in exactly the same way in the ratings file?

- "Real Madrid" in the pots, "Real Madrid" in the ratings file: found.

Most clubs are found here. In the Champions League, 27 of the 36 clubs are.

### Try 2: a list written by hand

Some names have nothing in common. "Red Star Belgrade" (English) and "FK Crvena Zvezda" (Serbian) do not share a single word. No rule could guess that they are the same club.

So the code keeps a small list, written by hand, of pairs that mean the same club. It is called the **alias list** (an alias is another name for the same thing). It has 18 pairs, for example:

| In the pots | In the ratings file |
|---|---|
| Bayern Munich | Bayern München |
| Inter Milan | Inter |
| Red Star Belgrade | FK Crvena Zvezda |
| Brest | Stade Brestois 29 |
| Sparta Prague | Sparta Praha |

If a club is in this list, the code trusts the list and stops.

### Try 3: clean both names, then compare

Many differences are just "noise": capital letters, accents, dashes, and little words like "FC" that do not tell you which club it is. So the code cleans each name:

1. Take the accents off the letters: "é" becomes "e".
2. Write everything in small letters.
3. Turn dashes, dots and slashes into spaces.
4. Remove the little words that every club uses, like "FC", "AC", "SC", "Club".

| Before cleaning | After cleaning |
|---|---|
| Atlético Madrid | atletico madrid |
| FC Porto | porto |
| Paris Saint-Germain | paris saint germain |
| 1. FC Heidenheim | heidenheim |
| AC Milan | milan |
| Bodo/Glimt | bodo glimt |

Now "Porto" and "FC Porto" both become "porto". Same text, so it is a match.

### Try 4: "this name looks very close"

If nothing has worked yet, the code compares the cleaned name with all 984 names of the ratings file and gives each one a **similarity score**:

- 1 means "exactly the same letters, in the same order";
- 0 means "nothing in common".

The score counts how many letters the two names share, in the same order, compared with their total length.

| Name from the pots | Closest name in the file | Score |
|---|---|---|
| man city | manchester city | 0.70 |
| racing casablanca | raja casablanca | 0.81 |

The code only accepts the closest name if **both** of these are true:

- the score is at least **0.80** (the names really look alike);
- the closest name is at least **0.05** ahead of the second closest one (there is a clear winner, not two names that look equally good).

Why so careful? Because a wrong match is worse than no match. If "Racing" got the rating of "Raja", the simulation would play the wrong club and nobody would notice.

### If all four tries fail

The club is not removed. It starts the simulation with an average rating of **1500**, and the app shows a warning: "not found in the Elo file, starting at 1500". This way, a missing club is always visible.

---

## 3. A full example

Imagine the ratings file had only four names: "Bayern München", "FC Copenhagen", "Real Madrid", "FC Porto". Here is what happens to five clubs from the pots:

| Club in the pots | Try 1: exact | Try 2: alias list | Try 3: cleaned | Result |
|---|---|---|---|---|
| Real Madrid | found | | | "Real Madrid" |
| Bayern Munich | no | found: "Bayern München" | | "Bayern München" |
| Copenhagen | no | not in the list | "copenhagen" = "copenhagen" | "FC Copenhagen" |
| Porto | no | not in the list | "porto" = "porto" | "FC Porto" |
| Zzz United | no | no | no, and try 4 finds nothing close | missing, starts at 1500 |

---

## 4. Try it in Python

This small program does the same four tries, with only Python's own tools. You can copy it and run it.

```python
import difflib
import re
import unicodedata

ALIASES = {"Bayern Munich": "Bayern München"}
LITTLE_WORDS = {"fc", "ac", "sc", "club"}

def clean(name):
    text = unicodedata.normalize("NFKD", name)                         # split "é" into "e" + accent
    text = "".join(ch for ch in text if not unicodedata.combining(ch))  # drop the accents
    text = re.sub(r"[^a-z0-9 ]+", " ", text.lower())                    # small letters, no symbols
    return " ".join(w for w in text.split() if w not in LITTLE_WORDS)

def find(club, file_names):
    if club in file_names:                                    # try 1
        return club, "exact"
    if ALIASES.get(club) in file_names:                       # try 2
        return ALIASES[club], "alias"
    cleaned = {clean(n): n for n in file_names}
    if clean(club) in cleaned:                                # try 3
        return cleaned[clean(club)], "cleaned"
    scores = sorted(((difflib.SequenceMatcher(None, clean(club), c).ratio(), n)
                     for c, n in cleaned.items()), reverse=True)
    best, second = scores[0][0], scores[1][0]
    if best >= 0.80 and best - second >= 0.05:                # try 4
        return scores[0][1], f"close ({best:.2f})"
    return None, "missing"

file_names = ["Bayern München", "FC Porto", "Real Madrid", "Raja Casablanca"]
for club in ["Real Madrid", "Bayern Munich", "Porto", "Racing Casablanca", "Man City"]:
    print(club, "->", find(club, file_names))
```

Output:

```
Real Madrid -> ('Real Madrid', 'exact')
Bayern Munich -> ('Bayern München', 'alias')
Porto -> ('FC Porto', 'cleaned')
Racing Casablanca -> ('Raja Casablanca', 'close (0.81)')
Man City -> (None, 'missing')
```

Look at "Racing Casablanca": it was matched to "Raja Casablanca", which is a **different club**. That is the weak point of try 4 (section 6).

---

## 5. What the code uses

### Python modules

All three come with Python; nothing needs to be installed.

| Module | What it is | What it does here |
|---|---|---|
| `unicodedata` | knows every letter of every alphabet | takes the accents off ("é" to "e", "ş" to "s") |
| `re` | "regular expressions": patterns to find and replace text | replaces every dash, dot, slash and symbol with a space |
| `difflib` | compares two pieces of text | gives the similarity score of try 4 (`SequenceMatcher`) |

### Functions in `model/names.py`

| Function | In one line |
|---|---|
| `normalise` | cleans a name (try 3) |
| `resolve` | runs the four tries for one club |
| `build_index` | cleans all 984 names of the ratings file once, so they are not cleaned again for every club |
| `resolve_all` | runs `resolve` for every club of the pots |
| `Resolution` | a small record: the club, the name found, and which try found it |

Two other parts of the project use it: `model/simulation.py` (to give each club its rating) and the draw files `model/draw_ucl.py` and `model/draw_uecl.py` (to find each club's country).

How each line works: [`code/names_code.md`](code/names_code.md).

---

## 6. What can go wrong

- **Try 4 can pick the wrong club.** Two different clubs with a long word in common ("Racing **Casablanca**" and "Raja **Casablanca**") look alike letter by letter. The check "clearly ahead of the second" does not help when the wrong club is the only close one.
- **A missing club plays at 1500.** For a big club that is a large mistake (Paris Saint-Germain is rated about 1850). The warning is shown, but the simulation still runs.
- **The little words are removed from every name.** "As", "de", "if" and "1899" are removed everywhere. No problem today, but a future club whose name is only made of such words would be cleaned into nothing.

Today, tries 3 and 4 are never needed for the clubs that come with the app: every club is found by try 1 or try 2. They are a safety net for clubs a user adds or renames in the app.

### Known bugs

- **Fixed in 1.1.0: a misspelt alias failed silently.** The alias itself is now searched first, then the club's name, and the result is labelled `alias-normalised` or `alias-fuzzy`; the simulation adds a warning that says the alias needs fixing.
- **Fixed in 1.1.0: one useless alias** ("Bodo/Glimt" pointing to itself) is removed. Seven aliases are added for the 2025/26 templates, among them "Newcastle United": the fuzzy score against "Newcastle" is only 0.72, so Newcastle used to start at the default 1500.

---

## 7. Ideas for later

- **Use ID numbers instead of names.** The football data website gives every club a number. If the pots stored that number too, no name matching would be needed at all, because numbers are never spelt two ways.
- **Check the country before accepting try 4.** A club from Morocco should not be matched with a club from Spain.
- **Ask the user.** When a club is missing, the app could show the three closest names and let the user pick.

---

## 8. Words to know

| Word | Meaning |
|---|---|
| pot | one of the lists of clubs used for the draw |
| rating | one number for a club's strength (see [`elo.md`](elo.md)) |
| alias | another name for the same thing |
| cleaning (normalising) | rewriting names in one simple form so small differences disappear |
| similarity score | a number from 0 to 1 that says how alike two names look |


---
---

# Correspondance des noms : un club, deux orthographes

> Le même club est souvent écrit de deux façons différentes dans ce projet. Cette partie comprend que « Bayern Munich » et « Bayern München » sont le même club, pour que chaque club du tirage reçoive sa note de force.

## En bref

- **Ce qui entre :** les noms des clubs des chapeaux (les listes du tirage) et les noms des clubs du fichier de notes.
- **Ce qui sort :** pour chaque club des chapeaux, le nom correspondant dans le fichier de notes, et la façon dont il a été trouvé.
- **Où c'est utilisé :** au début de chaque simulation, pour donner sa note à chaque club.
- **Code :** `model/names.py`. Explication ligne par ligne : [`code/names_code.md`](code/names_code.md).

---

## 1. Le problème

Le projet utilise deux listes de clubs écrites par des personnes différentes.

- **Les chapeaux** (les listes du tirage) utilisent les noms que les supporters connaissent : « Bayern Munich », « Inter Milan », « Brest ».
- **Le fichier de notes** vient d'un site de données sur le football. Il utilise d'autres noms : « Bayern München », « Inter », « Stade Brestois 29 ».

Un ordinateur est très strict. Pour lui, « Bayern Munich » et « Bayern München » sont deux textes différents, donc il croirait que le Bayern n'a pas de note du tout.

Imaginez une école avec deux listes de classe. Un professeur a écrit « Mo Salah », l'autre « Mohamed Salah ». Une personne voit tout de suite que c'est le même élève. Un ordinateur a besoin de règles pour le voir.

Cette partie du code est le seul endroit du projet où les deux orthographes se rencontrent.

---

## 2. Comment ça marche : quatre essais, dans l'ordre

Pour chaque club des chapeaux, le code essaie quatre choses, l'une après l'autre. Dès que l'une marche, il s'arrête.

### Essai 1 : exactement le même nom

Le nom est-il écrit exactement de la même façon dans le fichier de notes ?

- « Real Madrid » dans les chapeaux, « Real Madrid » dans le fichier : trouvé.

La plupart des clubs sont trouvés ici. En Ligue des champions, 27 clubs sur 36.

### Essai 2 : une liste écrite à la main

Certains noms n'ont rien en commun. « Red Star Belgrade » (anglais) et « FK Crvena Zvezda » (serbe) n'ont pas un seul mot en commun. Aucune règle ne pourrait deviner que c'est le même club.

Le code garde donc une petite liste, écrite à la main, de paires qui désignent le même club. On l'appelle la **liste d'alias** (un alias est un autre nom pour la même chose). Elle contient 18 paires, par exemple :

| Dans les chapeaux | Dans le fichier de notes |
|---|---|
| Bayern Munich | Bayern München |
| Inter Milan | Inter |
| Red Star Belgrade | FK Crvena Zvezda |
| Brest | Stade Brestois 29 |
| Sparta Prague | Sparta Praha |

Si un club est dans cette liste, le code fait confiance à la liste et s'arrête.

### Essai 3 : nettoyer les deux noms, puis comparer

Beaucoup de différences ne sont que du « bruit » : majuscules, accents, tirets, et petits mots comme « FC » qui ne disent pas de quel club il s'agit. Le code nettoie donc chaque nom :

1. Enlever les accents des lettres : « é » devient « e ».
2. Tout écrire en minuscules.
3. Transformer les tirets, points et barres obliques en espaces.
4. Enlever les petits mots que tous les clubs utilisent, comme « FC », « AC », « SC », « Club ».

| Avant le nettoyage | Après le nettoyage |
|---|---|
| Atlético Madrid | atletico madrid |
| FC Porto | porto |
| Paris Saint-Germain | paris saint germain |
| 1. FC Heidenheim | heidenheim |
| AC Milan | milan |
| Bodo/Glimt | bodo glimt |

Maintenant « Porto » et « FC Porto » deviennent tous les deux « porto ». Même texte, donc c'est une correspondance.

### Essai 4 : « ce nom ressemble beaucoup »

Si rien n'a encore marché, le code compare le nom nettoyé aux 984 noms du fichier de notes et donne à chacun un **score de ressemblance** :

- 1 veut dire « exactement les mêmes lettres, dans le même ordre » ;
- 0 veut dire « rien en commun ».

Le score compte combien de lettres les deux noms partagent, dans le même ordre, par rapport à leur longueur totale.

| Nom des chapeaux | Nom le plus proche dans le fichier | Score |
|---|---|---|
| man city | manchester city | 0.70 |
| racing casablanca | raja casablanca | 0.81 |

Le code n'accepte le nom le plus proche que si **les deux** conditions sont vraies :

- le score vaut au moins **0.80** (les noms se ressemblent vraiment) ;
- le nom le plus proche a au moins **0.05** d'avance sur le deuxième (il y a un vrai gagnant, pas deux noms qui se ressemblent autant).

Pourquoi autant de prudence ? Parce qu'une fausse correspondance est pire que pas de correspondance. Si « Racing » recevait la note de « Raja », la simulation jouerait le mauvais club et personne ne le verrait.

### Si les quatre essais échouent

Le club n'est pas retiré. Il commence la simulation avec une note moyenne de **1500**, et l'appli affiche un avertissement : « not found in the Elo file, starting at 1500 ». Comme ça, un club manquant se voit toujours.

---

## 3. Un exemple complet

Imaginez que le fichier de notes ne contienne que quatre noms : « Bayern München », « FC Copenhagen », « Real Madrid », « FC Porto ». Voici ce qui arrive à cinq clubs des chapeaux :

| Club des chapeaux | Essai 1 : exact | Essai 2 : alias | Essai 3 : nettoyé | Résultat |
|---|---|---|---|---|
| Real Madrid | trouvé | | | « Real Madrid » |
| Bayern Munich | non | trouvé : « Bayern München » | | « Bayern München » |
| Copenhagen | non | pas dans la liste | « copenhagen » = « copenhagen » | « FC Copenhagen » |
| Porto | non | pas dans la liste | « porto » = « porto » | « FC Porto » |
| Zzz United | non | non | non, et l'essai 4 ne trouve rien de proche | manquant, commence à 1500 |

---

## 4. À essayer en Python

Ce petit programme fait les mêmes quatre essais, avec seulement les outils fournis avec Python. Vous pouvez le copier et le lancer.

```python
import difflib
import re
import unicodedata

ALIASES = {"Bayern Munich": "Bayern München"}
LITTLE_WORDS = {"fc", "ac", "sc", "club"}

def clean(name):
    text = unicodedata.normalize("NFKD", name)                         # sépare "é" en "e" + accent
    text = "".join(ch for ch in text if not unicodedata.combining(ch))  # enlève les accents
    text = re.sub(r"[^a-z0-9 ]+", " ", text.lower())                    # minuscules, pas de symboles
    return " ".join(w for w in text.split() if w not in LITTLE_WORDS)

def find(club, file_names):
    if club in file_names:                                    # essai 1
        return club, "exact"
    if ALIASES.get(club) in file_names:                       # essai 2
        return ALIASES[club], "alias"
    cleaned = {clean(n): n for n in file_names}
    if clean(club) in cleaned:                                # essai 3
        return cleaned[clean(club)], "cleaned"
    scores = sorted(((difflib.SequenceMatcher(None, clean(club), c).ratio(), n)
                     for c, n in cleaned.items()), reverse=True)
    best, second = scores[0][0], scores[1][0]
    if best >= 0.80 and best - second >= 0.05:                # essai 4
        return scores[0][1], f"close ({best:.2f})"
    return None, "missing"

file_names = ["Bayern München", "FC Porto", "Real Madrid", "Raja Casablanca"]
for club in ["Real Madrid", "Bayern Munich", "Porto", "Racing Casablanca", "Man City"]:
    print(club, "->", find(club, file_names))
```

Résultat :

```
Real Madrid -> ('Real Madrid', 'exact')
Bayern Munich -> ('Bayern München', 'alias')
Porto -> ('FC Porto', 'cleaned')
Racing Casablanca -> ('Raja Casablanca', 'close (0.81)')
Man City -> (None, 'missing')
```

Regardez « Racing Casablanca » : il a été relié à « Raja Casablanca », qui est un **autre club**. C'est le point faible de l'essai 4 (section 6).

---

## 5. Ce que le code utilise

### Modules Python

Les trois sont fournis avec Python ; rien à installer.

| Module | Ce que c'est | Ce qu'il fait ici |
|---|---|---|
| `unicodedata` | connaît toutes les lettres de tous les alphabets | enlève les accents (« é » en « e », « ş » en « s ») |
| `re` | les « expressions régulières » : des modèles pour trouver et remplacer du texte | remplace chaque tiret, point, barre oblique et symbole par une espace |
| `difflib` | compare deux textes | donne le score de ressemblance de l'essai 4 (`SequenceMatcher`) |

### Fonctions de `model/names.py`

| Fonction | En une ligne |
|---|---|
| `normalise` | nettoie un nom (essai 3) |
| `resolve` | fait les quatre essais pour un club |
| `build_index` | nettoie une seule fois les 984 noms du fichier de notes, pour ne pas les nettoyer à nouveau pour chaque club |
| `resolve_all` | lance `resolve` pour chaque club des chapeaux |
| `Resolution` | une petite fiche : le club, le nom trouvé, et l'essai qui l'a trouvé |

Deux autres parties du projet l'utilisent : `model/simulation.py` (pour donner sa note à chaque club) et les fichiers du tirage `model/draw_ucl.py` et `model/draw_uecl.py` (pour trouver le pays de chaque club).

Comment marche chaque ligne : [`code/names_code.md`](code/names_code.md).

---

## 6. Ce qui peut mal tourner

- **L'essai 4 peut choisir le mauvais club.** Deux clubs différents avec un long mot en commun (« Racing **Casablanca** » et « Raja **Casablanca** ») se ressemblent lettre par lettre. La vérification « nettement devant le deuxième » n'aide pas quand le mauvais club est le seul proche.
- **Un club manquant joue à 1500.** Pour un grand club, c'est une grosse erreur (le Paris Saint-Germain a une note d'environ 1850). L'avertissement s'affiche, mais la simulation tourne quand même.
- **Les petits mots sont retirés de tous les noms.** « As », « de », « if » et « 1899 » sont retirés partout. Pas de souci aujourd'hui, mais un futur club dont le nom ne contiendrait que ces mots serait nettoyé en rien du tout.

Aujourd'hui, les essais 3 et 4 ne servent jamais pour les clubs fournis avec l'appli : chaque club est trouvé par l'essai 1 ou l'essai 2. Ce sont des filets de sécurité pour les clubs qu'un utilisateur ajoute ou renomme dans l'appli.

### Bugs connus

- **Corrigé en 1.1.0 : un alias mal écrit échouait sans bruit.** L'alias lui-même est maintenant cherché en premier, puis le nom du club, et le résultat est étiqueté `alias-normalised` ou `alias-fuzzy` ; la simulation ajoute un avertissement qui dit que l'alias est à corriger.
- **Corrigé en 1.1.0 : un alias inutile** (« Bodo/Glimt » qui pointait vers lui-même) est retiré. Sept alias sont ajoutés pour les modèles 2025/26, dont « Newcastle United » : son score de ressemblance avec « Newcastle » n'est que de 0.72, donc Newcastle partait à la note par défaut de 1500.

---

## 7. Idées pour plus tard

- **Utiliser des numéros au lieu des noms.** Le site de données donne un numéro à chaque club. Si les chapeaux gardaient aussi ce numéro, il n'y aurait plus besoin de comparer des noms, car un numéro ne s'écrit jamais de deux façons.
- **Vérifier le pays avant d'accepter l'essai 4.** Un club marocain ne devrait pas être relié à un club espagnol.
- **Demander à l'utilisateur.** Quand un club manque, l'appli pourrait montrer les trois noms les plus proches et laisser l'utilisateur choisir.

---

## 8. Mots à connaître

| Mot | Sens |
|---|---|
| chapeau | une des listes de clubs utilisées pour le tirage |
| note | un nombre qui mesure la force d'un club (voir [`elo.md`](elo.md)) |
| alias | un autre nom pour la même chose |
| nettoyage (normalisation) | réécrire les noms sous une forme simple pour que les petites différences disparaissent |
| score de ressemblance | un nombre de 0 à 1 qui dit à quel point deux noms se ressemblent |

----