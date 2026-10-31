"""Draw engine for the 8-match league phase: Champions League and Europa League.

Both competitions run the exact same format -- 36 clubs, four pots of nine,
eight opponents per club (two from every pot, one home and one away) -- so
they share one engine and differ only by the pot lists at the top of this
file. Pick which one with generate_draw(comp='UCL') or comp='UEL'.

The interface can also hand in its own `pots` and `countries` (club
replacement), in which case nothing is read from disk at all.
"""

import csv
import random
import time
from collections import defaultdict
from functools import lru_cache
from itertools import chain
from pathlib import Path

# model/draw_ucl.py -> model/ -> UEFA/. An absolute path means the module
# works whatever folder Python was launched from, which matters now that
# the interface imports it instead of running it as a script.
BASE_DIR = Path(__file__).resolve().parents[1]
CSV_PATH = BASE_DIR / 'data' / 'processed' / 'countries_filled_25.csv'

MAX_PER_COUNTRY = 2
MAX_ATTEMPTS = 50
NODE_BUDGET = 200_000

POTS_UCL = [
    ['Real Madrid', 'Manchester City', 'Bayern Munich', 'Paris Saint-Germain',
     'Liverpool', 'Inter Milan', 'Borussia Dortmund', 'RB Leipzig', 'Barcelona'],
    ['Bayer Leverkusen', 'Atlético Madrid', 'Atalanta', 'Juventus', 'Benfica',
     'Arsenal', 'Club Brugge', 'AC Milan', 'Feyenoord'],
    ['Sporting CP', 'PSV Eindhoven', 'Lille', 'Celtic', 'Monaco',
     'Aston Villa', 'Bologna', 'Girona', 'VfB Stuttgart'],
    ['Shakhtar Donetsk', 'Dinamo Zagreb', 'Red Bull Salzburg', 'Red Star Belgrade',
     'Young Boys', 'Slovan Bratislava', 'Sparta Prague', 'Sturm Graz', 'Brest'],
]

# 2024/25 Europa League seeding pots, by 2024 UEFA club coefficient.
# Names spelt exactly as in data/processed/countries_filled_25.csv and in
# assets/images/clubs/UEL/, otherwise load_countries() and the logo
# loader would both miss.
POTS_UEL = [
    ['AS Roma', 'Manchester United', 'FC Porto', 'Ajax', 'Rangers',
     'Eintracht Frankfurt', 'Lazio', 'Tottenham', 'Slavia Praha'],
    ['Real Sociedad', 'AZ Alkmaar', 'SC Braga', 'Olympiakos Piraeus', 'Lyon',
     'PAOK', 'Fenerbahçe', 'Maccabi Tel Aviv', 'Ferencvarosi TC'],
    ['Qarabag', 'Galatasaray', 'Plzen', 'Bodo/Glimt', 'Union St. Gilloise',
     'Dynamo Kyiv', 'Ludogorets', 'FC Midtjylland', 'Malmo FF'],
    ['Athletic Club', '1899 Hoffenheim', 'Nice', 'Anderlecht', 'Twente',
     'Beşiktaş', 'FCSB', 'Rīgas FS', 'IF Elfsborg'],
]

POTS_BY_COMP = {'UCL': POTS_UCL, 'UEL': POTS_UEL}

# Kept so that anything importing POTS from this module still works.
POTS = POTS_UCL


def load_countries(path, wanted):
    wanted = set(wanted)
    found = {}
    rows_by_club = {}
    with open(path, encoding='utf-8-sig') as file:
        reader = csv.DictReader(file, skipinitialspace=True)
        for row in reader:
            club = row['Club'].strip()
            rows_by_club[club] = row['Country'].strip()
            if club in wanted:
                found[club] = row['Country'].strip()
    missing = wanted - found.keys()
    if missing:
        # The CSV now spells clubs the way the Elo file does ("Bayern
        # München"), the pots the way the badges do ("Bayern Munich").
        # Rather than keep two copies of every list in step by hand, let
        # names.py bridge the gap, and only fail on a club it cannot place.
        from model.names import resolve_all
        still_missing = []
        for res in resolve_all(sorted(missing), rows_by_club.keys()):
            if res.key is None:
                still_missing.append(res.club)
            else:
                found[res.club] = rows_by_club[res.key]
        if still_missing:
            raise ValueError(f'Clubs not found in {path}: {still_missing}')
    return found


def build_teams(pots, countries):
    teams = {}
    for pot_number, pot in enumerate(pots, start=1):
        for club in pot:
            teams[club] = {
                'country': countries[club],
                'pot': pot_number,
                'home': [],
                'away': [],
                'played': set(),             # O(1) "have we met?" check
                'counts': defaultdict(int),  # opponents faced, per country
            }
    return teams


def opponents(team):
    return chain(team['home'], team['away'])


def link(teams, host_club, guest_club):
    """Record a fixture both ways and keep the incremental trackers in sync."""
    host = teams[host_club]
    guest = teams[guest_club]
    host['home'].append(guest_club)
    guest['away'].append(host_club)
    host['played'].add(guest_club)
    guest['played'].add(host_club)
    host['counts'][guest['country']] += 1
    guest['counts'][host['country']] += 1


def unlink(teams, host_club, guest_club):
    host = teams[host_club]
    guest = teams[guest_club]
    host['home'].pop()
    guest['away'].pop()
    host['played'].discard(guest_club)
    guest['played'].discard(host_club)
    host['counts'][guest['country']] -= 1
    guest['counts'][host['country']] -= 1


def options(slot, teams, slots, pots, constraints=frozenset()):
    club, pot, is_home = slot
    me = teams[club]
    valid = []
    for other in pots[pot - 1]:
        if other == club:
            continue
        them = teams[other]
        if them['country'] == me['country']:
            continue
        if (other, me['pot'], not is_home) not in slots:
            continue
        if other in me['played']:
            continue
        if me['counts'][them['country']] >= MAX_PER_COUNTRY:
            continue
        if them['counts'][me['country']] >= MAX_PER_COUNTRY:
            continue
        # A constraint is an ORDERED pair (host, guest) meaning "host must
        # not receive guest". Which of the two pairs this slot would create
        # depends on is_home, so the flag BUILDS the pair instead of
        # guarding the test: guarding it would leave every away slot
        # unchecked, which is exactly half the fixtures.
        if ((club, other) if is_home else (other, club)) in constraints:
            continue
        valid.append(other)
    return valid


def fill(teams, slots, rng, budget, pots, constraints=frozenset()):
    if not slots:
        return True
    budget[0] -= 1
    if budget[0] < 0:
        return False

    chosen, choices = None, None
    for slot in sorted(slots):  # deterministic order: sets of str-tuples hash-randomise per process
        current = options(slot, teams, slots, pots, constraints)
        if choices is None or len(current) < len(choices):
            chosen, choices = slot, current
            if len(current) <= 1:
                break

    club, _, is_home = chosen
    me = teams[club]
    slots.discard(chosen)
    rng.shuffle(choices)

    for other in choices:
        mirror = (other, me['pot'], not is_home)
        host_club, guest_club = (club, other) if is_home else (other, club)

        link(teams, host_club, guest_club)
        slots.discard(mirror)

        if fill(teams, slots, rng, budget, pots, constraints):
            return True

        slots.add(mirror)
        unlink(teams, host_club, guest_club)

    slots.add(chosen)
    return False


def draw(teams, rng, pots=POTS_UCL, constraints=frozenset()):
    for attempt in range(1, MAX_ATTEMPTS + 1):
        for team in teams.values():
            team['home'].clear()
            team['away'].clear()
            team['played'].clear()
            team['counts'].clear()

        slots = {(club, pot, is_home)
                 for club in teams
                 for pot in range(1, len(pots) + 1)
                 for is_home in (True, False)}

        budget = [NODE_BUDGET]
        if fill(teams, slots, rng, budget, pots, constraints):
            return attempt
        if budget[0] >= 0:
            # The search ran out of OPTIONS, not out of steps: fill() is a
            # complete backtracking search, so it has tried everything and
            # no draw exists for these pots and constraints. The 49 other
            # seeds would only add about two minutes before the same
            # failure.
            extra = f' and {len(constraints)} constraint(s)' if constraints else ''
            raise RuntimeError(f'no valid draw exists for these pots{extra}: '
                               f'too many clubs from one association in a pot, '
                               f'or constraints that cannot all be met')

    # Say whether constraints were in play. Without that, an impossible
    # set of constraints and a genuine search failure look identical.
    extra = f' ({len(constraints)} constraint(s) in force)' if constraints else ''
    raise RuntimeError(f'no valid draw found in {MAX_ATTEMPTS} attempts{extra}')


def verify(teams, pots=POTS_UCL, constraints=frozenset()):
    """Re-check the finished draw against every rule; raises on a violation.

    Runs once per draw, not once per search node, so it deliberately ignores
    the 'played'/'counts' caches and recomputes everything from 'home'/'away'
    only. That way a bug in the caches can never hide itself from this check.
    """
    pot_numbers = list(range(1, len(pots) + 1))

    for club, team in teams.items():
        drawn = list(opponents(team))
        if len(drawn) != 2 * len(pots):
            raise AssertionError(f'{club} has {len(drawn)} matches')
        if len(set(drawn)) != len(drawn):
            raise AssertionError(f'{club} plays someone twice')

        for side in ('home', 'away'):
            pots_played = sorted(teams[other]['pot'] for other in team[side])
            if pots_played != pot_numbers:
                raise AssertionError(f'{club} {side} pots are {pots_played}')

        counts = defaultdict(int)
        for other in drawn:
            other_country = teams[other]['country']
            if other_country == team['country']:
                raise AssertionError(f'{club} faces {other} from the same country')
            counts[other_country] += 1
            if counts[other_country] > MAX_PER_COUNTRY:
                raise AssertionError(f'{club} faces {counts[other_country]} clubs from {other_country}')

        for other in team['home']:
            if club not in teams[other]['away']:
                raise AssertionError(f'{club} vs {other} is not mirrored')
            if (club, other) in constraints:
                raise AssertionError(
                    f'{club} hosts {other}, forbidden by a constraint')


def fixtures(teams):
    """The 144 drawn matches as (home, away) pairs."""
    return [(club, other) for club, team in teams.items() for other in team['home']]


def show(teams, pots=POTS_UCL):
    for pot_number, pot in enumerate(pots, start=1):
        print(f'\n{"=" * 60}\nPOT {pot_number}\n{"=" * 60}')
        for club in pot:
            team = teams[club]
            print(f'\n{club} ({team["country"]})')
            for side, label in (('home', 'Home'), ('away', 'Away')):
                listed = sorted(team[side], key=lambda o: teams[o]['pot'])
                drawn = ', '.join(f'{o} (P{teams[o]["pot"]})' for o in listed)
                print(f'  {label}: {drawn}')


@lru_cache(maxsize=None)
def _countries(comp='UCL'):
    """CSV read + parsed once per competition, not once per draw.

    Measured cost: ~0.09ms per call versus ~80ms for draw()+verify() -- i.e.
    the CSV was never the bottleneck (about 0.1% of total time), so don't
    expect this alone to move the needle. It's cached because it's free and
    correct to do so, not because it was slow.
    """
    clubs = tuple(chain.from_iterable(POTS_BY_COMP[comp]))
    return load_countries(CSV_PATH, clubs)


def generate_draw(*, comp='UCL', seed=None, verify_result=True,
                  pots=None, countries=None, constraints=None):
    """Run one full draw and return the completed teams dict.

    comp          -- 'UCL' or 'UEL'. Both use this engine; only the pots differ.
    seed          -- anything random.Random() accepts. Same seed -> same
                     draw, reliably now that fill() iterates sorted(slots)
                     instead of a hash-order-dependent raw set.
    verify_result -- re-check every rule before returning (default True).
                     Measured at ~0.2ms against an ~80ms draw, so there's no
                     real speed reason to disable it.
    pots          -- override the pot lists, e.g. after the user swapped a
                     club in the interface. Must keep the same shape.
    countries     -- override the {club: country} map. Required when `pots`
                     names a club that is not in countries_filled_25.csv.
    constraints   -- a SET of (host, guest) tuples: "host must not receive
                     guest". None means no constraints. It must already be a
                     set of tuples (load_template() builds it); a list of
                     lists is refused loudly rather than silently ignored,
                     because ('a','b') == ['a','b'] is False in Python and
                     the ban would simply never fire.

    Returns the teams dict: {club: {'country', 'pot', 'home', 'away', ...}}.
    """
    if seed is None:
        seed = random.random()  # evaluated fresh on every function call
    if pots is None:
        pots = POTS_BY_COMP[comp]
    if countries is None:
        countries = _countries(comp)
    if constraints is None:
        constraints = frozenset()
    elif not isinstance(constraints, (set, frozenset)):
        raise TypeError('constraints must be a set of (host, guest) tuples, '
                        f'not {type(constraints).__name__}')

    teams = build_teams(pots, countries)
    draw(teams, random.Random(seed), pots, constraints)
    if verify_result:
        verify(teams, pots, constraints)
    return teams


if __name__ == '__main__':
    # One constraint per competition, so the demo run proves the rule is
    # actually applied: the club on the left never hosts the one on the right.
    DEMO = {'UCL': {('Liverpool', 'Real Madrid')},
            'UEL': {('AS Roma', 'Lazio')}}

    for competition in ('UCL', 'UEL'):
        t0 = time.perf_counter()
        drawn = generate_draw(comp=competition, seed=-0.1,
                              constraints=DEMO[competition])
        t1 = time.perf_counter()
        show(drawn, POTS_BY_COMP[competition])
        print(f'\n{competition}: {len(fixtures(drawn))} matches drawn, '
              f'all rules satisfied, {t1 - t0:.4f}s.')
