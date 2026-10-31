"""Play the league phase and rank the 36 clubs.

Input: the matchdays produced by matchdays_ucl.py (8 days of 18 fixtures
for UCL/UEL, 6 days for UECL). Output: every Match, and a ranked table.

The table follows the UEFA tiebreaker chain for the 36-club league
phase (Regulations of the UEFA Champions League 2024/25, art. 17.01,
same wording in the UEL and UECL regulations):

    a. points                       3 / 1 / 0
    b. goal difference
    c. goals scored
    d. away goals scored
    e. wins
    f. away wins
    g. points obtained collectively by the club's league-phase opponents
    h. (goal difference of opponents, goals of opponents: skipped, they
        never decided anything in practice and cost a second pass)
    i. disciplinary points          not modelled
    j. club coefficient             replaced by the club's Elo rating
                                    BEFORE the tournament

Head-to-head is not in the chain: in a 36-club league where each pair
plays at most once, UEFA dropped it. Note also that (j) uses the
pre-tournament rating on purpose: the in-simulation rating would let a
club's own results decide its tiebreak twice.
"""


class Row:
    """One club's line in the table."""

    __slots__ = ("club", "played", "wins", "draws", "losses", "gf", "ga",
                 "away_gf", "away_wins", "points", "opponents", "opp_points",
                 "seed_elo", "rank")

    def __init__(self, club, seed_elo):
        self.club = club
        self.played = self.wins = self.draws = self.losses = 0
        self.gf = self.ga = self.away_gf = self.away_wins = self.points = 0
        self.opponents = []
        self.opp_points = 0
        self.seed_elo = seed_elo
        self.rank = None

    @property
    def gd(self):
        return self.gf - self.ga

    def record(self, goals_for, goals_against, away, opponent):
        self.played += 1
        self.gf += goals_for
        self.ga += goals_against
        self.opponents.append(opponent)
        if away:
            self.away_gf += goals_for
        if goals_for > goals_against:
            self.wins += 1
            self.points += 3
            if away:
                self.away_wins += 1
        elif goals_for == goals_against:
            self.draws += 1
            self.points += 1
        else:
            self.losses += 1

    def sort_key(self):
        """Bigger is better on every field, so sort descending on this tuple."""
        return (self.points, self.gd, self.gf, self.away_gf, self.wins,
                self.away_wins, self.opp_points, self.seed_elo)

    def as_dict(self):
        return {"rank": self.rank, "club": self.club, "P": self.played,
                "W": self.wins, "D": self.draws, "L": self.losses,
                "GF": self.gf, "GA": self.ga, "GD": self.gd, "Pts": self.points}


def play_league_phase(engine, matchdays):
    """Every fixture of every matchday, in order. Returns [[Match, ...], ...]."""
    played = []
    for number, day in enumerate(matchdays, start=1):
        engine.section(f"Matchday {number}")
        # sorted(): the matchday lists come out of a set-based search,
        # so their order is not stable. Sorting makes the same seed give
        # the same simulation, which is the only way to reproduce a bug.
        played.append([engine.play(home, away, "league", label=f"MD{number}")
                       for home, away in sorted(day)])
    return played


def build_table(clubs, played, seed_ratings):
    """Rank `clubs` from the matches. Returns rows in table order, rank set."""
    rows = {club: Row(club, seed_ratings.get(club, 1500.0)) for club in clubs}
    for day in played:
        for m in day:
            rows[m.home].record(m.home_goals, m.away_goals, False, m.away)
            rows[m.away].record(m.away_goals, m.home_goals, True, m.home)
    # Tiebreaker (g) needs everyone's points first, hence the second loop.
    for row in rows.values():
        row.opp_points = sum(rows[o].points for o in row.opponents)

    ordered = sorted(rows.values(), key=Row.sort_key, reverse=True)
    for rank, row in enumerate(ordered, start=1):
        row.rank = rank
    return ordered


def explain_ties(ordered):
    """Lines for the log: which tiebreaker separated clubs level on points."""
    names = ("points", "goal difference", "goals scored", "away goals",
             "wins", "away wins", "opponents' points", "pre-tournament Elo")
    lines = []
    for above, below in zip(ordered, ordered[1:]):
        if above.points != below.points:
            continue
        ka, kb = above.sort_key(), below.sort_key()
        for i, (va, vb) in enumerate(zip(ka, kb)):
            if va != vb:
                lines.append(f"{above.rank}. {above.club} ahead of {below.rank}. "
                             f"{below.club}: level on points, split by {names[i]} "
                             f"({va:g} v {vb:g})")
                break
        else:
            # sorted() is stable: clubs equal on every field keep the
            # order of `clubs`, which is the pot order, not the alphabet.
            lines.append(f"{above.rank}. {above.club} and {below.rank}. {below.club}: "
                         f"identical on every tiebreaker, kept in pot order")
    return lines


def format_table(ordered, width=26):
    """Plain text table for the log and the console."""
    head = f"{'#':>2}  {'Club':{width}} {'P':>2} {'W':>2} {'D':>2} {'L':>2} {'GF':>3} {'GA':>3} {'GD':>4} {'Pts':>3}"
    lines = [head, "-" * len(head)]
    for r in ordered:
        lines.append(f"{r.rank:>2}  {r.club[:width]:{width}} {r.played:>2} {r.wins:>2} "
                     f"{r.draws:>2} {r.losses:>2} {r.gf:>3} {r.ga:>3} {r.gd:>+4} {r.points:>3}")
    return lines
