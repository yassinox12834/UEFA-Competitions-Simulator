"""Play ONE match: probabilities, outcome, scoreline, rating update, log.

Everything the simulation does to a single fixture happens here, in
this order, and nowhere else:

    1. read both clubs' CURRENT ratings (they move during the tournament)
    2. ask the classifier for (p_home, p_draw, p_away)
    3. draw the outcome with one uniform number u in [0, 1):
           u < p_home            -> home win
           u < p_home + p_draw   -> draw
           otherwise             -> away win
    4. draw a scoreline consistent with that outcome
    5. update both ratings with the Elo step, K taken from coefs.json
       for this competition and stage
    6. if the engine is in expert mode, append every number above to
       the trace

The league phase and the knockout rounds both call play(); they differ
only in what they do with the Match objects it returns.

Elo, with every symbol (same formulas as elo_score_updating_copy.py):

    E_A = 1 / (1 + 10^((R_B - R_A) / 400))    expected score of A
    S_A = 1 / 0.5 / 0                         actual: win / draw / loss
    R_A' = R_A + K (S_A - E_A)                the update
    K   = min(k_base * m_comp * m_stage, k_max)
"""

import json
import math
from functools import lru_cache
from pathlib import Path

from model.elo_score_updating import expected_score, update_rating
from model.predictor import format_trace
from model.scorelines import outcome_of

BASE_DIR = Path(__file__).resolve().parents[1]
COEFS_JSON = BASE_DIR / "data" / "reference" / "coefs.json"

# Stage names as they are spelt in coefs.json, keyed by the simulation's
# own round names.
STAGE_KEYS = {
    "league": "League",
    "playoff": "Playoff",
    "r16": "Round of 16",
    "qf": "Quarter Final",
    "sf": "Semi Final",
    "final": "Final",
}
STAGE_LABELS = {
    "league": "League phase",
    "playoff": "Knockout play-offs",
    "r16": "Round of 16",
    "qf": "Quarter-finals",
    "sf": "Semi-finals",
    "final": "Final",
}
DEFAULT_ELO = 1500.0
_S_HOME = {"home": 1.0, "draw": 0.5, "away": 0.0}


def load_k_table(comp, path=COEFS_JSON):
    """{stage: K} for one competition, plus the raw settings for the log.

    Copies of a cached read: a Monte Carlo of 1000 runs used to parse
    coefs.json 1000 times.
    """
    table, settings = _load_k_table(comp, str(path))
    return dict(table), dict(settings)


@lru_cache(maxsize=None)
def _load_k_table(comp, path):
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    k_base, k_max = float(raw["k_base"]), float(raw["k_max"])
    block = raw["competitions"][comp]
    comp_mult = float(block["comp_mult"])
    table = {}
    for stage, key in STAGE_KEYS.items():
        stage_mult = float(block["stages"][key])
        table[stage] = min(k_base * comp_mult * stage_mult, k_max)
    return table, {"k_base": k_base, "k_max": k_max, "comp_mult": comp_mult,
                   "stage_mult": {s: float(block["stages"][k]) for s, k in STAGE_KEYS.items()}}


class Match:
    """One played fixture and every number that produced it."""

    __slots__ = ("home", "away", "stage", "neutral", "elo_home", "elo_away",
                 "probs", "u", "outcome", "home_goals", "away_goals", "k",
                 "e_home", "s_home", "elo_home_after", "elo_away_after", "label")

    def __init__(self, home, away, stage, neutral, elo_home, elo_away, probs,
                 u, outcome, home_goals, away_goals, k, e_home, s_home,
                 elo_home_after, elo_away_after, label):
        # Positional on purpose: this runs ~190 times per season, and a
        # loop of setattr over **kw cost more than the match itself.
        self.home, self.away, self.stage, self.neutral = home, away, stage, neutral
        self.elo_home, self.elo_away, self.probs, self.u = elo_home, elo_away, probs, u
        self.outcome, self.home_goals, self.away_goals = outcome, home_goals, away_goals
        self.k, self.e_home, self.s_home = k, e_home, s_home
        self.elo_home_after, self.elo_away_after, self.label = elo_home_after, elo_away_after, label

    @property
    def winner(self):
        """The club that won in 90 minutes, or None for a draw."""
        if self.outcome == "home":
            return self.home
        if self.outcome == "away":
            return self.away
        return None

    

    @property
    def score(self):
        return f"{self.home_goals}-{self.away_goals}"

    def __repr__(self):
        return f"{self.home} {self.score} {self.away}"


class MatchEngine:
    """Holds the ratings, the model, the sampler, the RNG and the trace."""

    def __init__(self, model, sampler, ratings, k_table, rng, expert=False,
                 k_settings=None):
        self.model = model
        self.sampler = sampler
        self.ratings = dict(ratings)        # copied: a run must not leak into the next
        self.k_table = k_table
        self.k_settings = k_settings or {}
        self.rng = rng
        self.expert = expert
        self.trace = []                     # list of str, sections start with "== "
        self.played = 0

    # ---------- the log ----------
    def section(self, title):
        if self.expert:
            self.trace.append("== " + title)

    def note(self, text):
        if self.expert:
            self.trace.append(text)

    # ---------- one match ----------
    def play(self, home, away, stage, neutral=False, label=None):
        if not self.expert and not neutral:
            return self._play_fast(home, away, stage, label)
        return self._play_full(home, away, stage, neutral, label)

    def _play_fast(self, home, away, stage, label):
        """play() without the log: same maths, same RNG calls, same result.

        Inlined because this is the whole cost of a Monte Carlo run. Every
        line is the one-line version of a call in _play_full:
            probabilities()   -> softmax of three straight lines in x'
            expected_score()  -> 1 / (1 + 10^((R_away - R_home)/400))
            update_rating()   -> R + K (S - E)
        test_fast_path_matches_full_path checks that both agree exactly.
        """
        ratings = self.ratings
        r_home = ratings.get(home, DEFAULT_ELO)
        r_away = ratings.get(away, DEFAULT_ELO)
        m = self.model
        xs = (r_home - r_away - m.mean) / m.scale
        (ca, cd, ch), (ba, bd, bh) = m.coef, m.intercept
        za, zd, zh = ca * xs + ba, cd * xs + bd, ch * xs + bh
        top = za if za > zd else zd
        if zh > top:
            top = zh
        ea, ed, eh = math.exp(za - top), math.exp(zd - top), math.exp(zh - top)
        total = ea + ed + eh
        p_home, p_draw = eh / total, ed / total

        rng = self.rng
        u = rng.random()
        if u < p_home:
            outcome, s_home = "home", 1.0
        elif u < p_home + p_draw:
            outcome, s_home = "draw", 0.5
        else:
            outcome, s_home = "away", 0.0
        hg, ag = self.sampler.sample(outcome, rng)

        k = self.k_table[stage]
        e_home = 1.0 / (1.0 + 10.0 ** ((r_away - r_home) / 400.0))
        new_home = r_home + k * (s_home - e_home)
        new_away = r_away + k * ((1.0 - s_home) - (1.0 - e_home))
        ratings[home] = new_home
        ratings[away] = new_away
        self.played += 1
        return Match(home, away, stage, False, r_home, r_away, None, u, outcome,
                     hg, ag, k, e_home, s_home, new_home, new_away, label)

    def _play_full(self, home, away, stage, neutral, label):
        r_home = self.ratings.get(home, DEFAULT_ELO)
        r_away = self.ratings.get(away, DEFAULT_ELO)
        probs = self.model.probabilities(r_home, r_away, neutral=neutral,
                                         trace=self.expert)

        u = self.rng.random()
        if u < probs.p_home:
            outcome = "home"
        elif u < probs.p_home + probs.p_draw:
            outcome = "draw"
        else:
            outcome = "away"
        hg, ag = self.sampler.sample(outcome, self.rng)
        assert outcome_of(hg, ag) == outcome

        k = self.k_table[stage]
        e_home = expected_score(r_home, r_away)
        s_home = _S_HOME[outcome]
        new_home = update_rating(r_home, k, s_home, e_home)
        new_away = update_rating(r_away, k, 1.0 - s_home, 1.0 - e_home)
        self.ratings[home], self.ratings[away] = new_home, new_away
        self.played += 1

        match = Match(home, away, stage, neutral, r_home, r_away, probs, u,
                      outcome, hg, ag, k, e_home, s_home, new_home, new_away, label)
        if self.expert:
            self._log(match)
        return match

    def _log(self, m):
        t = self.trace
        where = " (neutral venue)" if m.neutral else ""
        t.append(f"-- {m.label + ': ' if m.label else ''}{m.home} v {m.away}{where}")
        for line in format_trace(m.probs.trace):
            t.append("   " + line)
        t.append(f"   p_home = {m.probs.p_home:.3f}   p_draw = {m.probs.p_draw:.3f}   "
                 f"p_away = {m.probs.p_away:.3f}")
        cut1, cut2 = m.probs.p_home, m.probs.p_home + m.probs.p_draw
        t.append(f"   u = {m.u:.4f}  ->  {m.outcome.upper()}  "
                 f"(home if u < {cut1:.3f}, draw if u < {cut2:.3f}, else away)")
        p_score = self.sampler.probability(m.outcome, m.home_goals, m.away_goals)
        t.append(f"   scoreline {m.score}  (P = {p_score:.3f} given {m.outcome})")
        t.append(f"   Elo: E_home = 1/(1+10^(({m.elo_away:.1f}-{m.elo_home:.1f})/400)) = {m.e_home:.3f}   "
                 f"S_home = {m.s_home}   K = {m.k:.2f}")
        t.append(f"        {m.home}: {m.elo_home:.1f} -> {m.elo_home_after:.1f} "
                 f"({m.elo_home_after - m.elo_home:+.1f})   "
                 f"{m.away}: {m.elo_away:.1f} -> {m.elo_away_after:.1f} "
                 f"({m.elo_away_after - m.elo_away:+.1f})")
