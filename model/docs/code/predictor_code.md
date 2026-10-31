# `predictor.py`, line by line

> This page walks through the code of the match model. For the idea (standardised gap, three judges, softmax, training), read [`../logistic_regression.md`](../logistic_regression.md) first.

*Version française : [plus bas](#predictorpy-ligne-par-ligne).*

## How to read this page

- Each function starts with its **arguments**.
- The code comes in groups of 2 to 4 lines, each followed by bullets: what, why, and which general idea.
- Each function ends with **In one line**.

The file has two halves that never mix: `train` (needs scikit-learn, run once) and `MatchModel` (needs only `math`, run before every simulated match).

---

## The imports and settings

```python
import json
import math
import sys
from datetime import datetime
from pathlib import Path
```

- Only modules that come with Python are imported at the top: `json` reads and writes the 8 numbers, `math` gives `exp` for softmax, `sys` reads `--train`, `datetime` stamps the training date, `Path` builds file paths.
- scikit-learn, pandas and numpy are **not** imported here, on purpose: they are imported inside `train` only. So `import model.predictor` works on a computer without them, and the app can run without installing them.

```python
CLASSES = (-1, 0, 1)                 # away win, draw, home win
CLASS_NAMES = {-1: "away", 0: "draw", 1: "home"}
```

- The three results as numbers, in the order scikit-learn sorts them (smallest first). The same order is used everywhere: away, draw, home.
- A **tuple** is used because this order must never change while the program runs; a tuple cannot be modified.

```python
class PredictorError(Exception):
    """The model cannot be used. The message says what to run."""
```

- A **custom exception**: a new kind of error that inherits from Python's `Exception`. Its body is only a docstring.
- Having its own name lets the interface catch exactly this problem (`except PredictorError`) and show a friendly message, without hiding other, unexpected errors.

---

## `train(features_csv, out_json, verbose)`: learn the 8 numbers

**Arguments:** `features_csv`: `Path`, the training data (`match_features.csv`). `out_json`: `Path`, where to save the numbers. `verbose`: `bool`, print a summary if `True`.

```python
    import numpy as np
    import pandas as pd
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import log_loss
```

- Imports **inside the function**: they only run when `train` is called. This is how the heavy libraries stay out of the app.
- `LogisticRegression` (scikit-learn) finds the slopes and starting values; `log_loss` (scikit-learn) computes the average surprise of [`../logistic_regression.md`](../logistic_regression.md), section 10. The next two imports, `Pipeline` and `StandardScaler`, come from scikit-learn too.

```python
    df = pd.read_csv(features_csv)
    df = df[df["target"].notna()].copy()
    if df.empty:
        raise PredictorError(f"no played match in {features_csv}")
```

- Reads the 5 328 rows, then keeps only the rows whose result is known (`notna()` is "not missing"): 5 251 rows.
- `.copy()` makes an independent table; without it, pandas may warn that later changes could affect the original table.
- If nothing is left, it stops with a clear error instead of crashing later with a confusing one: a **guard clause**.

```python
    X = (df["elo_home_before"] - df["elo_away_before"]).to_numpy().reshape(-1, 1)
    y = df["target"].astype(int).to_numpy()
```

- `X` is the input: one rating gap per match. `.reshape(-1, 1)` turns a flat list of 5 251 numbers into a table of 5 251 rows and 1 column, because scikit-learn always expects a table of inputs, even with a single input.
- `y` is the answer: −1, 0 or 1 per match. `.astype(int)` turns `1.0` into `1`, so the three classes are clean whole numbers.
- `X` and `y` are the usual names in machine learning: capital `X` for the table of inputs, small `y` for the answers.

```python
    def make():
        return Pipeline([("scaler", StandardScaler()),
                         ("lr", LogisticRegression(max_iter=1000))])
```

- A small **inner function** that builds a fresh, untrained model each time it is called. It is called twice: once for the exam, once for the final model.
- `Pipeline` (scikit-learn) chains two steps: `StandardScaler` measures the average and typical gap and standardises the input, then `LogisticRegression` learns the three score lines.
- `max_iter=1000` allows up to 1 000 steps down the bowl; about 6 are needed.

```python
    seasons = [int(s) for s in sorted(df["season"].unique())]
    if len(seasons) >= 2:
        last = seasons[-1]
        train_mask = (df["season"] < last).to_numpy()
```

- Lists the seasons in the data: `[2023, 2024, 2025]`.
- The plan: train on every season before the last one, and use the last one as the exam. `train_mask` is a list of `True`/`False`, one per match: `True` means "use this match for training".

```python
        if (~train_mask).sum() < 50 and len(seasons) >= 3:
            last = seasons[-2]
            train_mask = (df["season"] < last).to_numpy()
```

- `~` flips every `True`/`False`, so `(~train_mask).sum()` counts the exam matches. 2025 has only 5 matches, too few for an exam, so the code moves back one season.
- **Bug:** the exam becomes 2024, which holds 4 789 matches, and training keeps only the 457 matches of 2023. The exam is much bigger than the training set. The fix (split by date, 80 % / 20 %) is in [`../logistic_regression.md`](../logistic_regression.md), section 16.

```python
        pipe = make().fit(X[train_mask], y[train_mask])
        proba = pipe.predict_proba(X[~train_mask])
```

- `.fit` trains a fresh model on the training matches only. `X[train_mask]` keeps the rows where the mask is `True`: **boolean indexing**.
- `predict_proba` gives three chances for every exam match, which the model has never seen. This is the honest test.

```python
        freq = np.bincount(y[train_mask] + 1, minlength=3) / train_mask.sum()
        base = np.tile(freq, (int((~train_mask).sum()), 1))
```

- Builds the "know-nothing" forecast. `y + 1` turns −1, 0, 1 into 0, 1, 2; `np.bincount` counts how many of each; dividing by the number of matches gives the usual frequencies, for example `[0.34, 0.21, 0.46]`.
- `np.tile` copies that same row once per exam match, so it can be marked exactly like the real model.
- Comparing with this **baseline** is what proves the rating gap teaches something: 0.967 against 1.051.

```python
    pipe = make().fit(X, y)
    scaler, lr = pipe.named_steps["scaler"], pipe.named_steps["lr"]
    if list(lr.classes_) != list(CLASSES):
        raise PredictorError(f"unexpected class order {lr.classes_}")
```

- Trains the final model on **all** 5 251 matches; the exam is over, so no data is wasted.
- `named_steps` gives access to the two trained steps, to read their numbers.
- A safety check: the saved numbers will be read in the order away, draw, home. If scikit-learn ever sorted the classes differently, the code stops instead of saving swapped numbers.

```python
    weights = {
        "mean": float(scaler.mean_[0]),
        "scale": float(scaler.scale_[0]),
        "coef": [float(c[0]) for c in lr.coef_],
        "intercept": [float(b) for b in lr.intercept_],
        ...
    }
```

- Collects the 8 numbers: `mean` −0.1508 (average gap), `scale` 88.4953 (typical gap), three slopes `coef`, three starting values `intercept`. The real dictionary also stores the training date, the number of rows and the exam report.
- `float(...)` turns numpy's number types into plain Python numbers, which `json` knows how to write.
- `lr.coef_` is a table of 3 rows and 1 column; `c[0]` takes the single value of each row.

```python
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(weights, indent=2), encoding="utf-8")
```

- Creates the folder if needed (`exist_ok=True`: no error if it already exists), then writes the dictionary as readable JSON.
- Saving plain numbers, not a saved scikit-learn object, keeps the file readable by a person, comparable in git, and usable without scikit-learn.

**In one line:** reads the match data, trains a standardise-then-logistic-regression model, marks it on an exam, and saves its 8 numbers to `predictor_weights.json`.

---

## `Probs`: a small record of three chances

**Arguments:** `p_home`, `p_draw`, `p_away`: `float`, the three chances. `trace`: `dict` or `None`, the intermediate numbers for the expert log.

```python
    __slots__ = ("p_home", "p_draw", "p_away", "trace")

    def __init__(self, p_home, p_draw, p_away, trace=None):
        self.p_home, self.p_draw, self.p_away = p_home, p_draw, p_away
```

- `__slots__` fixes the attribute names: less memory per object, and a typing mistake raises an error. Useful because one `Probs` is built per simulated match.
- The three values are set in one line by **tuple assignment**.
- `trace` stays `None` unless asked for: building a dictionary per match would only waste time in a long simulation.

| Method | Does |
|---|---|
| `as_tuple()` | returns `(home, draw, away)`. Careful: this is the reverse of `CLASSES` (away, draw, home) |
| `__repr__()` | prints `Probs(home=0.622, draw=0.194, away=0.184)` |

---

## `MatchModel.__init__(weights)`: hold the 8 numbers

**Arguments:** `weights`: `dict`, the content of `predictor_weights.json`.

```python
        self.mean = float(weights["mean"])
        self.scale = float(weights["scale"]) or 1.0
        self.coef = [float(c) for c in weights["coef"]]
        self.intercept = [float(b) for b in weights["intercept"]]
```

- Copies the numbers into the object: `mean = -0.1508`, `scale = 88.4953`, `coef = [-0.5384, -0.0308, 0.5692]`, `intercept = [-0.0103, -0.3459, 0.3562]`.
- `or 1.0` is a guard: if the typical gap were 0 (every match with the same gap), dividing by it would crash, so 1.0 is used instead. `0.0 or 1.0` gives `1.0`.

```python
        self.classes = tuple(weights.get("classes", CLASSES))
        if len(self.coef) != 3 or len(self.intercept) != 3:
            raise PredictorError("weights must hold exactly three classes")
```

- Reads the class order from the file. **Known weakness:** it is read but never compared with `CLASSES`, so a file in another order would be used silently.
- The length check refuses a file that does not have exactly three judges, for example a two-result model saved by mistake.

---

## `MatchModel.load(path)`: read the file

**Arguments:** `path`: `Path` or `str`, where `predictor_weights.json` is.

```python
    @classmethod
    def load(cls, path=WEIGHTS_JSON):
        path = Path(path)
        if not path.is_file():
            raise PredictorError(...)
        return cls(json.loads(path.read_text(encoding="utf-8")))
```

- `@classmethod` means the method is called on the class itself, `MatchModel.load()`, and receives the class as `cls`. It is a common way to write an **alternative constructor**: another way to build an object, here "from a file".
- If the file is missing, the error message says exactly which command to run: `python -m model.predictor --train`.
- `cls(...)` calls `__init__` with the dictionary read from the file.

**In one line:** builds a `MatchModel` from the saved file, with a helpful message if it is missing.

---

## `MatchModel.scores(elo_home, elo_away)`: steps 0 and 1

**Arguments:** `elo_home`, `elo_away`: `float`, the two ratings.

```python
        x = elo_home - elo_away
        xs = (x - self.mean) / self.scale
        z = [w * xs + b for w, b in zip(self.coef, self.intercept)]
        return x, xs, z
```

- `x` is the gap, `xs` the standardised gap. Arsenal v Atalanta: `x = 67.76`, `xs = (67.76 + 0.1508) / 88.4953 = 0.767`.
- `zip` pairs each slope with its starting value, and the list comprehension computes the three scores, one straight line per judge: `z = [-0.423, -0.369, 0.793]` (away, draw, home).
- Returning all three values (not just `z`) lets the expert log show every step.

**In one line:** takes two ratings and returns the gap, the standardised gap and the three scores.

---

## `MatchModel.probabilities(elo_home, elo_away, neutral, trace)`: the three chances

**Arguments:** `elo_home`, `elo_away`: `float`. `neutral`: `bool`, `True` for a match on neutral ground (the final). `trace`: `bool`, also keep the intermediate numbers.

```python
        if neutral:
            a = self.probabilities(elo_home, elo_away, trace=trace)
            b = self.probabilities(elo_away, elo_home, trace=trace)
```

- On neutral ground, the method calls **itself** twice (a **recursive call**): once with the first club at home, once with the second club at home. Each call has `neutral=False`, so the recursion stops after one level.
- This way the softmax maths is written only once, below.

```python
            probs = Probs((a.p_home + b.p_away) / 2, (a.p_draw + b.p_draw) / 2,
                          (a.p_away + b.p_home) / 2)
```

- Averages the two orientations. The first club's win is "home win" in `a` but "away win" in `b`, hence `a.p_home + b.p_away`.
- Arsenal v Atalanta: `(0.622 + 0.475) / 2 = 0.548` Arsenal, `(0.194 + 0.231) / 2 = 0.212` draw, `(0.184 + 0.294) / 2 = 0.239` Atalanta. The home advantage cancels out.

```python
        x, xs, z = self.scores(elo_home, elo_away)
        top = max(z)
        e = [math.exp(v - top) for v in z]
```

- Gets the three scores, then subtracts the biggest from each before `math.exp`. Softmax does not change when the same number is subtracted from every score, and this stops `exp` from overflowing on huge scores (`math.exp(710)` raises an error).
- Arsenal v Atalanta: `top = 0.793`, `e = [exp(-1.216), exp(-1.162), exp(0)] = [0.296, 0.313, 1.0]`.
- This trick is called a **numerically stable softmax**.

```python
        total = sum(e)
        p_away, p_draw, p_home = (v / total for v in e)
        probs = Probs(p_home, p_draw, p_away)
```

- Divides each value by the total so the three add up to 1: `total = 1.609`, chances `0.184, 0.194, 0.622`.
- The three chances are unpacked **by position** (away, draw, home). This is why the class order must be right in the file.
- Wraps them in a `Probs` record.

```python
        if trace:
            probs.trace = {"x": x, "x_scaled": xs, "z": {...}, ...}
        return probs
```

- Only when asked, stores every intermediate number for the expert log.

**In one line:** takes two ratings and returns the chances of home win, draw and away win, averaged over both orientations on neutral ground.

---

## `format_trace(t, digits)` and the last lines

| Code | Does |
|---|---|
| `format_trace(t, digits=3)` | turns a trace into lines like `x' = (x - -0.151) / 88.495 = 0.767` and `z_home = +0.5692 * x' +0.3562 = 0.793` for the expert log; on neutral ground, calls itself for both orientations and indents them |
| `if __name__ == "__main__":` | runs only when the file is started directly |
| `if "--train" in sys.argv: train()` | `python -m model.predictor --train` trains the model |
| `else: ...` | otherwise prints the chances for gaps of −300, −100, 0, +100, +300 and one neutral match, a quick check that the saved numbers make sense |

---
---

# `predictor.py`, ligne par ligne

> Cette page explique le code du modèle de match. Pour l'idée (écart standardisé, trois juges, softmax, entraînement), lisez d'abord [`../logistic_regression.md`](../logistic_regression.md#le-modèle-de-match--dun-écart-de-notes-à-trois-chances).

## Comment lire cette page

- Chaque fonction commence par ses **arguments**.
- Le code vient en groupes de 2 à 4 lignes, chacun suivi de points : quoi, pourquoi, et quelle idée générale.
- Chaque fonction se termine par **En une ligne**.

Le fichier a deux moitiés qui ne se mélangent jamais : `train` (a besoin de scikit-learn, lancé une fois) et `MatchModel` (n'a besoin que de `math`, lancé avant chaque match simulé).

---

## Les imports et les réglages

```python
import json
import math
import sys
from datetime import datetime
from pathlib import Path
```

- Seuls des modules fournis avec Python sont importés en haut : `json` lit et écrit les 8 nombres, `math` donne `exp` pour softmax, `sys` lit `--train`, `datetime` date l'entraînement, `Path` construit les chemins.
- scikit-learn, pandas et numpy ne sont **pas** importés ici, exprès : ils sont importés seulement dans `train`. Donc `import model.predictor` marche sur un ordinateur sans eux, et l'appli peut tourner sans les installer.

```python
CLASSES = (-1, 0, 1)                 # away win, draw, home win
CLASS_NAMES = {-1: "away", 0: "draw", 1: "home"}
```

- Les trois résultats sous forme de nombres, dans l'ordre où scikit-learn les trie (le plus petit d'abord). Le même ordre est utilisé partout : extérieur, nul, domicile.
- Un **tuple** est utilisé car cet ordre ne doit jamais changer pendant que le programme tourne ; un tuple ne peut pas être modifié.

```python
class PredictorError(Exception):
    """The model cannot be used. The message says what to run."""
```

- Une **exception personnalisée** : un nouveau type d'erreur qui hérite de `Exception` de Python. Son corps n'est qu'une docstring.
- Avoir son propre nom permet à l'interface d'attraper exactement ce problème (`except PredictorError`) et d'afficher un message clair, sans cacher les autres erreurs inattendues.

---

## `train(features_csv, out_json, verbose)` : apprendre les 8 nombres

**Arguments :** `features_csv` : `Path`, les données d'entraînement (`match_features.csv`). `out_json` : `Path`, où enregistrer les nombres. `verbose` : `bool`, afficher un résumé si `True`.

```python
    import numpy as np
    import pandas as pd
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import log_loss
```

- Des imports **dans la fonction** : ils ne s'exécutent que quand `train` est appelée. C'est ainsi que les grosses bibliothèques restent hors de l'appli.
- `LogisticRegression` (scikit-learn) trouve les pentes et les valeurs de départ ; `log_loss` (scikit-learn) calcule la surprise moyenne de [`../logistic_regression.md`](../logistic_regression.md), section 10. Les deux imports suivants, `Pipeline` et `StandardScaler`, viennent aussi de scikit-learn.

```python
    df = pd.read_csv(features_csv)
    df = df[df["target"].notna()].copy()
    if df.empty:
        raise PredictorError(f"no played match in {features_csv}")
```

- Lit les 5 328 lignes, puis ne garde que celles dont le résultat est connu (`notna()` veut dire « pas manquant ») : 5 251 lignes.
- `.copy()` fait un tableau indépendant ; sans cela, pandas peut prévenir que des changements futurs pourraient toucher le tableau d'origine.
- S'il ne reste rien, la fonction s'arrête avec une erreur claire au lieu de planter plus tard avec une erreur confuse : une **clause de garde**.

```python
    X = (df["elo_home_before"] - df["elo_away_before"]).to_numpy().reshape(-1, 1)
    y = df["target"].astype(int).to_numpy()
```

- `X` est l'entrée : un écart de notes par match. `.reshape(-1, 1)` transforme une liste plate de 5 251 nombres en tableau de 5 251 lignes et 1 colonne, car scikit-learn attend toujours un tableau d'entrées, même avec une seule entrée.
- `y` est la réponse : −1, 0 ou 1 par match. `.astype(int)` transforme `1.0` en `1`, pour que les trois classes soient des entiers propres.
- `X` et `y` sont les noms habituels en apprentissage automatique : `X` majuscule pour le tableau des entrées, `y` minuscule pour les réponses.

```python
    def make():
        return Pipeline([("scaler", StandardScaler()),
                         ("lr", LogisticRegression(max_iter=1000))])
```

- Une petite **fonction interne** qui construit un modèle neuf, non entraîné, à chaque appel. Elle est appelée deux fois : une pour l'examen, une pour le modèle final.
- `Pipeline` (scikit-learn) enchaîne deux étapes : `StandardScaler` mesure l'écart moyen et typique et standardise l'entrée, puis `LogisticRegression` apprend les trois droites de score.
- `max_iter=1000` autorise jusqu'à 1 000 pas vers le fond du bol ; environ 6 suffisent.

```python
    seasons = [int(s) for s in sorted(df["season"].unique())]
    if len(seasons) >= 2:
        last = seasons[-1]
        train_mask = (df["season"] < last).to_numpy()
```

- Liste les saisons des données : `[2023, 2024, 2025]`.
- Le plan : s'entraîner sur toutes les saisons avant la dernière, et utiliser la dernière comme examen. `train_mask` est une liste de `True`/`False`, une par match : `True` veut dire « utiliser ce match pour l'entraînement ».

```python
        if (~train_mask).sum() < 50 and len(seasons) >= 3:
            last = seasons[-2]
            train_mask = (df["season"] < last).to_numpy()
```

- `~` inverse chaque `True`/`False`, donc `(~train_mask).sum()` compte les matchs d'examen. 2025 n'a que 5 matchs, trop peu pour un examen, donc le code recule d'une saison.
- **Bug :** l'examen devient 2024, qui contient 4 789 matchs, et l'entraînement ne garde que les 457 matchs de 2023. L'examen est bien plus gros que l'entraînement. La correction (découper par date, 80 % / 20 %) est dans [`../logistic_regression.md`](../logistic_regression.md), section 16.

```python
        pipe = make().fit(X[train_mask], y[train_mask])
        proba = pipe.predict_proba(X[~train_mask])
```

- `.fit` entraîne un modèle neuf sur les matchs d'entraînement seulement. `X[train_mask]` garde les lignes où le masque vaut `True` : une **sélection par booléens**.
- `predict_proba` donne trois chances pour chaque match d'examen, que le modèle n'a jamais vu. C'est le test honnête.

```python
        freq = np.bincount(y[train_mask] + 1, minlength=3) / train_mask.sum()
        base = np.tile(freq, (int((~train_mask).sum()), 1))
```

- Construit la prévision « qui ne sait rien ». `y + 1` transforme −1, 0, 1 en 0, 1, 2 ; `np.bincount` compte combien il y en a de chaque ; diviser par le nombre de matchs donne les fréquences habituelles, par exemple `[0.34, 0.21, 0.46]`.
- `np.tile` recopie cette même ligne une fois par match d'examen, pour la noter exactement comme le vrai modèle.
- La comparaison avec cette **référence** prouve que l'écart de notes apprend quelque chose : 0.967 contre 1.051.

```python
    pipe = make().fit(X, y)
    scaler, lr = pipe.named_steps["scaler"], pipe.named_steps["lr"]
    if list(lr.classes_) != list(CLASSES):
        raise PredictorError(f"unexpected class order {lr.classes_}")
```

- Entraîne le modèle final sur **tous** les 5 251 matchs ; l'examen est fini, donc aucune donnée n'est gaspillée.
- `named_steps` donne accès aux deux étapes entraînées, pour lire leurs nombres.
- Une vérification de sécurité : les nombres enregistrés seront lus dans l'ordre extérieur, nul, domicile. Si scikit-learn triait un jour les classes autrement, le code s'arrête au lieu d'enregistrer des nombres échangés.

```python
    weights = {
        "mean": float(scaler.mean_[0]),
        "scale": float(scaler.scale_[0]),
        "coef": [float(c[0]) for c in lr.coef_],
        "intercept": [float(b) for b in lr.intercept_],
        ...
    }
```

- Rassemble les 8 nombres : `mean` −0.1508 (écart moyen), `scale` 88.4953 (écart typique), trois pentes `coef`, trois valeurs de départ `intercept`. Le vrai dictionnaire garde aussi la date d'entraînement, le nombre de lignes et le rapport d'examen.
- `float(...)` transforme les types de nombres de numpy en nombres Python simples, que `json` sait écrire.
- `lr.coef_` est un tableau de 3 lignes et 1 colonne ; `c[0]` prend la seule valeur de chaque ligne.

```python
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(weights, indent=2), encoding="utf-8")
```

- Crée le dossier si besoin (`exist_ok=True` : pas d'erreur s'il existe déjà), puis écrit le dictionnaire en JSON lisible.
- Enregistrer de simples nombres, et non un objet scikit-learn sauvegardé, garde le fichier lisible par une personne, comparable dans git, et utilisable sans scikit-learn.

**En une ligne :** lit les données des matchs, entraîne un modèle « standardiser puis régression logistique », le note sur un examen, et enregistre ses 8 nombres dans `predictor_weights.json`.

---

## `Probs` : une petite fiche de trois chances

**Arguments :** `p_home`, `p_draw`, `p_away` : `float`, les trois chances. `trace` : `dict` ou `None`, les nombres intermédiaires pour le journal expert.

```python
    __slots__ = ("p_home", "p_draw", "p_away", "trace")

    def __init__(self, p_home, p_draw, p_away, trace=None):
        self.p_home, self.p_draw, self.p_away = p_home, p_draw, p_away
```

- `__slots__` fixe les noms des attributs : moins de mémoire par objet, et une faute de frappe provoque une erreur. Utile car un `Probs` est créé par match simulé.
- Les trois valeurs sont rangées en une ligne par **affectation de tuple**.
- `trace` reste `None` sauf demande : construire un dictionnaire par match ne ferait que perdre du temps dans une longue simulation.

| Méthode | Fait |
|---|---|
| `as_tuple()` | renvoie `(domicile, nul, extérieur)`. Attention : c'est l'inverse de `CLASSES` (extérieur, nul, domicile) |
| `__repr__()` | affiche `Probs(home=0.622, draw=0.194, away=0.184)` |

---

## `MatchModel.__init__(weights)` : garder les 8 nombres

**Arguments :** `weights` : `dict`, le contenu de `predictor_weights.json`.

```python
        self.mean = float(weights["mean"])
        self.scale = float(weights["scale"]) or 1.0
        self.coef = [float(c) for c in weights["coef"]]
        self.intercept = [float(b) for b in weights["intercept"]]
```

- Copie les nombres dans l'objet : `mean = -0.1508`, `scale = 88.4953`, `coef = [-0.5384, -0.0308, 0.5692]`, `intercept = [-0.0103, -0.3459, 0.3562]`.
- `or 1.0` est une protection : si l'écart typique valait 0 (tous les matchs avec le même écart), diviser par lui planterait, donc 1.0 est utilisé à la place. `0.0 or 1.0` donne `1.0`.

```python
        self.classes = tuple(weights.get("classes", CLASSES))
        if len(self.coef) != 3 or len(self.intercept) != 3:
            raise PredictorError("weights must hold exactly three classes")
```

- Lit l'ordre des classes dans le fichier. **Point faible connu :** il est lu mais jamais comparé à `CLASSES`, donc un fichier dans un autre ordre serait utilisé sans prévenir.
- La vérification de longueur refuse un fichier qui n'a pas exactement trois juges, par exemple un modèle à deux résultats enregistré par erreur.

---

## `MatchModel.load(path)` : lire le fichier

**Arguments :** `path` : `Path` ou `str`, l'endroit où se trouve `predictor_weights.json`.

```python
    @classmethod
    def load(cls, path=WEIGHTS_JSON):
        path = Path(path)
        if not path.is_file():
            raise PredictorError(...)
        return cls(json.loads(path.read_text(encoding="utf-8")))
```

- `@classmethod` veut dire que la méthode est appelée sur la classe elle-même, `MatchModel.load()`, et reçoit la classe sous le nom `cls`. C'est une façon courante d'écrire un **constructeur alternatif** : une autre façon de créer un objet, ici « à partir d'un fichier ».
- Si le fichier manque, le message d'erreur dit exactement quelle commande lancer : `python -m model.predictor --train`.
- `cls(...)` appelle `__init__` avec le dictionnaire lu dans le fichier.

**En une ligne :** crée un `MatchModel` à partir du fichier enregistré, avec un message utile s'il manque.

---

## `MatchModel.scores(elo_home, elo_away)` : étapes 0 et 1

**Arguments :** `elo_home`, `elo_away` : `float`, les deux notes.

```python
        x = elo_home - elo_away
        xs = (x - self.mean) / self.scale
        z = [w * xs + b for w, b in zip(self.coef, self.intercept)]
        return x, xs, z
```

- `x` est l'écart, `xs` l'écart standardisé. Arsenal-Atalanta : `x = 67.76`, `xs = (67.76 + 0.1508) / 88.4953 = 0.767`.
- `zip` associe chaque pente à sa valeur de départ, et la liste en compréhension calcule les trois scores, une droite par juge : `z = [-0.423, -0.369, 0.793]` (extérieur, nul, domicile).
- Renvoyer les trois valeurs (pas seulement `z`) permet au journal expert de montrer chaque étape.

**En une ligne :** prend deux notes et renvoie l'écart, l'écart standardisé et les trois scores.

---

## `MatchModel.probabilities(elo_home, elo_away, neutral, trace)` : les trois chances

**Arguments :** `elo_home`, `elo_away` : `float`. `neutral` : `bool`, `True` pour un match sur terrain neutre (la finale). `trace` : `bool`, garder aussi les nombres intermédiaires.

```python
        if neutral:
            a = self.probabilities(elo_home, elo_away, trace=trace)
            b = self.probabilities(elo_away, elo_home, trace=trace)
```

- Sur terrain neutre, la méthode s'appelle **elle-même** deux fois (un **appel récursif**) : une fois avec le premier club à domicile, une fois avec le second. Chaque appel a `neutral=False`, donc la récursion s'arrête après un niveau.
- Ainsi le calcul de softmax n'est écrit qu'une seule fois, plus bas.

```python
            probs = Probs((a.p_home + b.p_away) / 2, (a.p_draw + b.p_draw) / 2,
                          (a.p_away + b.p_home) / 2)
```

- Fait la moyenne des deux sens. La victoire du premier club est « victoire domicile » dans `a` mais « victoire extérieur » dans `b`, d'où `a.p_home + b.p_away`.
- Arsenal-Atalanta : `(0.622 + 0.475) / 2 = 0.548` Arsenal, `(0.194 + 0.231) / 2 = 0.212` nul, `(0.184 + 0.294) / 2 = 0.239` Atalanta. L'avantage du terrain s'annule.

```python
        x, xs, z = self.scores(elo_home, elo_away)
        top = max(z)
        e = [math.exp(v - top) for v in z]
```

- Récupère les trois scores, puis soustrait le plus grand à chacun avant `math.exp`. Softmax ne change pas quand on soustrait le même nombre à chaque score, et cela empêche `exp` de déborder sur des scores énormes (`math.exp(710)` provoque une erreur).
- Arsenal-Atalanta : `top = 0.793`, `e = [exp(-1.216), exp(-1.162), exp(0)] = [0.296, 0.313, 1.0]`.
- Cette astuce s'appelle une **softmax numériquement stable**.

```python
        total = sum(e)
        p_away, p_draw, p_home = (v / total for v in e)
        probs = Probs(p_home, p_draw, p_away)
```

- Divise chaque valeur par le total pour que les trois fassent 1 : `total = 1.609`, chances `0.184, 0.194, 0.622`.
- Les trois chances sont déballées **selon leur position** (extérieur, nul, domicile). C'est pourquoi l'ordre des classes doit être bon dans le fichier.
- Les range dans une fiche `Probs`.

```python
        if trace:
            probs.trace = {"x": x, "x_scaled": xs, "z": {...}, ...}
        return probs
```

- Seulement si on le demande, garde chaque nombre intermédiaire pour le journal expert.

**En une ligne :** prend deux notes et renvoie les chances de victoire à domicile, de nul et de victoire à l'extérieur, en faisant la moyenne des deux sens sur terrain neutre.

---

## `format_trace(t, digits)` et les dernières lignes

| Code | Fait |
|---|---|
| `format_trace(t, digits=3)` | transforme une trace en lignes comme `x' = (x - -0.151) / 88.495 = 0.767` et `z_home = +0.5692 * x' +0.3562 = 0.793` pour le journal expert ; sur terrain neutre, s'appelle elle-même pour les deux sens et les décale |
| `if __name__ == "__main__":` | ne s'exécute que quand le fichier est lancé directement |
| `if "--train" in sys.argv: train()` | `python -m model.predictor --train` entraîne le modèle |
| `else: ...` | sinon affiche les chances pour des écarts de −300, −100, 0, +100, +300 et un match neutre, une vérification rapide que les nombres enregistrés ont du sens |
