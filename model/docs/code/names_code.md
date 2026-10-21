# `names.py`, line by line

> This page walks through the code of `model/names.py`, a few lines at a time. For the idea behind it (why two spellings exist, the four tries), read [`../names.md`](../names.md) first.

*Version française : [plus bas](#namespy-ligne-par-ligne).*

## How to read this page

- Each function starts with its **arguments**: what comes in, and what type it is.
- Then the code comes in small groups of 2 to 4 lines. Under each group, a few bullets say what the lines do, why they are written that way, and what general idea they are an example of.
- Each function ends with **In one line**: what goes in and what comes out.

---

## The imports

```python
import difflib
import re
import unicodedata
```

- `difflib` (comes with Python) compares two pieces of text; only its `SequenceMatcher` class is used, in `resolve`, to give the similarity score of try 4.
- `re` (comes with Python) finds and replaces text that follows a pattern; it is used once, in `normalise`, to turn every symbol into a space.
- `unicodedata` (comes with Python) knows the details of every letter, including which "letters" are really accents; `normalise` uses it to take accents off.
- No outside package is needed, so this file works on any computer with Python, even without pandas or scikit-learn.

---

## The settings at the top

```python
ALIASES = {
    "Bayern Munich": "Bayern München",
    "Inter Milan": "Inter",
    ...
}
```

- A **dictionary** (`dict`): each key is a name as written in the pots, each value is the same club as written in the ratings file.
- It holds the pairs no rule could ever find, such as "Red Star Belgrade" and "FK Crvena Zvezda", which share no word.
- Looking a name up in a dictionary is instant, whatever its size, because Python finds keys by a computed address (a **hash lookup**), not by reading the list from the top.

| Code | Does | Example value |
|---|---|---|
| `_FILLER = {"fc", "cf", "sc", ...}` | a **set** of little words that never tell clubs apart | `"fc" in _FILLER` is `True` |
| `FUZZY_MIN = 0.80` | the lowest similarity score accepted by try 4 | 0.81 passes, 0.70 fails |
| `FUZZY_GAP = 0.05` | how far ahead of the second-best name the best one must be | 0.85 against 0.83: refused |

- The underscore in `_FILLER` is a Python habit meaning "for use inside this file only".
- A set, like a dictionary, answers "is this word inside?" instantly, which matters because the question is asked for every word of every name.

---

## `normalise(name)`: clean a name

**Arguments:** `name`: any value, usually a `str`, the club name to clean.

```python
def normalise(name):
    text = unicodedata.normalize("NFKD", str(name))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
```

- `str(name)` turns the input into text first, so the function never crashes if it receives a number or `None` by mistake.
- `unicodedata.normalize("NFKD", ...)` splits each accented letter into two characters: the plain letter, then the accent on its own. `"é"` becomes `"e"` followed by an invisible accent mark. `text: "Atlético" -> "Atle´tico"` (the accent is now separate).
- The second line rebuilds the text keeping only characters that are not accents (`unicodedata.combining(ch)` is true for an accent). `text: "Atle´tico" -> "Atletico"`.
- `"".join(... for ch in text if ...)` is a **generator expression** inside `join`: it walks through the characters one by one, keeps some, and glues them back together without building a list first.
- This trick removes accents from every alphabet at once ("é", "ü", "ş", "ø"), with no hand-made table of letters.

```python
    text = re.sub(r"[^a-z0-9 ]+", " ", text.lower())
    words = [w for w in text.split() if w not in _FILLER]
    return " ".join(words) or text.strip()
```

- `text.lower()` writes everything in small letters, then `re.sub` replaces every run of characters that is not a small letter, a digit or a space with one space. `r"[^a-z0-9 ]+"` reads "one or more characters that are NOT a to z, 0 to 9 or space". `"paris saint-germain" -> "paris saint germain"`.
- `text.split()` cuts the text into words (and ignores double spaces); the **list comprehension** keeps the words that are not in `_FILLER`. `"fc porto" -> ["porto"]`.
- `" ".join(words)` glues the words back with single spaces.
- `or text.strip()` is a safety net: if every word was a filler word, `" ".join([])` is the empty string `""`, which Python treats as false, so the cleaned text is returned instead. This stops two very different clubs from both becoming `""`.

**In one line:** takes any club name and returns it in small letters, without accents, symbols or filler words: `"FC Porto" -> "porto"`.

---

## `Resolution`: a small record of one match

**Arguments:** `club`: `str`, the name in the pots. `key`: `str` or `None`, the name found in the ratings file. `how`: `str`, which try found it (`"exact"`, `"alias"`, `"normalised"`, `"fuzzy"` or `"missing"`). `score`: `float`, the similarity score, 1.0 unless try 4 was used.

```python
class Resolution:
    __slots__ = ("club", "key", "how", "score")

    def __init__(self, club, key, how, score=1.0):
```

- A **class** used only as a container of four values: a record. It has no real behaviour.
- `__slots__` fixes the list of allowed attributes. Two benefits: each object takes less memory, and a typing mistake such as `r.socre = 0.5` raises an error instead of quietly creating a new attribute.
- `score=1.0` is a **default value**: callers only pass it for try 4, the only try that is not certain.

```python
    def __repr__(self):
        return f"Resolution({self.club!r} -> {self.key!r}, {self.how}, {self.score:.2f})"
```

- `__repr__` decides what Python prints when you print the object; without it you would see something like `<Resolution object at 0x7f...>`.
- `!r` puts quotes around the names, so `None` and `'None'` cannot be confused; `:.2f` shows the score with two decimals.
- Its purpose is the expert log: every match can be read by a person, for example `Resolution('Bayern Munich' -> 'Bayern München', alias, 1.00)`.

**In one line:** stores how one club was found, so the result can be checked by eye.

---

## `resolve(club, keys, _norm_index=None)`: the four tries for one club

**Arguments:** `club`: `str`, a name from the pots. `keys`: a collection of `str` (here the 984 names of the ratings file). `_norm_index`: `dict` or `None`, the cleaned names already prepared by `build_index`, so they are not cleaned again.

```python
    if club in keys:
        return Resolution(club, club, "exact")
    alias = ALIASES.get(club)
    if alias is not None and alias in keys:
        return Resolution(club, alias, "alias")
```

- Try 1: `club in keys` checks for the exact same text. On success the function stops at once with `return`: this pattern is called an **early return**, and it keeps the cheap, certain checks first.
- Try 2: `ALIASES.get(club)` returns the hand-written partner, or `None` if there is none; unlike `ALIASES[club]`, `get` never crashes on a missing key.
- `alias in keys` makes sure the alias really exists in the ratings file before trusting it. If it does not (a typing mistake in the list), the code silently falls through to try 3: that is the known bug described in [`../names.md`](../names.md), section 6.

```python
    index = _norm_index if _norm_index is not None else build_index(keys)
    wanted = normalise(club)
    hit = index.get(wanted)
    if hit is not None:
        return Resolution(club, hit, "normalised")
```

- The first line reuses the prepared index if one was given, and builds it otherwise. Cleaning 984 names takes time, so `resolve_all` builds it once and passes it to every call: this is **caching**, keeping a result to reuse it.
- `wanted` is the cleaned pot name. `index` maps each cleaned file name back to its original spelling: `{"porto": "FC Porto", ...}`.
- `index.get(wanted)` is try 3: one instant dictionary lookup instead of comparing with 984 names one by one. `wanted: "porto" -> hit: "FC Porto"`.

```python
    scored = sorted(((difflib.SequenceMatcher(None, wanted, norm).ratio(), key)
                     for norm, key in index.items()), reverse=True)
```

- Try 4 starts here. For every cleaned file name, `SequenceMatcher(None, wanted, norm).ratio()` gives a similarity score from 0 to 1. The first argument `None` means "no characters to ignore".
- Each score is paired with the original name in a **tuple** `(score, name)`, and `sorted(..., reverse=True)` puts the highest score first. Python sorts tuples by their first item, so the order is by score.
- This compares the name with all 984 names: the slowest step of the file, which is why it is the last try.
- The code does not use the shortcut `difflib.get_close_matches`, because that function hides the score of the second-best name, and the next lines need it.

```python
    if scored and scored[0][0] >= FUZZY_MIN:
        best_score, best_key = scored[0]
        second = scored[1][0] if len(scored) > 1 else 0.0
        if best_score - second >= FUZZY_GAP:
            return Resolution(club, best_key, "fuzzy", best_score)
    return Resolution(club, None, "missing", 0.0)
```

- `scored and ...` first checks the list is not empty (an empty list counts as false), then that the best score reaches 0.80.
- `best_score, best_key = scored[0]` is **unpacking**: the two items of the tuple go into two names in one line.
- The gap test refuses a near tie: with 0.85 and 0.83 the gap is 0.02, below 0.05, so no guess is made. `second` falls back to 0.0 if there is only one name to compare with.
- If any test fails, the last line records the club as missing with `key=None`. The caller then gives it the default rating of 1500 and shows a warning.

**In one line:** takes one pot name and the file's names, and returns a `Resolution` saying which file name matches it and how, or that none does.

---

## `build_index(keys)`: clean every file name once

**Arguments:** `keys`: a collection of `str`, the names of the ratings file.

```python
def build_index(keys):
    index = {}
    for key in keys:
        index.setdefault(normalise(key), key)
    return index
```

- This is the **accumulator pattern**: start with an empty dictionary, fill it in a loop, return it. `index: {} -> {"bayern munchen": "Bayern München", "porto": "FC Porto", ...}`.
- `setdefault(k, v)` only writes `v` if `k` is not already there. So if two file names clean into the same text, the first one is kept and the second does not silently replace it.
- On the real file, no two of the 984 names clean into the same text, so this rule never fires today; it is a guard for the future.

**In one line:** turns a list of names into a dictionary from cleaned name to original name.

---

## `resolve_all(clubs, keys)`: every club at once

**Arguments:** `clubs`: `list` of `str`, the pot names. `keys`: the names of the ratings file.

```python
def resolve_all(clubs, keys):
    index = build_index(keys)
    return [resolve(club, keys, index) for club in clubs]
```

- Builds the index of cleaned names **once**, then passes it to every call of `resolve`. Without this, the 984 names would be cleaned again for each of the 36 clubs.
- The list comprehension keeps the order of `clubs`, so result number 5 always belongs to club number 5.
- It returns the full `Resolution` records, not just the ratings: `model/simulation.py` uses them to warn about missing clubs, and the expert log prints how each club was found.

**In one line:** takes all pot names and returns one `Resolution` per club, in the same order.

---
---

# `names.py`, ligne par ligne

> Cette page explique le code de `model/names.py`, quelques lignes à la fois. Pour l'idée générale (pourquoi deux orthographes existent, les quatre essais), lis d'abord [`../names.md`](../names.md#correspondance-des-noms--un-club-deux-orthographes).

## Comment lire cette page

- Chaque fonction commence par ses **arguments** : ce qui entre, et de quel type.
- Ensuite le code vient en petits groupes de 2 à 4 lignes. Sous chaque groupe, quelques points disent ce que font les lignes, pourquoi elles sont écrites ainsi, et de quelle idée générale elles sont un exemple.
- Chaque fonction se termine par **En une ligne** : ce qui entre et ce qui sort.

---

## Les imports

```python
import difflib
import re
import unicodedata
```

- `difflib` (fourni avec Python) compare deux textes ; seule sa classe `SequenceMatcher` est utilisée, dans `resolve`, pour donner le score de ressemblance de l'essai 4.
- `re` (fourni avec Python) trouve et remplace du texte qui suit un modèle ; il sert une fois, dans `normalise`, pour transformer chaque symbole en espace.
- `unicodedata` (fourni avec Python) connaît le détail de chaque lettre, y compris quels « caractères » sont en fait des accents ; `normalise` s'en sert pour enlever les accents.
- Aucun paquet extérieur n'est nécessaire, donc ce fichier marche sur tout ordinateur avec Python, même sans pandas ni scikit-learn.

---

## Les réglages en haut du fichier

```python
ALIASES = {
    "Bayern Munich": "Bayern München",
    "Inter Milan": "Inter",
    ...
}
```

- Un **dictionnaire** (`dict`) : chaque clé est un nom écrit comme dans les chapeaux, chaque valeur est le même club écrit comme dans le fichier de notes.
- Il contient les paires qu'aucune règle ne pourrait trouver, comme « Red Star Belgrade » et « FK Crvena Zvezda », qui n'ont aucun mot en commun.
- Chercher un nom dans un dictionnaire est immédiat, quelle que soit sa taille, car Python trouve les clés par une adresse calculée (une **recherche par hachage**), pas en lisant la liste depuis le début.

| Code | Fait | Exemple |
|---|---|---|
| `_FILLER = {"fc", "cf", "sc", ...}` | un **ensemble** (`set`) de petits mots qui ne distinguent jamais les clubs | `"fc" in _FILLER` vaut `True` |
| `FUZZY_MIN = 0.80` | le plus petit score de ressemblance accepté par l'essai 4 | 0.81 passe, 0.70 échoue |
| `FUZZY_GAP = 0.05` | l'avance que le meilleur nom doit avoir sur le deuxième | 0.85 contre 0.83 : refusé |

- Le tiret bas dans `_FILLER` est une habitude Python qui veut dire « à utiliser seulement dans ce fichier ».
- Un ensemble, comme un dictionnaire, répond tout de suite à « ce mot est-il dedans ? », ce qui compte car la question est posée pour chaque mot de chaque nom.

---

## `normalise(name)` : nettoyer un nom

**Arguments :** `name` : n'importe quelle valeur, en général un `str`, le nom du club à nettoyer.

```python
def normalise(name):
    text = unicodedata.normalize("NFKD", str(name))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
```

- `str(name)` transforme d'abord l'entrée en texte, pour que la fonction ne plante jamais si elle reçoit un nombre ou `None` par erreur.
- `unicodedata.normalize("NFKD", ...)` sépare chaque lettre accentuée en deux caractères : la lettre simple, puis l'accent tout seul. `"é"` devient `"e"` suivi d'une marque d'accent invisible. `text : "Atlético" -> "Atle´tico"` (l'accent est maintenant à part).
- La deuxième ligne reconstruit le texte en ne gardant que les caractères qui ne sont pas des accents (`unicodedata.combining(ch)` est vrai pour un accent). `text : "Atle´tico" -> "Atletico"`.
- `"".join(... for ch in text if ...)` est une **expression génératrice** dans `join` : elle parcourt les caractères un par un, en garde certains, et les recolle sans construire de liste avant.
- Cette astuce enlève les accents de tous les alphabets d'un coup (« é », « ü », « ş », « ø »), sans table de lettres faite à la main.

```python
    text = re.sub(r"[^a-z0-9 ]+", " ", text.lower())
    words = [w for w in text.split() if w not in _FILLER]
    return " ".join(words) or text.strip()
```

- `text.lower()` écrit tout en minuscules, puis `re.sub` remplace chaque suite de caractères qui n'est ni une minuscule, ni un chiffre, ni une espace par une seule espace. `r"[^a-z0-9 ]+"` se lit « un ou plusieurs caractères qui ne sont PAS de a à z, de 0 à 9 ou une espace ». `"paris saint-germain" -> "paris saint germain"`.
- `text.split()` coupe le texte en mots (et ignore les espaces doubles) ; la **liste en compréhension** garde les mots qui ne sont pas dans `_FILLER`. `"fc porto" -> ["porto"]`.
- `" ".join(words)` recolle les mots avec une seule espace.
- `or text.strip()` est un filet de sécurité : si tous les mots étaient des petits mots, `" ".join([])` donne le texte vide `""`, que Python considère comme faux, donc c'est le texte nettoyé qui est renvoyé. Cela empêche deux clubs très différents de devenir tous les deux `""`.

**En une ligne :** prend n'importe quel nom de club et le renvoie en minuscules, sans accents, symboles ni petits mots : `"FC Porto" -> "porto"`.

---

## `Resolution` : une petite fiche pour une correspondance

**Arguments :** `club` : `str`, le nom dans les chapeaux. `key` : `str` ou `None`, le nom trouvé dans le fichier de notes. `how` : `str`, l'essai qui l'a trouvé (`"exact"`, `"alias"`, `"normalised"`, `"fuzzy"` ou `"missing"`). `score` : `float`, le score de ressemblance, 1.0 sauf pour l'essai 4.

```python
class Resolution:
    __slots__ = ("club", "key", "how", "score")

    def __init__(self, club, key, how, score=1.0):
```

- Une **classe** utilisée seulement comme boîte à quatre valeurs : une fiche. Elle n'a pas de vrai comportement.
- `__slots__` fixe la liste des attributs permis. Deux avantages : chaque objet prend moins de mémoire, et une faute de frappe comme `r.socre = 0.5` provoque une erreur au lieu de créer en silence un nouvel attribut.
- `score=1.0` est une **valeur par défaut** : on ne la donne que pour l'essai 4, le seul qui n'est pas certain.

```python
    def __repr__(self):
        return f"Resolution({self.club!r} -> {self.key!r}, {self.how}, {self.score:.2f})"
```

- `__repr__` décide de ce que Python affiche quand on affiche l'objet ; sans lui, on verrait quelque chose comme `<Resolution object at 0x7f...>`.
- `!r` met des guillemets autour des noms, pour qu'on ne confonde pas `None` et `'None'` ; `:.2f` affiche le score avec deux décimales.
- Son but est le journal expert : chaque correspondance peut être lue par une personne, par exemple `Resolution('Bayern Munich' -> 'Bayern München', alias, 1.00)`.

**En une ligne :** garde la façon dont un club a été trouvé, pour que le résultat puisse être vérifié à l'œil.

---

## `resolve(club, keys, _norm_index=None)` : les quatre essais pour un club

**Arguments :** `club` : `str`, un nom des chapeaux. `keys` : une collection de `str` (ici les 984 noms du fichier de notes). `_norm_index` : `dict` ou `None`, les noms nettoyés déjà préparés par `build_index`, pour ne pas les nettoyer à nouveau.

```python
    if club in keys:
        return Resolution(club, club, "exact")
    alias = ALIASES.get(club)
    if alias is not None and alias in keys:
        return Resolution(club, alias, "alias")
```

- Essai 1 : `club in keys` cherche exactement le même texte. En cas de succès, la fonction s'arrête tout de suite avec `return` : ce schéma s'appelle un **retour anticipé**, et il place en premier les vérifications rapides et sûres.
- Essai 2 : `ALIASES.get(club)` renvoie le partenaire écrit à la main, ou `None` s'il n'y en a pas ; contrairement à `ALIASES[club]`, `get` ne plante jamais sur une clé absente.
- `alias in keys` vérifie que l'alias existe vraiment dans le fichier de notes avant de lui faire confiance. Sinon (une faute de frappe dans la liste), le code passe en silence à l'essai 3 : c'est le bug connu décrit dans [`../names.md`](../names.md), section 6.

```python
    index = _norm_index if _norm_index is not None else build_index(keys)
    wanted = normalise(club)
    hit = index.get(wanted)
    if hit is not None:
        return Resolution(club, hit, "normalised")
```

- La première ligne réutilise l'index préparé s'il a été donné, et le construit sinon. Nettoyer 984 noms prend du temps, donc `resolve_all` le construit une fois et le passe à chaque appel : c'est de la **mise en cache**, garder un résultat pour le réutiliser.
- `wanted` est le nom du chapeau nettoyé. `index` relie chaque nom nettoyé du fichier à son orthographe d'origine : `{"porto": "FC Porto", ...}`.
- `index.get(wanted)` est l'essai 3 : une seule recherche immédiate dans le dictionnaire au lieu de comparer avec 984 noms un par un. `wanted : "porto" -> hit : "FC Porto"`.

```python
    scored = sorted(((difflib.SequenceMatcher(None, wanted, norm).ratio(), key)
                     for norm, key in index.items()), reverse=True)
```

- L'essai 4 commence ici. Pour chaque nom nettoyé du fichier, `SequenceMatcher(None, wanted, norm).ratio()` donne un score de ressemblance de 0 à 1. Le premier argument `None` veut dire « aucun caractère à ignorer ».
- Chaque score est associé au nom d'origine dans un **tuple** `(score, nom)`, et `sorted(..., reverse=True)` met le plus grand score en premier. Python trie les tuples selon leur premier élément, donc l'ordre suit le score.
- Cela compare le nom avec les 984 noms : l'étape la plus lente du fichier, c'est pourquoi c'est le dernier essai.
- Le code n'utilise pas le raccourci `difflib.get_close_matches`, car cette fonction cache le score du deuxième meilleur nom, dont les lignes suivantes ont besoin.

```python
    if scored and scored[0][0] >= FUZZY_MIN:
        best_score, best_key = scored[0]
        second = scored[1][0] if len(scored) > 1 else 0.0
        if best_score - second >= FUZZY_GAP:
            return Resolution(club, best_key, "fuzzy", best_score)
    return Resolution(club, None, "missing", 0.0)
```

- `scored and ...` vérifie d'abord que la liste n'est pas vide (une liste vide compte comme faux), puis que le meilleur score atteint 0.80.
- `best_score, best_key = scored[0]` est un **déballage** : les deux éléments du tuple vont dans deux noms en une ligne.
- Le test d'avance refuse une quasi-égalité : avec 0.85 et 0.83, l'écart est 0.02, sous 0.05, donc aucune supposition. `second` vaut 0.0 s'il n'y a qu'un seul nom à comparer.
- Si un test échoue, la dernière ligne note le club comme manquant avec `key=None`. L'appelant lui donne alors la note par défaut de 1500 et affiche un avertissement.

**En une ligne :** prend un nom des chapeaux et les noms du fichier, et renvoie une `Resolution` qui dit quel nom du fichier lui correspond et comment, ou qu'aucun ne correspond.

---

## `build_index(keys)` : nettoyer chaque nom du fichier une seule fois

**Arguments :** `keys` : une collection de `str`, les noms du fichier de notes.

```python
def build_index(keys):
    index = {}
    for key in keys:
        index.setdefault(normalise(key), key)
    return index
```

- C'est le **schéma de l'accumulateur** : partir d'un dictionnaire vide, le remplir dans une boucle, le renvoyer. `index : {} -> {"bayern munchen": "Bayern München", "porto": "FC Porto", ...}`.
- `setdefault(k, v)` n'écrit `v` que si `k` n'est pas déjà là. Donc si deux noms du fichier deviennent le même texte une fois nettoyés, le premier est gardé et le second ne le remplace pas en silence.
- Dans le vrai fichier, aucun des 984 noms ne donne le même texte nettoyé qu'un autre, donc cette règle ne sert jamais aujourd'hui ; c'est une protection pour l'avenir.

**En une ligne :** transforme une liste de noms en dictionnaire « nom nettoyé vers nom d'origine ».

---

## `resolve_all(clubs, keys)` : tous les clubs d'un coup

**Arguments :** `clubs` : `list` de `str`, les noms des chapeaux. `keys` : les noms du fichier de notes.

```python
def resolve_all(clubs, keys):
    index = build_index(keys)
    return [resolve(club, keys, index) for club in clubs]
```

- Construit l'index des noms nettoyés **une seule fois**, puis le passe à chaque appel de `resolve`. Sans cela, les 984 noms seraient nettoyés à nouveau pour chacun des 36 clubs.
- La liste en compréhension garde l'ordre de `clubs`, donc le résultat numéro 5 appartient toujours au club numéro 5.
- Elle renvoie les fiches `Resolution` complètes, pas seulement les notes : `model/simulation.py` s'en sert pour signaler les clubs manquants, et le journal expert affiche comment chaque club a été trouvé.

**En une ligne :** prend tous les noms des chapeaux et renvoie une `Resolution` par club, dans le même ordre.
