# Poisson goals, broken down

How the "Poisson goals" option was built into your UEFA app on the branch `trying_vgoals`. Every snippet below is the real code in your repo. Every number was computed by running it.

Your last message stopped after "like that :", so I used the five-heading format from your saved preferences for every part: **1 Purpose, 2 Arguments, 3 Category, 4 Worked example with the state shown, 5 Line by line.**

**Contents**

0. The shape of the whole thing
1. `model/fit_goals.py`: from data to three numbers
2. `model/poisson_goals.py`: the sampler
3. `model/scorelines.py`: the same call shape for the old sampler
4. `model/match_engine.py`: the engine passes the Elo gap
5. `model/simulation.py`: the option, the choice of sampler, the Monte Carlo
6. The interface: switch, hint, launch
7. Defects, what to keep, how to edit it
8. Going further

---

## 0. The shape of the whole thing

**Purpose.** Once the classifier has decided who wins, draw a scoreline from a Poisson model of the Elo gap instead of from one global table.

**Category.** A *strategy swap*: two interchangeable objects (`ScorelineSampler`, `PoissonSampler`) with the same call, chosen by one option.

**The key design decision.** The classifier still chooses the **outcome** (home, draw, away). The goal model only chooses the **score inside that outcome**. That is why the code only keeps the grid cells that agree with the outcome. It also means the sampler has the same call shape as the old one, so the engine never needs to know which one it holds.

```
  data/processed/match_features.csv  (Elo before each match)
  data/processed/fixtures_25.csv     (goals)
              |
              v     python -m model.fit_goals
  data/reference/goal_weights.json   mu_home, mu_away, gamma
              |
              v     PoissonSampler.load()
  Resources.sampler_for("poisson") --+
  Resources.sampler (the table)  ----+--> MatchEngine(sampler)
                                              |
        classifier: p_home, p_draw, p_away    |  engine.play(home, away)
                 |                            v
                 +--> outcome u -----> sampler.sample(outcome, rng, elo_gap, neutral)
                                              |
                                              v
                                       (home_goals, away_goals)
```

The maths, with every symbol:

$$\lambda_H=\tau\,\mu_H\,e^{\gamma d},\qquad \lambda_A=\tau\,\mu_A\,e^{-\gamma d},\qquad d=\frac{R_H-R_A}{400},\qquad P(k)=\frac{e^{-\lambda}\lambda^{k}}{k!}$$

| Symbol | Said | Meaning | Value in your data |
|---|---|---|---|
| $\lambda_H,\lambda_A$ | "lambda" | expected goals of the home and the away side | depends on the match |
| $\mu_H,\mu_A$ | "mu" | expected goals of two equal teams | 1.5753 and 1.2855 |
| $\gamma$ | "gamma" | how strongly the Elo gap moves goals | 1.4044 |
| $\tau$ | "tau" | tension knob, 1 means as fitted | 1.0 |
| $R_H,R_A$ | "R" | Elo ratings of the home and away side | e.g. 1650 and 1450 |
| $d$ | "d" | Elo gap in units of 400 | 0.5 |
| $k$ | "k" | a number of goals | 0, 1, 2... |
| $k!$ | "k factorial" | $k\times(k-1)\times\dots\times1$, and $0!=1$ | $3!=6$ |

---

## 1. `model/fit_goals.py`: from data to three numbers

```python
def load_joined():
    features = pd.read_csv(FEATURES_CSV)
    fixtures = pd.read_csv(FIXTURES_CSV)
    goals = fixtures[KEY + ["ft_home", "ft_away"]]
    df = features.merge(goals, on=KEY, how="inner", validate="one_to_one")
    df = df.dropna(subset=["ft_home", "ft_away"]).reset_index(drop=True)
    df["d"] = (df["elo_home_before"] - df["elo_away_before"]) / ELO_SCALE
    return df


def stack(df):
    signed_gap = np.concatenate([df["d"], -df["d"]])
    is_home = np.concatenate([df["is_home"], np.zeros(len(df))])
    goals = np.concatenate([df["ft_home"], df["ft_away"]])
    X = np.column_stack([signed_gap, is_home])
    return X, goals


def fit(df=None):
    df = load_joined() if df is None else df
    X, y = stack(df)
    model = PoissonRegressor(alpha=0.0, max_iter=1000).fit(X, y)
    gamma, h = model.coef_
    return {"mu_home": float(np.exp(model.intercept_ + h)),
            "mu_away": float(np.exp(model.intercept_)),
            "gamma": float(gamma), "matches": int(len(df))}
```

**1. Purpose.** Find the $\mu_H$, $\mu_A$ and $\gamma$ that make your 4,626 real scores most likely, and save them in `goal_weights.json`.

**2. Arguments.** `load_joined()` takes none. `stack(df)` takes the joined table and returns `X` (shape 9252 × 2) and `goals` (9252 values). `fit(df=None)` takes a table or loads one, and returns a dict of four numbers.

**3. Category.** Wrangling (join and reshape), then a maximum-likelihood fit (a Poisson regression).

**4. Worked example.** Two real rows after the join:

| `home_team` | `away_team` | Elo home | Elo away | `is_home` | goals | `d` |
|---|---|---:|---:|---:|---|---:|
| HJK Helsinki | Mariehamn | 1448.48 | 1448.48 | 1 | 1-0 | 0.0000 |
| Gnistan | HJK Helsinki | 1448.48 | 1457.51 | 1 | 1-2 | -0.0226 |

After `stack`, with $n=4626$ matches, row 1 (Gnistan at home) has `X = [-0.0226, 1]`, `goals = 1`. Its away twin is row $n+1$ (HJK away), with `X = [+0.0226, 0]` and `goals = 2`. The fitted line is $\log\lambda = 0.251 + 1.404\,s + 0.203\cdot\text{is\_home}$. That gives $\mu_A=e^{0.251}=1.2855$ and $\mu_H=e^{0.251+0.203}=1.5753$.

**5. Line by line.**
- `merge(... validate="one_to_one")`: glue rows with equal `(timestamp, home_team, away_team)`; raise an error if a key appears twice.
- `dropna(...)`: removes the 2 unplayed matches (4628 becomes 4626).
- `np.concatenate([d, -d])`: home rows keep the gap, away rows flip its sign, because $\lambda_A$ uses $e^{-\gamma d}$.
- `alpha=0.0`: no regularisation. The default 1.0 would shrink $\gamma$ towards 0.
- `float(...)`, `int(...)`: `json.dumps` cannot write NumPy numbers.

---

## 2. `model/poisson_goals.py`: the sampler

```python
def _pmf(k, lam):
    return math.exp(-lam) * lam ** k / math.factorial(k)


class PoissonSampler:
    def __init__(self, mu_home, mu_away, gamma, tau=1.0, max_goals=MAX_GOALS,
                 source="manual", matches=0):
        ...
        g = self.max_goals
        self._pairs = {
            "home": [(h, a) for h in range(1, g + 1) for a in range(h)],
            "draw": [(k, k) for k in range(g + 1)],
            "away": [(h, a) for a in range(1, g + 1) for h in range(a)],
        }

    def lambdas(self, elo_gap, neutral=False):
        d = elo_gap / ELO_SCALE
        if neutral:
            mu_h = mu_a = math.sqrt(self.mu_home * self.mu_away)
        else:
            mu_h, mu_a = self.mu_home, self.mu_away
        return (self.tau * mu_h * math.exp(self.gamma * d),
                self.tau * mu_a * math.exp(-self.gamma * d))

    def _weights(self, outcome, elo_gap, neutral):
        lam_h, lam_a = self.lambdas(elo_gap, neutral)
        ph = [_pmf(k, lam_h) for k in range(self.max_goals + 1)]
        pa = [_pmf(k, lam_a) for k in range(self.max_goals + 1)]
        cells = self._pairs[outcome]
        return cells, [ph[h] * pa[a] for h, a in cells]

    def sample(self, outcome, rng, elo_gap=0.0, neutral=False):
        cells, weights = self._weights(outcome, elo_gap, neutral)
        return rng.choices(cells, weights=weights)[0]

    def probability(self, outcome, home_goals, away_goals, elo_gap=0.0, neutral=False):
        cells, weights = self._weights(outcome, elo_gap, neutral)
        try:
            i = cells.index((home_goals, away_goals))
        except ValueError:
            return 0.0
        return weights[i] / sum(weights)

    def sample_extra_time(self, rng, elo_gap=0.0, neutral=True):
        lam_h, lam_a = self.lambdas(elo_gap, neutral)
        ks = range(self.max_goals + 1)
        h = rng.choices(ks, weights=[_pmf(k, lam_h * ET_SHARE) for k in ks])[0]
        a = rng.choices(ks, weights=[_pmf(k, lam_a * ET_SHARE) for k in ks])[0]
        return h, a
```

**1. Purpose.** Turn "the home side wins" plus "the Elo gap is +100" into one scoreline such as 1-0.

**2. Arguments.**

| Argument | Type | Meaning |
|---|---|---|
| `outcome` | `"home"`, `"draw"` or `"away"` | what the classifier decided |
| `rng` | `random.Random` | the engine's generator (it has `.choices`) |
| `elo_gap` | float | $R_H-R_A$ in Elo points, before the match |
| `neutral` | bool | no home advantage (the final) |
| returns | `(int, int)` | home goals, away goals |

**3. Category.** A *sampler*: build a table of weights, then draw one entry in proportion to its weight. `_pairs` is a precomputed index, `lambdas` is a transform, `_weights` is a builder.

**4. Worked example.** Elo gap = +100, outcome `"home"`, `max_goals=6`.

*Step A, `lambdas(100)`.* $d=100/400=0.25$, so $\lambda_H=1.5753\,e^{1.4044\times0.25}=2.2379$ and $\lambda_A=1.2855\,e^{-0.3511}=0.9049$.

*Step B, the two lists.*

| goals $k$ | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---:|---:|---:|---:|---:|---:|---:|
| `ph[k]` | 0.1067 | 0.2387 | 0.2671 | 0.1993 | 0.1115 | 0.0499 | 0.0186 |
| `pa[k]` | 0.4046 | 0.3661 | 0.1656 | 0.0500 | 0.0113 | 0.0020 | 0.0003 |

*Step C, `_pairs["home"]`.* The cells with $h>a$. On a tiny grid with `max_goals=2` it is `[(1, 0), (2, 0), (2, 1)]`; with 6 it has 21 cells. The other outcomes on that tiny grid: `draw` is `[(0,0), (1,1), (2,2)]`, `away` is `[(0,1), (0,2), (1,2)]`.

*Step D, weights.* `weights[i] = ph[h] * pa[a]` for each cell. The first four, with the running total that `random.choices` builds:

| cell | `ph[h]` × `pa[a]` | weight | running total |
|---|---|---:|---:|
| (1, 0) | 0.2387 × 0.4046 | 0.0966 | 0.0966 |
| (2, 0) | 0.2671 × 0.4046 | 0.1081 | 0.2047 |
| (2, 1) | 0.2671 × 0.3661 | 0.0978 | 0.3025 |
| (3, 0) | 0.1993 × 0.4046 | 0.0806 | 0.3831 |

The 21 weights add up to 0.6674 (that is the Poisson's own chance of a home win here, which we ignore). `random.choices` draws $u\times0.6674$ and picks the first cell whose running total is above it. With `random.Random(1)`, $u=0.1344$, and $0.1344\times0.6674=0.0897<0.0966$, so the answer is **(1, 0)**.

*Step E, `probability("home", 2, 1, 100)`.* $0.0978/0.6674=0.1465$. The same step gives the full conditional list: 2-0 16.2%, 2-1 14.7%, 1-0 14.5%, 3-0 12.1%, 3-1 10.9%.

**5. Line by line.**
- `_pmf`: the Poisson formula from section 0, one number.
- `_pairs` (in `__init__`): built once, so a call does not re-test 49 cells with `if`. For `"home"`, the outer loop runs `h` from 1 and the inner loop `a` from 0 to `h-1`, which is exactly $h>a$.
- `lambdas`, branch `neutral=False`: uses $\mu_H,\mu_A$. Branch `neutral=True`: both sides use $\sqrt{\mu_H\mu_A}=1.4231$, the middle of the two on the log scale. At a gap of 0 the final therefore has $\lambda=1.4231$ for both.
- `_weights`: two lists of Poisson probabilities, then one multiplication per cell (independence of the two sides).
- `sample`: `rng.choices(cells, weights=...)` normalises the weights itself, so the division by 0.6674 happens automatically.
- `probability`, branch found: `weights[i] / sum(weights)`. Branch not found: returns 0.0, for example a 7-0 when `max_goals` is 6.
- `sample_extra_time`: 30 minutes is a third of a match, so each side's expectation is $\lambda/3$ and the two scores are independent. Neutral: $\lambda=1.4231/3=0.4744$ each, so P(0)=0.6223, P(1)=0.2952, P(2)=0.0700, P(3)=0.0111. Extra time therefore ends 0-0 about 38.7% of the time, and with a single goal 36.7%.

---

## 3. `model/scorelines.py`: the same call shape for the old sampler

```python
    def sample(self, outcome, rng, elo_gap=0.0, neutral=False):
        """elo_gap and neutral are ignored: they exist so that this sampler and
        model/poisson_goals.PoissonSampler can be swapped without touching the engine."""
        cum = self._cum[outcome]
        ...

    def probability(self, outcome, home_goals, away_goals, elo_gap=0.0, neutral=False):
        ...
```

**1. Purpose.** Let the table sampler accept the two new arguments so that the engine can call either sampler the same way.

**2. Arguments.** `elo_gap` (float) and `neutral` (bool), both ignored, with defaults. Old calls `sample(outcome, rng)` still work.

**3. Category.** An *adapter*: change a signature, not a behaviour.

**4. Worked example.** `ScorelineSampler.sample("home", Random(7))` and `ScorelineSampler.sample("home", Random(7), 200, True)` return the same score. I checked it: the default simulation (UCL, seed 1, fast and expert mode, Monte Carlo with 1 and 2 workers) gave results identical to before the edit.

**5. Line by line.** Only the `def` lines and the docstrings changed. The body is untouched, which is why nothing else could change.

---

## 4. `model/match_engine.py`: the engine passes the Elo gap

```python
# _play_fast (non-neutral matches only)
        hg, ag = self.sampler.sample(outcome, rng, r_home - r_away)

# _play_full (neutral matches, and every match in expert mode)
        hg, ag = self.sampler.sample(outcome, self.rng, r_home - r_away, neutral)

# _log (the expert log)
        p_score = self.sampler.probability(m.outcome, m.home_goals, m.away_goals,
                                           m.elo_home - m.elo_away, m.neutral)
```

**1. Purpose.** Give the sampler the information it needs: the rating gap before the match, and whether the ground is neutral.

**2. Arguments.** `r_home`, `r_away` are the current Elo ratings (floats), read at the top of each method. `neutral` is the flag `play()` received.

**3. Category.** Plumbing: pass existing values one step further.

**4. Worked example.** Home 1650 v away 1450, regular match: `_play_fast` calls `sample(outcome, rng, 200)` and the Poisson sampler computes $\lambda_H=3.179$, $\lambda_A=0.637$. The final (neutral) goes through `_play_full`, which also passes `neutral=True`.

**5. Line by line.**
- Why `_play_fast` has no `neutral`: it is only used when `neutral` is false (see `play()`), so the default `False` is correct.
- The gap is the **pre-match** rating. The Elo update happens later in the same method, so there is no leakage.
- In `_log`, `m.elo_home` and `m.elo_away` are the ratings stored in the `Match` before the update, so the logged probability is the one actually used.

---

## 5. `model/simulation.py`: the option, the choice of sampler, the Monte Carlo

```python
GOAL_MODELS = ("table", "poisson")
DEFAULT_GOALS = "table"

class SimConfig:
    def __init__(self, method=knockout.DEFAULT_METHOD, expert=False, seed=None,
                 runs=1, goals=DEFAULT_GOALS):
        ...
        if goals not in GOAL_MODELS:
            raise ValueError(f"goals must be one of {GOAL_MODELS}")
        self.goals = goals

class Resources:
    def __init__(self, model=None, sampler=None, ratings=None):
        ...
        self.sampler = sampler or ScorelineSampler.load()
        self._poisson = None            # loaded the first time a run asks for it

    def sampler_for(self, goals):
        if goals == "poisson":
            if self._poisson is None:
                self._poisson = PoissonSampler.load()
            return self._poisson
        return self.sampler

# in simulate():
    engine = MatchEngine(res.model, res.sampler_for(config.goals), seeds, k_table, ...)
```

And the option travelling through the Monte Carlo:

```python
# monte_carlo
    counts, points = _mc_parallel(comp, clubs, days, config.method, seeds,
                                  workers, progress, res, config.goals)
    ...
    counts, points = _mc_block(comp, clubs, days, config.method, seeds, res,
                               progress, runs, config.goals)

# _mc_parallel
    futures = [pool.submit(_mc_worker, (comp, clubs, days, method, chunk, goals))
               for chunk in chunks]

# _mc_worker
    comp, clubs, days, method, seeds, goals = args
    return len(seeds), _mc_block(comp, clubs, days, method, seeds, _WORKER_RES, goals=goals)

# _mc_block
    run_cfg = SimConfig(method, expert=False, seed=seed, goals=goals)
```

**1. Purpose.** Add a `goals` setting, pick the matching sampler once per run, and make the Monte Carlo (including its worker processes) respect it.

**2. Arguments.**

| Name | Type | Meaning |
|---|---|---|
| `goals` | `"table"` or `"poisson"` | which goal model to use |
| `Resources.sampler_for(goals)` | returns a sampler | the table one, or the Poisson one, loaded lazily |

**3. Category.** Configuration (a validated option), a *lazy cache* (`_poisson`), and a dispatcher (`sampler_for`).

**4. Worked example.**

| Step | State |
|---|---|
| `SimConfig(goals="poisson")` | passes validation, `config.goals = "poisson"` |
| first `res.sampler_for("poisson")` | `_poisson` is `None`, so it reads `goal_weights.json`; `_poisson` now holds a `PoissonSampler` |
| second call | `_poisson` is not `None`, the same object is returned, no file read |
| `SimConfig(goals="nope")` | `ValueError: goals must be one of ('table', 'poisson')` |
| `SimConfig()` | `goals = "table"`, so old behaviour |

**5. Line by line, and why the Monte Carlo needs so many edits.**
- A Monte Carlo builds a **new** `SimConfig` for every season (`run_cfg`) because each season needs its own seed. That new config would silently fall back to `"table"`. So `goals` must be handed down explicitly, as a plain string.
- It travels inside the tuple sent to each worker process. A plain string pickles trivially, which is why it is passed as a string rather than as a sampler object.
- The `Resources` object, with its lazily loaded `_poisson`, is already sent to the workers by the existing `initializer`, so the workers do not reload files per season.
- Parameter order: `goals` is added **last**, with a default, so every old call still works.
- The expert log header now prints `scorelines: poisson model, goal_weights.json (4626 matches)`. If it says `fallback`, the JSON was not found and the constants in `poisson_goals.py` were used.

---

## 6. The interface: switch, hint, launch

```python
# sim_view.py, in the settings grid (row 3)
        label(3, "sim_goals_short")
        self.goals_switch = ctk.CTkSwitch(grid, text="", width=46,
                                          progress_color=self.app.accent,
                                          command=self._toggle_goals)
        self.goals_switch.grid(row=3, column=1, sticky="w")
        if self.poisson:
            self.goals_switch.select()
        self.goals_hint = hint(3, "")
        self._paint_goals_hint()

    def _toggle_goals(self):
        self.poisson = bool(self.goals_switch.get())

    def _paint_goals_hint(self):
        self.goals_hint.configure(text=self.app.t("sim_goals_h") + " "
                                       + self.app.t("sim_goals_" + self.method))

# in _pick_method, after _paint_methods():
        self._paint_goals_hint()

# in _launch:
        self.job = SimJob(self.comp, self.teams, self.matchdays,
                          method=self.method, expert=self.expert,
                          runs=self.runs, seed=seed,
                          goals="poisson" if self.poisson else "table").start()
```

```python
# sim_engine.py
    def __init__(self, comp, teams, matchdays, method=DEFAULT_METHOD,
                 expert=True, runs=0, seed=None, goals=DEFAULT_GOALS):
        self.config = sim.SimConfig(method=method, expert=expert, seed=seed, goals=goals)
```

**1. Purpose.** A switch on the settings screen that sets the `goals` option, plus a hint that says what it changes in the selected two-leg method.

**2. Arguments.** `self.poisson` (bool, remembered between runs like `self.expert`). `self.method` is `"legs"`, `"aggregate"` or `"oneshot"`.

**3. Category.** View state and event handlers: a toggle, a text refresher, and a hand-off to the engine.

**4. Worked example.**

| User action | `self.poisson` | `self.method` | hint text (English) |
|---|---|---|---|
| open screen | False | aggregate | "...in every mode. Here it also decides the two-legged ties and extra time." |
| click "One-shot probability" card | False | oneshot | "...in every mode. A tie is one random draw without scores, so nothing else changes." |
| flip the switch | True | oneshot | same text (the switch does not change the hint) |
| press Simulate | True | oneshot | `SimJob(..., goals="poisson")` |

**5. Line by line.**
- `self.goals_switch.select()` sets the switch to match the remembered value when the screen is rebuilt.
- `hint(3, "")` creates the help label empty, then `_paint_goals_hint()` fills it. The key is built as `"sim_goals_" + self.method`, so `config.py` needs one key per method (all three exist, in English and French).
- `goals="poisson" if self.poisson else "table"`: a bool becomes the string the model expects. The interface never imports the sampler classes.

I have not seen this screen run: this machine has no display or CustomTkinter. The files compile and the model-side behaviour is tested.

---

## 7. Defects, what to keep, how to edit it

**Defects (measured or read in the code):**

1. **The goal count is cut at 6.** The grid stops at 6 goals and renormalises, so 7+ goals never happen. In the replay of your 4,626 real matches, Poisson made **18.0%** of matches wins by 3 goals or more, against **21.4%** in reality. That is the model being too cautious about heavy wins, partly from the cap, partly from Poisson's variance being too small.
2. **Independence is false.** Poisson treats the two sides' goals as independent, which gives draws 24.0% against a real 20.9%. This is hidden here, because the classifier chooses the outcome, but it still shapes which draws (0-0 or 1-1) appear.
3. **The neutral rule is my assumption.** Using $\sqrt{\mu_H\mu_A}$ for a final is a reasonable middle, but your data has only 53 neutral matches, so I did not test it.
4. **Extra time ignores the Elo gap.** `knockout.py` calls `sample_extra_time(engine.rng)` without a gap, so extra time is played between "equal" sides.
5. **$\gamma$ comes from every competition mixed** (domestic leagues and Europe). Whether it fits European matches alone I did not check.
6. **The screen was never run.**

**The design decision to keep.** The sampler has the same call as the old one, and the classifier still picks the outcome. Undo either and the engine, the log and the Monte Carlo all need rewriting.

| You want to... | Edit | Watch out for |
|---|---|---|
| refit after new data | run `python model/elo_score_updating.py --write`, then `python -m model.fit_goals` | the second step reads `match_features.csv`, so the first must come first |
| a tenser final | build `PoissonSampler.load(tau=0.8)` and use it only in `play_final` | the engine holds one sampler, so you need a second one passed in |
| allow more than 6 goals | `max_goals=` in `PoissonSampler(...)` | `MAX_GOALS` in `scorelines.py` is shared by the table sampler |
| add a third goal model | add its name to `GOAL_MODELS`, a branch in `sampler_for`, a UI control | the `sim_goals_*` hint keys must exist in both languages |
| remove the option | delete `goals` from `SimConfig`, `_mc_*`, `SimJob`, the view | the Monte Carlo tuple changes size |

---

## 8. Going further

The explanation above is complete. This part is extra.

- **Dixon-Coles** corrects Poisson for 0-0, 1-0, 0-1 and 1-1 with one extra parameter, which attacks defect 2 directly.
- A **negative binomial** distribution allows variance larger than the mean, which attacks defect 1. Your home goals have variance 2.10 for a mean of 1.65.
- With **cross-validation** by season you can test whether the fitted $\gamma$ predicts the next season, instead of only the seasons it was fitted on.

## English vocabulary

*drop-in* (replaceable without other changes), *strategy swap*, *lazy* (done only when first needed), *lazily loaded*, *dispatcher*, *renormalise* (rescale so the total is 1), *plumbing* (code that only passes values along), *hand down* (pass to a deeper function).
