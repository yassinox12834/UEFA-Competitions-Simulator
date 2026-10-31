"""Draw engine for the 6-match league phase: Conference League.

Different shape from draw_ucl.py: 36 clubs in six pots of six, one
opponent per pot instead of two, and the pots are paired (1-2, 3-4, 5-6)
so that a club plays one of each pair at home and the other away. Three
home games, three away, six matchdays.

The interface can hand in its own `pots` and `countries` (club
replacement), in which case nothing is read from disk at all.
"""

import csv
import random
import time
from itertools import chain
from pathlib import Path

# model/draw_uecl.py -> model/ -> UEFA/. Absolute, so the module works
# whatever folder Python was launched from -- the interface imports it
# rather than running it as a script. Deliberately not uefa.config: that
# module loads python-dotenv and an API key, neither of which a draw needs.
BASE_DIR = Path(__file__).resolve().parents[1]
CSV_PATH = BASE_DIR / 'data' / 'processed' / 'countries_filled_25.csv'

MAX_PER_COUNTRY = 2      # opponents a club may face from any single association
MAX_ATTEMPTS = 50        # full restarts before giving up
NODE_BUDGET = 200_000    # backtracking steps allowed per attempt

POTS = [
    # Pot 1
    ['Chelsea', 'FC Copenhagen', 'Gentoise', 'Fiorentina', 'Lask Linz', 'Real Betis'],
    # Pot 2
    ['Başakşehir Istanbul', 'Molde', 'Legia Warszawa', '1. FC Heidenheim', 'Djurgardens IF', 'Apoel Nicosia'],
    # Pot 3
    ['Rapid Vienna', 'Omonia Nicosia', 'HJK Helsinki', 'Guimaraes', 'FC Astana', 'Olimpija Ljubljana'],
    # Pot 4
    ['Cercle Brugge', 'Shamrock Rovers', 'The New Saints', 'FC Lugano', 'Heart Of Midlothian', 'Mlada Boleslav'],
    # Pot 5
    ['Petrocub', 'FC ST. Gallen', 'Panathinaikos', 'TSC Backa Topola', 'Borac Banja Luka', 'Jagiellonia'],
    # Pot 6
    ['Celje', 'Larne', 'Dinamo Minsk', 'Pafos', 'Vikingur Reykjavik', 'FC Noah'],
]

POTS_UECL = POTS


def load_countries(path, wanted):
    """Read the CSV once and return {club: country} for the clubs we care about."""
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
                'home': [],   # clubs this team hosts
                'away': [],   # clubs this team visits
            }
    return teams


def opponents(team):
    """Every club already drawn against this team, home and away."""
    return chain(team['home'], team['away'])


def faced_from(team, country, teams):
    """How many opponents this team already has from a given association."""
    return sum(1 for club in opponents(team) if teams[club]['country'] == country)


def options(slot, teams, slots, pots, constraints=frozenset()):
    """Clubs that can legally fill an open slot.

    A slot is (club, pot, is_home): the club still needs one game against `pot`,
    hosting it if is_home else travelling to it. Filling it also uses up the
    opponent's mirror slot against the club's own pot.

    `constraints` is a set of ordered (host, guest) pairs: "host must not
    receive guest". Same rule and same shape as draw_ucl.options().
    """
    club, pot, is_home = slot
    me = teams[club]
    valid = []

    for other in pots[pot - 1]:
        if other == club:
            continue
        them = teams[other]
        if them['country'] == me['country']:
            continue
        # The opponent must still owe the mirror game against our pot.
        if (other, me['pot'], not is_home) not in slots:
            continue
        # Teams meet at most once over the six matchdays.
        if other in me['home'] or other in me['away']:
            continue
        if faced_from(me, them['country'], teams) >= MAX_PER_COUNTRY:
            continue
        if faced_from(them, me['country'], teams) >= MAX_PER_COUNTRY:
            continue
        # is_home decides WHICH ordered pair this slot would create, so it
        # builds the pair rather than guarding the test.
        if ((club, other) if is_home else (other, club)) in constraints:
            continue
        valid.append(other)

    return valid


def paired_pot(pot):
    """Pot 1 pairs with 2, 3 with 4, 5 with 6."""
    return pot + 1 if pot in (1, 3, 5) else pot - 1


def fill(teams : dict, slots : tuple[str, str, str], rng, budget : list, pots, constraints=frozenset()):
    """Fill every remaining requirement, backtracking on dead ends."""
    if not slots:
        return True

    budget[0] -= 1
    if budget[0] < 0:
        return False

    # 1. Most-constrained slot first. sorted() rather than the raw set:
    #    a set of tuples-of-str iterates in hash order, which changes from
    #    one process to the next, so the same seed would not replay the
    #    same draw. Same reasoning as fill() in draw_ucl.py.
    chosen, choices = None, None
    for slot in sorted(slots):
        current = options(slot, teams, slots, pots, constraints)
        if choices is None or len(current) < len(choices):
            chosen, choices = slot, current
            if len(current) <= 1:
                break

    club, pot, _ = chosen
    me = teams[club]

    # 2. The real variable is "club's match against `pot`".
    #    Its values are (opponent, direction) over BOTH directions.
    candidates = []
    for is_home in (True, False):
        slot = (club, pot, is_home)
        if slot in slots:
            for other in options(slot, teams, slots, pots, constraints):
                candidates.append((other, is_home))
    rng.shuffle(candidates)

    # 3. Close the variable: both directions leave `slots` for now.
    closed = [s for s in ((club, pot, True), (club, pot, False)) if s in slots]
    slots.difference_update(closed)

    # 4. Try every value.
    for other, is_home in candidates:
        them = teams[other]

        mirror   = (other, me['pot'], not is_home)
        leftover = (other, me['pot'], is_home)
        partner  = (club,  paired_pot(pot), is_home)
        partner2 = (other, paired_pot(me['pot']), not is_home)

        host, guest = (me, them) if is_home else (them, me)
        if is_home:
            host['home'].append(other)
            guest['away'].append(club)
        else:
            host['home'].append(club)
            guest['away'].append(other)

        removed = [s for s in (mirror, leftover, partner, partner2) if s in slots]
        slots.difference_update(removed)

        if fill(teams, slots, rng, budget, pots, constraints):
            return True

        slots.update(removed)
        host['home'].pop()
        guest['away'].pop()

    # 5. Nothing worked: reopen the variable exactly as we found it.
    slots.update(closed)
    return False


def draw(teams, rng, pots=POTS, constraints=frozenset()):
    """Give every club six opponents: one home or away game per pot."""

    
    for attempt in range(1, MAX_ATTEMPTS + 1):
        for team in teams.values():
            team['home'].clear()
            team['away'].clear()

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

    extra = f' ({len(constraints)} constraint(s) in force)' if constraints else ''
    raise RuntimeError(f'no valid draw found in {MAX_ATTEMPTS} attempts{extra}')


def verify(teams, pots=POTS, constraints=frozenset()):
    """Re-check the finished draw against every rule; raises on a violation."""
    all_pots = list(range(1, len(pots) + 1))
    half = len(pots) // 2

    for club, team in teams.items():
        drawn = list(opponents(team))

        # Six opponents, no repeats, exactly one from every pot.
        if len(drawn) != len(pots):
            raise AssertionError(f'{club} has {len(drawn)} matches')
        if len(set(drawn)) != len(drawn):
            raise AssertionError(f'{club} plays someone twice')
        if sorted(teams[o]['pot'] for o in drawn) != all_pots:
            raise AssertionError(f'{club} pot coverage is '
                                 f'{sorted(teams[o]["pot"] for o in drawn)}')

        # Three home, three away.
        if len(team['home']) != half or len(team['away']) != half:
            raise AssertionError(f'{club} has {len(team["home"])} home, '
                                 f'{len(team["away"])} away')

        # Paired pots must run in opposite directions.
        for first in range(1, len(pots), 2):
            second = first + 1
            one = next(o for o in drawn if teams[o]['pot'] == first)
            two = next(o for o in drawn if teams[o]['pot'] == second)
            if (one in team['home']) == (two in team['home']):
                raise AssertionError(
                    f'{club} plays pots {first} and {second} on the same side')

        # Country rules.
        for other in drawn:
            if teams[other]['country'] == team['country']:
                raise AssertionError(f'{club} faces {other} from the same country')
            count = faced_from(team, teams[other]['country'], teams)
            if count > MAX_PER_COUNTRY:
                raise AssertionError(
                    f'{club} faces {count} clubs from {teams[other]["country"]}')

        # Every home game appears as the opponent's away game.
        for other in team['home']:
            if club not in teams[other]['away']:
                raise AssertionError(f'{club} vs {other} is not mirrored')
            if (club, other) in constraints:
                raise AssertionError(
                    f'{club} hosts {other}, forbidden by a constraint')


def fixtures(teams):
    """The 108 drawn matches as (home, away) pairs."""
    return [(club, other) for club, team in teams.items() for other in team['home']]


def show(teams, pots=POTS):
    for pot_number, pot in enumerate(pots, start=1):
        print(f'\n{"=" * 60}\nPOT {pot_number}\n{"=" * 60}')
        for club in pot:
            team = teams[club]
            print(f'\n{club} ({team["country"]})')
            for side, label in (('home', 'Home'), ('away', 'Away')):
                listed = sorted(team[side], key=lambda o: teams[o]['pot'])
                drawn = ', '.join(f'{o} (P{teams[o]["pot"]})' for o in listed)
                print(f'  {label}: {drawn}')


_COUNTRIES_CACHE = {}


def _countries():
    """CSV read + parsed once per process, not once per draw."""
    if 'default' not in _COUNTRIES_CACHE:
        clubs = list(chain.from_iterable(POTS))
        _COUNTRIES_CACHE['default'] = load_countries(CSV_PATH, clubs)
    return _COUNTRIES_CACHE['default']


def generate_draw(*, comp='UECL', seed=None, verify_result=True,
                  pots=None, countries=None, constraints=None):
    """Run one full Conference League draw and return the completed teams dict.

    Same signature as draw_ucl.generate_draw() on purpose: the interface
    picks a module by competition and then calls the two identically.

    comp          -- only 'UECL' here; accepted so the two engines share a call shape.
    seed          -- anything random.Random() accepts. Same seed -> same draw.
    verify_result -- re-check every rule before returning (default True).
    pots          -- override the pot lists, e.g. after the user swapped a
                     club in the interface. Must keep the same shape.
    countries     -- override the {club: country} map. Required when `pots`
                     names a club that is not in countries_filled_25.csv.
    constraints   -- a SET of (host, guest) tuples: "host must not receive
                     guest". None means no constraints. Must already be a set
                     of tuples; a list of lists is refused loudly, because
                     ('a','b') == ['a','b'] is False and the ban would then
                     never fire.
    """
    if comp != 'UECL':
        raise ValueError(f"draw_uecl only draws UECL, not {comp!r}")
    if seed is None:
        seed = random.random()
    if pots is None:
        pots = POTS
    if countries is None:
        countries = _countries()
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
    t0 = time.perf_counter()
    drawn = generate_draw(seed=-0.1,
                          constraints={('Chelsea', 'Real Betis')})
    t1 = time.perf_counter()

    show(drawn)
    print(f'\n{len(fixtures(drawn))} matches drawn, all rules satisfied, '
          f'{t1 - t0:.4f}s.')
