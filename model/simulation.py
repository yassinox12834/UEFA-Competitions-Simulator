"""Simulate a whole competition from a finished draw.

    result = simulate(comp, teams, matchdays, SimConfig(...))
    probs  = monte_carlo(comp, teams, matchdays, SimConfig(...), runs=300)

`teams` and `matchdays` are what draw_ucl / draw_uecl and matchdays_ucl
produce, so the simulation starts exactly where the draw screen stops.

What one run does, in order:

    1. resolve every club of the pots to its Elo rating (model/names.py);
       a club that cannot be found starts at DEFAULT_ELO and is reported
    2. play the league phase, matchday by matchday, ratings moving after
       every match (model/league_phase.py, model/match_engine.py)
    3. rank the 36 clubs with the UEFA tiebreaker chain
    4. play the knockout phase to the final (model/knockout.py)
    5. return everything, plus the expert trace if it was asked for

Monte Carlo repeats step 2 to 4 with a fresh RNG each time and counts
how often each club reaches each stage. One run is an anecdote; the
counts are the prediction.
"""

import json
import os
import random
import time
from concurrent.futures.process import BrokenProcessPool
from datetime import datetime
from pathlib import Path
from pickle import PicklingError

from model import knockout, league_phase
from model.match_engine import DEFAULT_ELO, STAGE_LABELS, MatchEngine, load_k_table
from model.names import ALIASES, resolve_all
from model.predictor import MatchModel
from model.scorelines import ScorelineSampler
from uefa.paths import USER_DIR

BASE_DIR = Path(__file__).resolve().parents[1]
ELO_JSON = BASE_DIR / "data" / "processed" / "eeelo_final.json"
LOG_DIR = USER_DIR / "data" / "processed"

STAGES = ("top8", "top24", "r16", "qf", "sf", "final", "winner")
STAGE_TITLES = {"top8": "Top 8", "top24": "Top 24", "r16": "Round of 16",
                "qf": "Quarter-finals", "sf": "Semi-finals", "final": "Final",
                "winner": "Winner"}


class SimConfig:
    """Everything the user can choose on the simulation screen."""

    def __init__(self, method=knockout.DEFAULT_METHOD, expert=False, seed=None,
                 runs=1):
        if method not in knockout.METHODS:
            raise ValueError(f"method must be one of {knockout.METHODS}")
        self.method = method
        self.expert = expert
        # Python's shared generator is only touched when a seed has to be
        # invented: a given seed must not change the state of `random` for
        # the rest of the program.
        if seed is None:
            seed = random.random() + random.randint(-400, 400)
        self.seed = seed
        self.runs = int(runs)

    def as_dict(self):
        return {"method": self.method, "expert": self.expert,
                "seed": self.seed, "runs": self.runs}


class Resources:
    """The three files a simulation needs, loaded once and shared."""

    def __init__(self, model = None, sampler=None, ratings=None):
        self.model = model or MatchModel.load()
        self.sampler = sampler or ScorelineSampler.load()
        if ratings is None:
            ratings = {c: float(r) for c, r in
                       json.loads(ELO_JSON.read_text(encoding="utf-8")).items()}
        self.ratings = ratings
        self._seeds = {}

    def seeds_for(self, clubs):
        """seed_ratings(clubs), computed once per set of clubs.

        Name resolution builds a normalised index of ~1500 Elo names; it
        was 60 % of a Monte Carlo run when it was redone every season.
        """
        key = tuple(clubs)
        if key not in self._seeds:
            self._seeds[key] = seed_ratings(clubs, self.ratings)
        seeds, resolutions = self._seeds[key]
        return dict(seeds), resolutions


class SimulationResult:
    __slots__ = ("comp", "config", "clubs", "resolutions", "seed_ratings",
                 "league", "table", "rounds", "champion", "final_ratings",
                 "trace", "elapsed", "warnings", "k_settings")

    def __init__(self, **kw):
        for name in self.__slots__:
            setattr(self, name, kw.get(name))

    def stage_reached(self):
        """{club: furthest stage key}, for the summary and Monte Carlo."""
        reached = {}
        for row in self.table:
            reached[row.club] = "top24" if row.rank <= 24 else "league"
            if row.rank <= 8:
                reached[row.club] = "top8"
        for stage in ("r16", "qf", "sf", "final"):
            for tie in self.rounds.get(stage, ()):
                reached[tie.a] = reached[tie.b] = stage
        reached[self.champion] = "winner"
        return reached


# ---------------------------------------------------------------------------
# Ratings for the pots
# ---------------------------------------------------------------------------

def seed_ratings(clubs, ratings):
    """{club as spelt in the pots: Elo}, and the resolution table."""
    resolutions = resolve_all(clubs, ratings.keys())
    seeds = {}
    for res in resolutions:
        seeds[res.club] = ratings[res.key] if res.key is not None else DEFAULT_ELO
    return seeds, resolutions


# ---------------------------------------------------------------------------
# One run
# ---------------------------------------------------------------------------

def simulate(comp, teams, matchdays, config=None, resources=None):
    config = config or SimConfig()
    res = resources or Resources()
    t0 = time.perf_counter()

    clubs = list(teams)
    seeds, resolutions = res.seeds_for(clubs)
    k_table, k_settings = load_k_table(comp)
    engine = MatchEngine(res.model, res.sampler, seeds, k_table,
                         random.Random(config.seed), expert=config.expert,
                         k_settings=k_settings)
    warnings = [f"{r.club}: not found in the Elo file, starting at {DEFAULT_ELO:.0f}"
                for r in resolutions if r.key is None]
    warnings += [f"{r.club}: alias {ALIASES.get(r.club)!r} is not in the Elo file; "
                 f"matched to {r.key!r} by {r.how[len('alias-'):]} search, fix the alias"
                 for r in resolutions if r.how.startswith("alias-") and r.key is not None]

    if config.expert:
        _log_header(engine, comp, config, res, resolutions, seeds, k_settings)

    league = league_phase.play_league_phase(engine, matchdays)
    table = league_phase.build_table(clubs, league, seeds)
    if config.expert:
        engine.section("League phase table")
        for line in league_phase.format_table(table):
            engine.note("   " + line)
        for line in league_phase.explain_ties(table):
            engine.note("   " + line)

    rounds = knockout.play_knockout(engine, table, config.method)
    champion = rounds["final"][0].winner

    return SimulationResult(
        comp=comp, config=config, clubs=clubs, resolutions=resolutions,
        seed_ratings=seeds, league=league, table=table, rounds=rounds,
        champion=champion, final_ratings=dict(engine.ratings),
        trace=engine.trace, elapsed=time.perf_counter() - t0,
        warnings=warnings, k_settings=k_settings)


def _log_header(engine, comp, config, res, resolutions, seeds, k):
    engine.section(f"{comp} simulation, seed {config.seed!r}, two-leg method '{config.method}'")
    meta = res.model.meta
    engine.note(f"   classifier: {meta.get('rows')} rows, seasons {meta.get('seasons')}, "
                f"trained {meta.get('trained_at')}")
    hold = meta.get("holdout") or {}
    if hold:
        # predictor.train() writes train_fraction / train_rows / test_rows;
        # holdout_season is the key of weights trained before 1.0.2.
        where = (f"newest {1 - hold['train_fraction']:.0%} of matches, "
                 f"{hold.get('train_rows')} train / {hold.get('test_rows')} test"
                 if "train_fraction" in hold else f"season {hold.get('holdout_season')}")
        engine.note(f"   holdout ({where}): log loss "
                    f"{hold.get('log_loss', 0):.4f} (no-skill {hold.get('log_loss_no_skill', 0):.4f})")
    engine.note(f"   weights: coef away/draw/home = {res.model.coef}, "
                f"intercept = {res.model.intercept}, mean = {res.model.mean:.3f}, "
                f"scale = {res.model.scale:.3f}")
    engine.note(f"   scorelines: {res.sampler.source} ({res.sampler.matches} matches)")
    engine.note(f"   Elo K: k_base {k['k_base']:g} x comp_mult {k['comp_mult']:g} x stage_mult, "
                f"capped at {k['k_max']:g}: " +
                ", ".join(f"{s} {engine.k_table[s]:.2f}" for s in engine.k_table))
    engine.section("Starting ratings")
    for r in sorted(resolutions, key=lambda r: -seeds[r.club]):
        how = "" if r.how == "exact" else f"   [{r.how}: {r.key!r}]" if r.key else "   [NOT FOUND, default]"
        engine.note(f"   {r.club:28} {seeds[r.club]:7.1f}{how}")


class MonteCarloResult:
    __slots__ = ("comp", "runs", "counts", "points", "elapsed", "config")

    def __init__(self, comp, runs, counts, points, elapsed, config):
        self.comp, self.runs, self.counts = comp, runs, counts
        self.points, self.elapsed, self.config = points, elapsed, config

    def probability(self, club, stage):
        return self.counts[club][stage] / self.runs

    def rows(self):
        """[(club, mean points, {stage: p}), ...] sorted by P(winner), P(final), ..."""
        out = []
        for club, counts in self.counts.items():
            probs = {s: counts[s] / self.runs for s in STAGES}
            out.append((club, self.points[club] / self.runs, probs))
        out.sort(key=lambda r: tuple(-r[2][s] for s in reversed(STAGES)) + (-r[1],))
        return out


PARALLEL_FROM = 2000      

def monte_carlo(comp, teams, matchdays, config=None, runs=200, resources=None,
                progress=None, workers=None):
    """Run the tournament `runs` times. `progress(done, runs)` is called as runs finish.

    The seed of every run is drawn up front from config.seed, so the
    counts are the same whether the runs are played in this process or
    split across `workers` processes (None = automatic: parallel from
    PARALLEL_FROM runs, one process per core, at most 8).
    """
    config = config or SimConfig()
    t0 = time.perf_counter()
    base = random.Random(config.seed)
    seeds = [base.random() for _ in range(runs)]
    clubs = list(teams)
    days = [sorted(day) for day in matchdays]      # sorted once, not once per run

    if workers is None:
        workers = min(os.cpu_count() or 1, 8) if runs >= PARALLEL_FROM else 1
    # The SAME resources go to the worker processes. They used to build
    # their own Resources() from the default files, so custom ratings (or
    # a custom model) were silently ignored as soon as the run count
    # crossed PARALLEL_FROM, and 1 and 2 processes gave different counts.
    res = resources or Resources()
    counts = points = None
    if workers > 1:
        try:
            counts, points = _mc_parallel(comp, clubs, days, config.method, seeds,
                                          workers, progress, res)
        except (BrokenProcessPool, OSError, PicklingError):
            # No usable process pool here (a sandbox that forbids new
            # processes, a frozen app without freeze_support...): play the
            # runs in this process instead. Any OTHER exception is a real
            # error in a run, and is raised as it is rather than hidden
            # behind a slower second attempt. Cancelled passes through.
            counts = points = None
    if counts is None:
        counts, points = _mc_block(comp, clubs, days, config.method, seeds, res,
                                   progress, runs)
    return MonteCarloResult(comp, runs, counts, points, time.perf_counter() - t0, config)


class Cancelled(Exception):
    """Raise it from a progress callback to abandon a Monte Carlo."""


def _mc_block(comp, clubs, days, method, seeds, res, progress=None, total=None):
    """Play one run per seed; return ({club: {stage: n}}, {club: points})."""
    counts = {club: dict.fromkeys(STAGES, 0) for club in clubs}
    points = dict.fromkeys(clubs, 0)
    # "top8" is off the chain: a club can reach the R16 through the
    # play-offs without it. Everything else nests: a semi-finalist was a
    # quarter-finalist, was in the R16, was in the top 24.
    chain = ("top24", "r16", "qf", "sf", "final", "winner")
    upto = {stage: chain[:i + 1] for i, stage in enumerate(chain)}
    upto["top8"] = upto["top24"]
    for i, seed in enumerate(seeds):
        run_cfg = SimConfig(method, expert=False, seed=seed)
        result = simulate(comp, clubs, days, run_cfg, res)
        for row in result.table:
            points[row.club] += row.points
            if row.rank <= 8:
                counts[row.club]["top8"] += 1
        for club, stage in result.stage_reached().items():
            for s in upto.get(stage, ()):
                counts[club][s] += 1
        if progress is not None:
            progress(i + 1, total or len(seeds))
    return counts, points


_WORKER_RES = None


def _mc_worker_init(res=None):
    """Runs once in each worker process: keep the resources it was sent."""
    global _WORKER_RES
    _WORKER_RES = res if res is not None else Resources()


def _mc_worker(args):
    comp, clubs, days, method, seeds = args
    return len(seeds), _mc_block(comp, clubs, days, method, seeds, _WORKER_RES)


def _mc_parallel(comp, clubs, days, method, seeds, workers, progress, res=None):
    from concurrent.futures import ProcessPoolExecutor, as_completed
    # Small chunks so the progress bar moves; ~4 chunks per worker.
    size = max(50, len(seeds) // (workers * 4))
    chunks = [seeds[i:i + size] for i in range(0, len(seeds), size)]
    counts = {club: dict.fromkeys(STAGES, 0) for club in clubs}
    points = dict.fromkeys(clubs, 0)
    done = 0
    pool = ProcessPoolExecutor(max_workers=workers, initializer=_mc_worker_init,
                               initargs=(res,))
    try:
        futures = [pool.submit(_mc_worker, (comp, clubs, days, method, chunk))
                   for chunk in chunks]
        for fut in as_completed(futures):
            n, (c, p) = fut.result()
            for club in clubs:
                points[club] += p[club]
                row, part = counts[club], c[club]
                for s in STAGES:
                    row[s] += part[s]
            done += n
            if progress is not None:
                progress(done, len(seeds))       # may raise Cancelled
    finally:
        # Cancelled or failed: drop the chunks not started yet, do not wait.
        pool.shutdown(wait=False, cancel_futures=True)
    return counts, points


# ---------------------------------------------------------------------------
# Text export
# ---------------------------------------------------------------------------

def summary_lines(result):
    """The result as plain text, with or without the expert trace."""
    lines = [f"{result.comp} simulation  |  {datetime.now():%Y-%m-%d %H:%M}  |  "
             f"seed {result.config.seed!r}  |  two-leg method {result.config.method}  |  "
             f"{result.elapsed * 1000:.0f} ms", ""]
    for w in result.warnings:
        lines.append("WARNING " + w)
    lines.append("LEAGUE PHASE")
    lines += league_phase.format_table(result.table)
    lines.append("")
    for stage in ("playoff", "r16", "qf", "sf", "final"):
        lines.append(STAGE_LABELS[stage].upper())
        for tie in result.rounds[stage]:
            lines.append(f"  {describe_tie(tie)}")
        lines.append("")
    lines.append(f"CHAMPIONS: {result.champion}")
    return lines


def describe_tie(tie):
    if tie.method == "final":
        m = tie.legs[0]
        extra = ""
        if tie.extra_time:
            extra = f", aet {tie.extra_time[0]}-{tie.extra_time[1]}"
        if tie.pens:
            extra += f", {tie.winner} win {tie.pens_won[0]}-{tie.pens_won[1]} on pens"
        return f"{m.home} {m.score} {m.away}{extra}  ->  {tie.winner}"
    if tie.method == "oneshot":
        return f"{tie.a} v {tie.b}: P(A) = {tie.p_advance:.3f}  ->  {tie.winner}"
    l1, l2 = tie.legs
    body = f"{tie.b} {l1.score} {tie.a}  |  {tie.a} {l2.score} {tie.b}"
    if tie.method == "aggregate":
        body += f"  (agg {tie.score_a}-{tie.score_b}"
    else:
        body += f"  (legs {tie.score_a:g}-{tie.score_b:g}"
    if tie.extra_time:
        body += f", aet {tie.extra_time[0]}-{tie.extra_time[1]}"
    if tie.pens:
        body += f", {tie.pens_won[0]}-{tie.pens_won[1]} on pens"
    return body + f")  ->  {tie.winner}"


def write_log(result, dest_dir=LOG_DIR, stamp=None):
    """data/processed/sim_<COMP>_<stamp>.txt with summary then trace."""
    stamp = stamp or datetime.now().strftime("%Y%m%d-%H%M%S")
    path = Path(dest_dir) / f"sim_{result.comp}_{stamp}.txt"
    lines = summary_lines(result)
    if result.trace:
        lines += ["", "=" * 70, "EXPERT TRACE", "=" * 70] + result.trace
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    import sys
    from model import draw_ucl, draw_uecl
    from model.matchdays_ucl import generate_matchdays

    comp = sys.argv[1] if len(sys.argv) > 1 else "UCL"
    if comp == "UECL":
        teams = draw_uecl.generate_draw(seed=1)
    else:
        teams = draw_ucl.generate_draw(comp=comp, seed=1)
    days = generate_matchdays(teams, seed=1)
    result = simulate(comp, teams, days, SimConfig(expert=True, seed=1))
    print("\n".join(summary_lines(result)))
    print(f"\ntrace: {len(result.trace)} lines, {result.elapsed * 1000:.0f} ms")
    mc = monte_carlo(comp, teams, days, SimConfig(seed=1), runs=100)
    print(f"\nMonte Carlo, {mc.runs} runs, {mc.elapsed:.2f} s")
    for club, pts, p in mc.rows()[:10]:
        print(f"  {club:26} pts {pts:5.1f}  top8 {p['top8']:.2f}  QF {p['qf']:.2f}  "
              f"final {p['final']:.2f}  win {p['winner']:.2f}")
