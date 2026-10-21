"""Split a completed draw_uecl.py draw into its six matchdays.

The scheduling problem is identical to the Champions League one -- give
every fixture a matchday so that no club appears twice on the same day --
so this module does NOT copy the search a third time: it calls
generate_matchdays() from matchdays_ucl.py, which already reads the
number of matchdays off the draw itself (len(home) + len(away), so 8
there and 6 here) rather than hard-coding it.

What is genuinely Conference-League-specific lives here:
    verify_matchdays()      the shape checks: 6 days, 18 matches a day,
                            36 clubs playing exactly once each day
    generate_uecl_matchdays()  draw + schedule in one call, verified
"""

import random
import time
from collections import Counter
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]   # model/ -> UEFA/
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
from model.draw_uecl import fixtures, generate_draw
from model.matchdays_ucl import generate_matchdays

MATCHDAYS = 6            # six pots, one opponent from each
MATCHES_PER_DAY = 18     # 36 clubs, all playing, two clubs per match


def verify_matchdays(teams, matchdays):
    """Re-check a finished schedule against the Conference League shape.

    Recomputed from `matchdays` alone, never from the scheduler's own
    bookkeeping, so a bug in the search cannot hide from this check --
    same principle as verify() in the draw modules.
    """
    if len(matchdays) != MATCHDAYS:
        raise AssertionError(f'{len(matchdays)} matchdays, expected {MATCHDAYS}')

    scheduled = Counter()
    for day_number, day in enumerate(matchdays, start=1):
        if len(day) != MATCHES_PER_DAY:
            raise AssertionError(
                f'matchday {day_number} has {len(day)} matches, '
                f'expected {MATCHES_PER_DAY}')

        playing = Counter()
        for home, away in day:
            playing[home] += 1
            playing[away] += 1
            scheduled[(home, away)] += 1

        if len(playing) != len(teams):
            raise AssertionError(
                f'matchday {day_number} involves {len(playing)} clubs, '
                f'expected {len(teams)}')
        twice = [club for club, n in playing.items() if n > 1]
        if twice:
            raise AssertionError(
                f'matchday {day_number}: {sorted(twice)} play twice that day')

    # Every drawn fixture placed exactly once, and nothing invented.
    drawn = Counter(fixtures(teams))
    if scheduled != drawn:
        missing = sorted((drawn - scheduled).elements())
        extra = sorted((scheduled - drawn).elements())
        raise AssertionError(
            f'schedule does not match the draw: {len(missing)} missing, '
            f'{len(extra)} invented. missing={missing[:3]} extra={extra[:3]}')


def generate_uecl_matchdays(*, seed=None, teams=None, verify_result=True,
                            pots=None, countries=None):
    """Draw the Conference League league phase and split it into matchdays.

    seed          -- anything random.Random() accepts. Same seed -> same
                     draw AND same schedule.
    teams         -- reuse a draw you already have instead of drawing a new
                     one. This is what the interface passes: it runs the
                     draw first so it can animate it, then asks for the
                     matchdays of that exact draw.
    verify_result -- run verify_matchdays() before returning (default True).
    pots, countries -- forwarded to draw_uecl.generate_draw(), for the club
                     replacement feature. Ignored when `teams` is given.

    Returns (teams, matchdays): the draw, and a list of 6 lists of
    (home, away) pairs.
    """
    if seed is None:
        seed = random.random()

    if teams is None:
        teams = generate_draw(seed=seed, pots=pots, countries=countries)

    matchdays = generate_matchdays(teams, seed=seed)

    if verify_result:
        verify_matchdays(teams, matchdays)
    return teams, matchdays


if __name__ == '__main__':
    t0 = time.perf_counter()
    drawn, days = generate_uecl_matchdays(seed=-0.1)
    t1 = time.perf_counter()

    for day_number, day in enumerate(days, start=1):
        print(f'\nMatchday {day_number}:')
        for home, away in sorted(day):
            print(f'  {home} vs {away}')

    total = sum(len(day) for day in days)
    print(f'\n{total} matches scheduled across {len(days)} matchdays, '
          f'all rules satisfied, {t1 - t0:.4f}s.')
