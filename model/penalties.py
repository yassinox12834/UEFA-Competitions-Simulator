"""A penalty shoot-out, kick by kick, with a score.

IFAB Law 10 in the form the simulation needs:

    1. a coin decides which club kicks first (the ABAB order);
    2. five kicks each, alternating; the shoot-out stops as soon as one
       club cannot catch up even if it scores every kick it has left;
    3. still level after five each: sudden death, one kick each, until
       one scores and the other misses in the same round.

Every kick is scored with the same probability P_SCORE. That choice is
deliberate: with equal probabilities the shoot-out is symmetric, so the
club kicking first wins exactly half the time on average, and the
"penalties at 50/50" rule of the previous version is kept. What changes
is that the result now has a score (4-3, 5-4 after sudden death, ...).

Two entry points:

    kick(rng, a, b)               a free shoot-out, returns a Shootout
    kick_for(rng, a, b, winner)   a shoot-out whose winner is already known

`kick_for` exists for the "legs" two-leg method, where the winner of a
level tie is drawn with the Elo expected score E_A (Yassine's choice).
It draws shoot-outs until one ends the right way round (rejection
sampling). Because the free shoot-out is symmetric, half of all draws
are accepted, so it takes two tries on average, and the score it
returns is a genuine shoot-out score for that winner.
"""

P_SCORE = 0.76          # share of shoot-out kicks scored, men's club football
MAX_ROUNDS = 40         # a safety net; P(still level after 40 rounds) ~ 1e-14


class Shootout:
    """The record of one shoot-out. `first` kicked first."""

    __slots__ = ("first", "second", "goals_first", "goals_second",
                 "kicks_first", "kicks_second", "winner", "p_winner", "u")

    def __init__(self, first, second, goals_first, goals_second,
                 kicks_first, kicks_second):
        self.first, self.second = first, second
        self.goals_first, self.goals_second = goals_first, goals_second
        self.kicks_first, self.kicks_second = kicks_first, kicks_second
        self.winner = first if goals_first > goals_second else second
        self.p_winner = None        # the probability used to pick the winner, if any
        self.u = None               # the uniform number that picked it

    def score_for(self, club):
        """(goals of `club`, goals of the other one)."""
        if club == self.first:
            return self.goals_first, self.goals_second
        return self.goals_second, self.goals_first

    def sheet(self):
        """'o o x o o' per club: o scored, x missed, - not taken. For the log.

        Both rows get the same length, so round n sits in the same column
        for both clubs (the club kicking second often stops one short).
        """
        mark = {True: "o", False: "x"}
        n = max(len(self.kicks_first), len(self.kicks_second))

        def row(kicks):
            return " ".join([mark[k] for k in kicks] + ["-"] * (n - len(kicks)))

        return row(self.kicks_first), row(self.kicks_second)

    def __repr__(self):
        return (f"Shootout({self.first} {self.goals_first}-{self.goals_second} "
                f"{self.second}, winner={self.winner})")


def _kick_once(random, p):
    """One shoot-out between 'first' and 'second'. `random` = rng.random."""
    ga = gb = 0
    ka, kb = [], []
    PRESSURE_DROP = 0.1 
    # Regulation: five rounds, stop as soon as the result is certain.
    for rnd in range(5):
        
        q = p - PRESSURE_DROP if rnd == 4 and ga + 1 == gb else p
        scored = random() < q
        ka.append(scored)
        ga += scored
        left = 4 - rnd                              # kicks left after this round
        if ga > gb + left + 1 or gb > ga + left:    # b has left+1 kicks to come
            return ga, gb, ka, kb
        u = p - PRESSURE_DROP if rnd == 4 and gb + 1 == ga else p
        scored = random() < u
        kb.append(scored)
        gb += scored
        if ga > gb + left or gb > ga + left:
            return ga, gb, ka, kb
    # Sudden death.
    for _ in range(MAX_ROUNDS):
        sa = random() < p
        sb = random() < p
        ka.append(sa)
        kb.append(sb)
        ga += sa
        gb += sb
        if sa != sb:
            return ga, gb, ka, kb
    # Never reached in practice; settle it rather than loop forever.
    ka.append(True)
    kb.append(False)
    return ga + 1, gb, ka, kb


def kick(rng, club_a, club_b, p=P_SCORE):
    """A free shoot-out between two clubs. The coin picks who kicks first."""
    first, second = (club_a, club_b) if rng.random() < 0.5 else (club_b, club_a)
    return Shootout(first, second, *_kick_once(rng.random, p))


def kick_for(rng, club_a, club_b, winner, p=P_SCORE):
    """A shoot-out that `winner` wins. Rejection sampling, ~2 draws on average."""
    while True:
        so = kick(rng, club_a, club_b, p)
        if so.winner == winner:
            return so
