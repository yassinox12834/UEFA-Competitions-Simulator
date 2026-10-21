"""Turn a match OUTCOME into a SCORELINE.

The classifier only says "home wins / draw / away wins". A league table
needs goal difference (the first tiebreaker after points), and a
two-legged tie played on aggregate needs goals. So once the outcome is
drawn, a scoreline consistent with it is drawn from a table of how often
each scoreline happened in real matches WITH THAT OUTCOME.

This is route 2 of the roadmap: cheap, honest about what it is, and the
goal difference it produces is not tied to team strength beyond the
outcome. Route 1 (a Poisson goals model) would replace this module and
the classifier together; see docs/MODEL.md, "Going further".

Data
    build_table() reads data/processed/fixtures_25.csv, keeps every
    non-friendly match with a 90-minute score, and counts scorelines per
    outcome. save_table() writes data/reference/scorelines.json so the
    app never needs pandas at run time.

Extra time
    Thirty minutes is a third of a match. A goal scored in a full-length
    replay is kept with probability 1/3 (binomial thinning of a Poisson
    process keeps it Poisson), so an extra-time score is a regular
    scoreline sample with each goal kept or dropped by a coin weighted
    1/3. Cheap, and it gets the one fact that matters right: most extra
    times finish 0-0 or 1-0.
"""

import json
import random
from bisect import bisect
from itertools import accumulate
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
FIXTURES_CSV = BASE_DIR / "data" / "processed" / "fixtures_25.csv"
TABLE_JSON = BASE_DIR / "data" / "reference" / "scorelines.json"

OUTCOMES = ("home", "draw", "away")
MAX_GOALS = 6            # anything above is folded into this bucket
ET_KEEP = 1.0 / 3.0      # share of a full match that extra time lasts

# Used when scorelines.json is missing: a rough shape of European
# football, enough to run, and reported in the log as the fallback.
FALLBACK = {
    "home": {"1-0": 22, "2-0": 18, "2-1": 22, "3-0": 10, "3-1": 12, "3-2": 5,
             "4-0": 4, "4-1": 4, "4-2": 2, "5-0": 1},
    "draw": {"0-0": 30, "1-1": 45, "2-2": 20, "3-3": 5},
    "away": {"0-1": 24, "0-2": 18, "1-2": 22, "0-3": 9, "1-3": 12, "2-3": 6,
             "0-4": 4, "1-4": 3, "2-4": 1, "0-5": 1},
}


def outcome_of(home_goals, away_goals):
    if home_goals > away_goals:
        return "home"
    if home_goals < away_goals:
        return "away"
    return "draw"


# ---------------------------------------------------------------------------
# Building the table (pandas side, run once)
# ---------------------------------------------------------------------------

def build_table(fixtures_csv=FIXTURES_CSV):
    """{outcome: {"h-a": count}} from real matches. Friendlies excluded."""
    import pandas as pd

    df = pd.read_csv(fixtures_csv)
    df = df[df["league"] != "Friendlies Clubs"]
    # ft_* is the 90-minute score; home_goals/away_goals includes extra
    # time in cup ties, which would pollute the regular-time table.
    home_col, away_col = ("ft_home", "ft_away") if "ft_home" in df else ("home_goals", "away_goals")
    df = df.dropna(subset=[home_col, away_col])

    table = {o: {} for o in OUTCOMES}
    for h, a in zip(df[home_col].astype(int), df[away_col].astype(int)):
        h, a = min(h, MAX_GOALS), min(a, MAX_GOALS)
        key = f"{h}-{a}"
        bucket = table[outcome_of(h, a)]
        bucket[key] = bucket.get(key, 0) + 1
    return table


def save_table(table=None, path=TABLE_JSON):
    table = build_table() if table is None else table
    payload = {"_comment": "Scoreline counts per 90-minute outcome, built by "
                           "model/scorelines.py from fixtures_25.csv (friendlies "
                           "excluded). Rebuild with: python -m model.scorelines",
               "matches": sum(sum(b.values()) for b in table.values()),
               "table": table}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Sampling (pure Python side)
# ---------------------------------------------------------------------------

class ScorelineSampler:
    """Draws a (home_goals, away_goals) pair given the outcome."""

    def __init__(self, table, source="table"):
        self.source = source
        self._keys = {}
        self._cum = {}
        for outcome in OUTCOMES:
            items = sorted(table[outcome].items())
            keys = [tuple(int(v) for v in k.split("-")) for k, _ in items]
            weights = [float(w) for _, w in items]
            if not keys or sum(weights) <= 0:
                raise ValueError(f"scoreline table has no entry for {outcome!r}")
            for (h, a) in keys:
                if outcome_of(h, a) != outcome:
                    raise ValueError(f"{h}-{a} listed under {outcome!r}")
            self._keys[outcome] = keys
            self._cum[outcome] = list(accumulate(weights))
        self.matches = int(sum(sum(b.values()) for b in table.values()))

    @classmethod
    def load(cls, path=TABLE_JSON):
        path = Path(path)
        if path.is_file():
            raw = json.loads(path.read_text(encoding="utf-8"))
            return cls(raw["table"], source=path.name)
        return cls(FALLBACK, source="fallback")

    def sample(self, outcome, rng):
        """One scoreline for `outcome` in {"home", "draw", "away"}."""
        cum = self._cum[outcome]
        u = rng.random() * cum[-1]
        return self._keys[outcome][bisect(cum, u)]

    def sample_extra_time(self, rng, keep=ET_KEEP):
        """A 30-minute score: a full-match sample, each goal kept with p = keep.

        The outcome is drawn uniformly from the three, then thinned. The
        uniform choice is deliberate: extra time is not a home fixture in
        any meaningful sense, and the thinning flattens the outcome
        anyway (a 2-1 kept at 1/3 is 0-0 more often than not).
        """
        outcome = OUTCOMES[int(rng.random() * 3)]
        h, a = self.sample(outcome, rng)
        return (sum(1 for _ in range(h) if rng.random() < keep),
                sum(1 for _ in range(a) if rng.random() < keep))

    def probability(self, outcome, home_goals, away_goals):
        """P(this scoreline | outcome), for the expert log."""
        keys, cum = self._keys[outcome], self._cum[outcome]
        try:
            i = keys.index((home_goals, away_goals))
        except ValueError:
            return 0.0
        weight = cum[i] - (cum[i - 1] if i else 0.0)
        return weight / cum[-1]


if __name__ == "__main__":
    out = save_table()
    sampler = ScorelineSampler.load(out)
    print(f"wrote {out} ({sampler.matches} matches)")
    rng = random.Random(1)
    for outcome in OUTCOMES:
        print(outcome, [sampler.sample(outcome, rng) for _ in range(8)])
    print("extra time", [sampler.sample_extra_time(rng) for _ in range(8)])
