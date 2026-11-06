"""Turn a match OUTCOME into a SCORELINE with a Poisson goal model.

Same job as scorelines.py, and the same call (`sample(outcome, rng, ...)`),
so the engine does not care which one it holds. The difference: the chance
of each scoreline now depends on the Elo gap of the two clubs, not on one
global table.

    d         = (R_home - R_away) / 400                the Elo gap, in units of 400
    lambda_H  = tau * mu_home * exp(+gamma * d)        expected goals, home side
    lambda_A  = tau * mu_away * exp(-gamma * d)        expected goals, away side
    P(h, a)   = Poisson(h; lambda_H) * Poisson(a; lambda_A)

    mu_home, mu_away, gamma   fitted by model/fit_goals.py (goal_weights.json)
    tau                       1.0 = as fitted; below 1 gives tighter scores, above 1 wider ones

The classifier still decides the OUTCOME. This module keeps only the cells of
the grid that agree with it (home: h > a, draw: h == a, away: h < a) and draws
one of them with probability proportional to P(h, a).

Neutral ground (the final): there is no home advantage, so both sides use the
geometric mean of mu_home and mu_away, which is the middle of the two on the log
scale the model works on.

Extra time: 30 minutes is a third of a match, so each side's expected goals
are lambda / 3 and the two scores are drawn independently.
"""

import json
import math
from pathlib import Path

from model.scorelines import MAX_GOALS

BASE_DIR = Path(__file__).resolve().parents[1]
WEIGHTS_JSON = BASE_DIR / "data" / "reference" / "goal_weights.json"

ELO_SCALE = 400.0
ET_SHARE = 1.0 / 3.0

# Used when goal_weights.json is missing: the values of the first fit
# (4626 matches), reported in the log as "fallback".
FALLBACK = {"mu_home": 1.5753, "mu_away": 1.2855, "gamma": 1.4044, "matches": 0}


def _pmf(k, lam):
    """P(k goals) when `lam` goals are expected."""
    return math.exp(-lam) * lam ** k / math.factorial(k)


class PoissonSampler:
    """Draws a (home_goals, away_goals) pair given the outcome and the Elo gap."""

    def __init__(self, mu_home, mu_away, gamma, tau=1.0, max_goals=MAX_GOALS,
                 source="manual", matches=0):
        self.mu_home = float(mu_home)
        self.mu_away = float(mu_away)
        self.gamma = float(gamma)
        self.tau = float(tau)
        self.max_goals = int(max_goals)
        self.source = source
        self.matches = int(matches)
        # The cells of the grid that belong to each outcome, built once.
        g = self.max_goals
        self._pairs = {
            "home": [(h, a) for h in range(1, g + 1) for a in range(h)],
            "draw": [(k, k) for k in range(g + 1)],
            "away": [(h, a) for a in range(1, g + 1) for h in range(a)],
        }

    @classmethod
    def load(cls, path=WEIGHTS_JSON, tau=1.0):
        path = Path(path)
        if path.is_file():
            raw = json.loads(path.read_text(encoding="utf-8"))
            return cls(raw["mu_home"], raw["mu_away"], raw["gamma"], tau=tau,
                       source=path.name, matches=raw.get("matches", 0))
        return cls(FALLBACK["mu_home"], FALLBACK["mu_away"], FALLBACK["gamma"],
                   tau=tau, source="fallback", matches=FALLBACK["matches"])

    def lambdas(self, elo_gap, neutral=False):
        """(lambda_home, lambda_away) for a Elo gap R_home - R_away."""
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
        """One scoreline for `outcome` in {"home", "draw", "away"}."""
        cells, weights = self._weights(outcome, elo_gap, neutral)
        return rng.choices(cells, weights=weights)[0]

    def probability(self, outcome, home_goals, away_goals, elo_gap=0.0, neutral=False):
        """P(this scoreline | outcome), for the expert log."""
        cells, weights = self._weights(outcome, elo_gap, neutral)
        try:
            i = cells.index((home_goals, away_goals))
        except ValueError:
            return 0.0
        return weights[i] / sum(weights)

    def sample_extra_time(self, rng, elo_gap=0.0, neutral=True):
        """A 30-minute score: each side Poisson with lambda / 3, drawn independently."""
        lam_h, lam_a = self.lambdas(elo_gap, neutral)
        ks = range(self.max_goals + 1)
        h = rng.choices(ks, weights=[_pmf(k, lam_h * ET_SHARE) for k in ks])[0]
        a = rng.choices(ks, weights=[_pmf(k, lam_a * ET_SHARE) for k in ks])[0]
        return h, a


if __name__ == "__main__":
    import random
    sampler = PoissonSampler.load()
    print(f"source: {sampler.source} (gamma {sampler.gamma:.3f}, "
          f"mu_home {sampler.mu_home:.3f}, mu_away {sampler.mu_away:.3f})")
    rng = random.Random(1)
    for gap in (0, 100, 200):
        lam_h, lam_a = sampler.lambdas(gap)
        print(f"gap {gap:+4d}: lambda {lam_h:.2f} v {lam_a:.2f}   home wins",
              [sampler.sample("home", rng, gap) for _ in range(6)])
    print("extra time", [sampler.sample_extra_time(rng) for _ in range(8)])
