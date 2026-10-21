"""Split a completed draw_ucl.py draw into matchdays.

Kept separate from draw_ucl.py on purpose: "who plays who" (the draw) and
"which day does each fixture happen on" (this module) are different kinds
of constraint problem, solved independently, one built on top of the other.
"""
import random
import time
from collections import defaultdict

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]   # model/ -> UEFA/
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from model.draw_ucl import generate_draw


def _schedule_matchdays_once(all_matches, num_matchdays, rng, budget):
    """Proper edge-colouring: assign each match a matchday so that no team
    appears twice on the same day. Same MRV + backtrack pattern as fill()
    in draw_ucl.py; a 'matchday' here plays the role an 'opponent' played
    there.

    Iterates sorted(remaining), not the raw set: this isn't just about
    reproducibility (see fill()'s own comment on this) -- it was measured
    to explore roughly half as many search nodes as an insertion-ordered
    dict on this exact problem, because the tie-break order the MRV
    heuristic sees changes how much of the tree gets explored. Don't
    assume a fancier data structure is faster without measuring it.
    SHuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuut up/down
    """
    remaining = set(all_matches)
    busy = defaultdict(set)   
    assigned = {}

    def options(match):
        home, away = match
        return [d for d in range(num_matchdays)
                if d not in busy[home] and d not in busy[away]]

    def backtrack():
        if not remaining:
            return True
        budget[0] -= 1
        if budget[0] < 0:
            return False

        chosen, choices = None, None
        for match in sorted(remaining):
            current = options(match)
            if choices is None or len(current) < len(choices):
                chosen, choices = match, current
                if len(current) <= 1:
                    break
        if not choices:
            return False  # this match has no legal matchday left

        home, away = chosen
        remaining.discard(chosen)
        days = list(choices)
        rng.shuffle(days)

        for day in days:
            busy[home].add(day)
            busy[away].add(day)
            assigned[chosen] = day

            if backtrack():
                return True

            del assigned[chosen]
            busy[home].discard(day)
            busy[away].discard(day)

        remaining.add(chosen)
        return False

    return assigned if backtrack() else None


def generate_matchdays(teams, *, seed=None, node_budget=200_000, max_attempts=30):
    """Split a completed draw into matchdays, UCL-style: every team plays
    exactly once per matchday, so the number of matchdays is fixed by how
    many opponents each team has (8 here) -- it's not a free parameter.

    teams         -- a completed draw_ucl.generate_draw() result.
    seed          -- anything random.Random() accepts. None (default)
                     draws a fresh seed each call, same convention as
                     generate_draw().
    node_budget   -- backtracking steps allowed per attempt.
    max_attempts  -- a single pass can dead-end on bad tie-break luck even
                     though a schedule exists (tested: every "failure" at
                     node_budget=200_000 solved instantly on a retry with a
                     different tie-break seed), so this retries with a
                     fresh seed instead of trusting one pass, same as
                     draw() retries the whole draw on MAX_ATTEMPTS.
                     Measured: ~100% success within 3 attempts across 300
                     real draws.

    Returns a list of `num_matchdays` lists, each holding that day's
    (home, away) fixtures. Every team appears in every matchday exactly
    once, as either home or away.
    """
    if seed is None:
        seed = random.random()

    all_matches = [(home, away) for home, data in teams.items() for away in data['home']]
    sample = next(iter(teams.values()))
    num_matchdays = len(sample['home']) + len(sample['away'])  # one opponent per matchday, no byes

    rng = random.Random(seed)
    for _ in range(1, max_attempts + 1):
        result = _schedule_matchdays_once(
            all_matches, num_matchdays, random.Random(rng.random()), [node_budget])
        if result is not None:
            matchdays = [[] for _ in range(num_matchdays)]
            for match, day in result.items():
                matchdays[day].append(match)
            return matchdays

    raise RuntimeError(f'no valid {num_matchdays}-:matchday schedule found in {max_attempts} attempts')


if __name__ == '__main__':
    t0 = time.perf_counter()
    teams = generate_draw()
    matchdays = generate_matchdays(teams)
    t1 = time.perf_counter()

    for day_number, day in enumerate(matchdays, start=1):
        print(f'\nMatchday {day_number}:')
        for home, away in sorted(day):
            print(f'  {home} vs {away}')

    total_matches = sum(len(day) for day in matchdays)
    print(f'\n{total_matches} matches scheduled across {len(matchdays)} matchdays, '
          f'{t1 - t0:.4f}s.')