"""The knockout phase: play-offs, round of 16, quarter-finals,
semi-finals, final. Same shape for UCL, UEL and UECL.

Who goes where (UEFA format since 2024/25, all three competitions):

    ranks 1-8     straight to the round of 16
    ranks 9-24    knockout play-off round, two legs
    ranks 25-36   eliminated

Play-off draw: seeded pairs (9-10, 11-12, 13-14, 15-16) against unseeded
pairs (23-24, 21-22, 19-20, 17-18). Which of the two seeded clubs meets
which of the two unseeded is drawn. The seeded club plays the second
leg at home.

Round of 16: 1-2 meet the winners of the 15/16 v 17/18 ties, 3-4 the
winners of 13/14 v 19/20, 5-6 the 11/12 v 21/22 winners, 7-8 the 9/10 v
23/24 winners; again drawn within the pair. The top-8 club plays the
second leg at home.

From the quarter-finals the bracket is fixed by the seed of the top-8
club in each round-of-16 tie:

    QF1 = tie(1) v tie(8)      SF1 = QF1 v QF2
    QF2 = tie(3) v tie(5)      SF2 = QF3 v QF4
    QF3 = tie(2) v tie(7)      Final = SF1 v SF2, single leg, neutral
    QF4 = tie(4) v tie(6)

Second-leg home advantage in the QF and SF is decided by a coin, as the
real bracket draw does.

Three ways to settle a two-legged tie, chosen by the user. Every one of
them uses the same logistic regression; they differ in what they ask
of it.

    "legs"       (default, Yassine's choice)
                 Each leg is played as a match and worth 1 for a win,
                 0.5 for a draw. Higher total over the two legs goes
                 through. Level (1-1, or two draws) -> a shoot-out
                 whose WINNER is one Bernoulli draw with probability
                 E_A, the Elo expected score of the second-leg host,
                 and whose SCORE is a real shoot-out sampled for that
                 winner (penalties.kick_for).
    "aggregate"  Each leg is played as a match with a scoreline. Goals
                 added over both legs. Level -> extra time (a thinned
                 scoreline, see scorelines.py) -> a penalty shoot-out
                 kicked one by one (penalties.py), 50/50 by symmetry.
                 This is the real rule (no away-goals rule since 2021).
    "oneshot"    No legs. p_A = A's win probability averaged over both
                 venues, p_B likewise, P(A advances) = p_A / (p_A + p_B).
                 One uniform draw. The ratings take one Elo step as if
                 the tie were a single neutral match.
"""

from model import penalties
from model.elo_score_updating_copy import expected_score, update_rating

METHODS = ("legs", "aggregate", "oneshot")
DEFAULT_METHOD = "legs"

# Play-off pairs, in the order that lines them up with the round-of-16
# pairs below (index 0 of PLAYOFF meets index 3 of R16_TOP, and so on).
PLAYOFF_SEEDED = ((9, 10), (11, 12), (13, 14), (15, 16))
PLAYOFF_UNSEEDED = ((23, 24), (21, 22), (19, 20), (17, 18))
R16_TOP = ((1, 2), (3, 4), (5, 6), (7, 8))
QF_BRACKET = ((1, 8), (3, 5), (2, 7), (4, 6))


class Tie:
    """A two-legged tie, or the final. `a` hosts the second leg."""

    __slots__ = ("a", "b", "stage", "method", "legs", "score_a", "score_b",
                 "extra_time", "shootout", "p_advance", "winner", "lines",
                 "seed_a", "seed_b", "tag")

    def __init__(self, a, b, stage, tag=None, seed_a=None, seed_b=None):
        self.a, self.b, self.stage, self.tag = a, b, stage, tag
        self.seed_a, self.seed_b = seed_a, seed_b
        self.method = None
        self.legs = []
        self.score_a = self.score_b = None      # aggregate goals or leg points
        self.extra_time = None                  # (goals_a, goals_b) or None
        self.shootout = None                    # penalties.Shootout or None
        self.p_advance = None                   # oneshot only
        self.winner = None
        self.lines = []

    @property
    def loser(self):
        return self.b if self.winner == self.a else self.a

    @property
    def pens(self):
        """(pens of a, pens of b), or None if there was no shoot-out."""
        return self.shootout.score_for(self.a) if self.shootout else None

    @property
    def pens_won(self):
        """(winner's pens, loser's pens), the way a report writes it: 4-3."""
        return self.shootout.score_for(self.winner) if self.shootout else None

    def __repr__(self):
        return f"Tie({self.a} v {self.b}, {self.stage}, winner={self.winner})"


# ---------------------------------------------------------------------------
# One tie
# ---------------------------------------------------------------------------

def play_tie(engine, tie, method=DEFAULT_METHOD):
    if method not in METHODS:
        raise ValueError(f"unknown two-leg method {method!r}, choose from {METHODS}") # !r means : --> uses __repr__ instead of str()
                                    # so it ignore slashes/backslahses
                                    
    
    tie.method = method
    engine.section(f"{tie.stage}: {tie.a} v {tie.b}  [{method}]")
    {"legs": _play_legs, "aggregate": _play_aggregate,
     "oneshot": _play_oneshot}[method](engine, tie)
    for line in tie.lines:
        engine.note("   " + line)
    engine.note(f"   => {tie.winner} through")
    return tie


def _two_legs(engine, tie):
    """Leg 1 at b, leg 2 at a. Both update the ratings like any match."""
    leg1 = engine.play(tie.b, tie.a, tie.stage, label=f"{tie.stage} leg 1")
    leg2 = engine.play(tie.a, tie.b, tie.stage, label=f"{tie.stage} leg 2")
    tie.legs = [leg1, leg2]
    return leg1, leg2


def _play_legs(engine, tie):
    leg1, leg2 = _two_legs(engine, tie)
    pts_a = (1.0 - leg1.s_home) + leg2.s_home        # a is away in leg 1
    pts_b = leg1.s_home + (1.0 - leg2.s_home)
    tie.score_a, tie.score_b = pts_a, pts_b
    tie.lines.append(f"leg 1: {leg1}   leg 2: {leg2}")
    tie.lines.append(f"leg points: {tie.a} {pts_a:g}, {tie.b} {pts_b:g}")
    if pts_a != pts_b:
        tie.winner = tie.a if pts_a > pts_b else tie.b
        return
    r_a, r_b = engine.ratings[tie.a], engine.ratings[tie.b]
    p_a = expected_score(r_a, r_b)
    u = engine.rng.random()
    winner = tie.a if u < p_a else tie.b
    so = penalties.kick_for(engine.rng, tie.a, tie.b, winner)
    so.p_winner, so.u = (p_a if winner == tie.a else 1.0 - p_a), u
    tie.shootout, tie.winner = so, winner
    tie.lines.append(f"level: shoot-out, P({tie.a}) = E_A = 1/(1+10^(({r_b:.1f}-{r_a:.1f})/400)) "
                     f"= {p_a:.3f}, u = {u:.4f} -> {tie.winner}")
    _log_shootout(tie, so)


def _log_shootout(tie, so):
    first, second = so.sheet()
    width = max(len(so.first), len(so.second))
    tie.lines.append(f"penalties {tie.a} {tie.pens[0]}-{tie.pens[1]} {tie.b}"
                     f"  ({so.first} kicked first)")
    tie.lines.append(f"   {so.first:{width}}  {first}   = {so.goals_first}")
    tie.lines.append(f"   {so.second:{width}}  {second}   = {so.goals_second}")


def _play_aggregate(engine, tie):
    leg1, leg2 = _two_legs(engine, tie)
    agg_a = leg1.away_goals + leg2.home_goals
    agg_b = leg1.home_goals + leg2.away_goals
    tie.score_a, tie.score_b = agg_a, agg_b
    tie.lines.append(f"leg 1: {leg1}   leg 2: {leg2}   aggregate {tie.a} {agg_a}-{agg_b} {tie.b}")
    if agg_a != agg_b:
        tie.winner = tie.a if agg_a > agg_b else tie.b
        return
    _settle_level(engine, tie, home=tie.a, away=tie.b)


def _settle_level(engine, tie, home, away):
    """Extra time, then penalties. `home` is the club hosting that leg."""
    et_home, et_away = engine.sampler.sample_extra_time(engine.rng)
    tie.extra_time = (et_home, et_away) if home == tie.a else (et_away, et_home)
    tie.lines.append(f"level after 90: extra time {home} {et_home}-{et_away} {away}")
    if et_home != et_away:
        tie.winner = home if et_home > et_away else away
        return
    so = penalties.kick(engine.rng, tie.a, tie.b)
    so.p_winner = 0.5
    tie.shootout, tie.winner = so, so.winner
    tie.lines.append(f"still level: shoot-out, every kick scored with p = {penalties.P_SCORE}")
    _log_shootout(tie, so)


def _play_oneshot(engine, tie):
    r_a, r_b = engine.ratings[tie.a], engine.ratings[tie.b]
    at_a = engine.model.probabilities(r_a, r_b, trace=engine.expert)
    at_b = engine.model.probabilities(r_b, r_a, trace=engine.expert)
    p_a = (at_a.p_home + at_b.p_away) / 2
    p_b = (at_a.p_away + at_b.p_home) / 2
    p_adv = p_a / (p_a + p_b)
    u = engine.rng.random()
    tie.p_advance = p_adv
    tie.winner = tie.a if u < p_adv else tie.b
    tie.lines.append(f"{tie.a} at home: p_win {at_a.p_home:.3f}   {tie.b} at home: "
                     f"p_win {at_b.p_home:.3f}")
    tie.lines.append(f"p_A = ({at_a.p_home:.3f} + {at_b.p_away:.3f})/2 = {p_a:.3f}   "
                     f"p_B = ({at_a.p_away:.3f} + {at_b.p_home:.3f})/2 = {p_b:.3f}")
    tie.lines.append(f"P(A advances) = {p_a:.3f} / ({p_a:.3f} + {p_b:.3f}) = {p_adv:.3f}, "
                     f"u = {u:.4f} -> {tie.winner}")
    # One Elo step, as if the tie were a single neutral match.
    k = engine.k_table[tie.stage]
    e_a = expected_score(r_a, r_b)
    s_a = 1.0 if tie.winner == tie.a else 0.0
    engine.ratings[tie.a] = update_rating(r_a, k, s_a, e_a)
    engine.ratings[tie.b] = update_rating(r_b, k, 1.0 - s_a, 1.0 - e_a)
    engine.played += 1
    tie.lines.append(f"Elo (one step, K = {k:.2f}): {tie.a} {r_a:.1f} -> {engine.ratings[tie.a]:.1f}, "
                     f"{tie.b} {r_b:.1f} -> {engine.ratings[tie.b]:.1f}")


def play_final(engine, tie):
    """Single leg on neutral ground; draw -> extra time -> penalties."""
    tie.method = "final"
    engine.section(f"Final: {tie.a} v {tie.b}")
    match = engine.play(tie.a, tie.b, "final", neutral=True, label="Final")
    tie.legs = [match]
    tie.score_a, tie.score_b = match.home_goals, match.away_goals
    tie.lines.append(f"90 minutes: {match}")
    if match.winner is not None:
        tie.winner = match.winner
    else:
        _settle_level(engine, tie, home=tie.a, away=tie.b)
    for line in tie.lines:
        engine.note("   " + line)
    engine.note(f"   => {tie.winner} are champions")
    return tie


# ---------------------------------------------------------------------------
# The bracket
# ---------------------------------------------------------------------------

def _pair_up(seeded, unseeded, rng):
    """[(s, u), (s', u')]: which seeded club meets which unseeded, by coin."""
    (s1, s2), (u1, u2) = seeded, unseeded
    if rng.random() < 0.5:
        return [(s1, u1), (s2, u2)]
    return [(s1, u2), (s2, u1)]


def draw_playoffs(by_rank, rng):
    """Eight play-off ties. Each carries `tag` = index of its seeded pair."""
    ties = []
    for slot, (seeded, unseeded) in enumerate(zip(PLAYOFF_SEEDED, PLAYOFF_UNSEEDED)):
        s_clubs = tuple(by_rank[r] for r in seeded)
        u_clubs = tuple(by_rank[r] for r in unseeded)
        for a, b in _pair_up(s_clubs, u_clubs, rng):
            ties.append(Tie(a, b, "playoff", tag=slot,
                            seed_a=_rank_of(by_rank, a), seed_b=_rank_of(by_rank, b)))
    return ties


def draw_r16(by_rank, playoff_ties, rng):
    """Eight round-of-16 ties. `tag` = rank of the top-8 club in the tie."""
    winners_by_slot = {}
    for tie in playoff_ties:
        winners_by_slot.setdefault(tie.tag, []).append(tie.winner)
    ties = []
    for index, top in enumerate(R16_TOP):
        top_clubs = tuple(by_rank[r] for r in top)
        opponents = tuple(winners_by_slot[3 - index])     # 1/2 meet the 15/16 slot
        for a, b in _pair_up(top_clubs, opponents, rng):
            ties.append(Tie(a, b, "r16", tag=_rank_of(by_rank, a),
                            seed_a=_rank_of(by_rank, a), seed_b=_rank_of(by_rank, b)))
    return ties


def _rank_of(by_rank, club):
    """Rank of `club` in {rank: club}. The reverse map is built once per dict."""
    reverse = _REVERSE.get(id(by_rank))
    if reverse is None or reverse[0] is not by_rank:
        reverse = (by_rank, {name: rank for rank, name in by_rank.items()})
        _REVERSE.clear()                    # one bracket at a time; no leak
        _REVERSE[id(by_rank)] = reverse
    return reverse[1].get(club)


_REVERSE = {}


def _next_round(previous, pairs_by_tag, stage, rng, by_rank):
    """Pair the winners of `previous` following `pairs_by_tag`; coin for home."""
    winner_by_tag = {tie.tag: tie.winner for tie in previous}
    ties = []
    for index, (t1, t2) in enumerate(pairs_by_tag):
        first, second = winner_by_tag[t1], winner_by_tag[t2]
        if rng.random() < 0.5:
            first, second = second, first
        ties.append(Tie(first, second, stage, tag=index,
                        seed_a=_rank_of(by_rank, first), seed_b=_rank_of(by_rank, second)))
    return ties


def play_knockout(engine, table, method=DEFAULT_METHOD):
    """From a ranked table to a champion. Returns {stage: [Tie, ...]}."""
    by_rank = {row.rank: row.club for row in table}
    rng = engine.rng
    rounds = {}

    engine.section("Knockout draw")
    playoffs = draw_playoffs(by_rank, rng)
    for tie in playoffs:
        engine.note(f"   play-off: {tie.a} ({tie.seed_a}) v {tie.b} ({tie.seed_b})")
    rounds["playoff"] = [play_tie(engine, tie, method) for tie in playoffs]

    r16 = draw_r16(by_rank, rounds["playoff"], rng)
    engine.section("Round of 16 draw")
    for tie in r16:
        engine.note(f"   {tie.a} ({tie.seed_a}) v {tie.b} ({tie.seed_b})")
    rounds["r16"] = [play_tie(engine, tie, method) for tie in r16]

    qf = _next_round(rounds["r16"], QF_BRACKET, "qf", rng, by_rank)
    rounds["qf"] = [play_tie(engine, tie, method) for tie in qf]

    sf = _next_round(rounds["qf"], ((0, 1), (2, 3)), "sf", rng, by_rank)
    rounds["sf"] = [play_tie(engine, tie, method) for tie in sf]

    final = _next_round(rounds["sf"], ((0, 1),), "final", rng, by_rank)[0]
    rounds["final"] = [play_final(engine, final)]
    return rounds
