"""Match outcome model: a three-class logistic regression on the Elo gap.

Two halves, deliberately separated:

    train()      needs scikit-learn and pandas. Reads match_features.csv,
                 fits StandardScaler + LogisticRegression, scores a
                 chronological holdout, and writes the fitted NUMBERS to
                 data/reference/predictor_weights.json.
    MatchModel   needs nothing but math. Reads that JSON and computes the
                 probabilities by hand: scale x, one z per class, softmax.

Why not call pipe.predict_proba() inside the simulation? Three reasons.
Speed: predict_proba costs about 0.5 ms of Python overhead per call, and
a Monte Carlo of 500 tournaments makes ~90 000 calls. Dependencies: the
app should run without scikit-learn installed, and requirements.txt has
been wrong about it for a month. Transparency: the expert log must show
the actual numbers, "z_home = 0.41 * 1.23 + 0.12", and the pipeline
hides them.

The maths, with every symbol:

    x    = R_home - R_away                    the Elo gap, one feature
    x'   = (x - mu) / sigma                   StandardScaler, mu and sigma
                                              measured on the training set
    z_k  = w_k * x' + b_k                     one score per class k in
                                              {away, draw, home}; w_k and
                                              b_k are what the fit learned
    p_k  = exp(z_k) / sum_j exp(z_j)          softmax, so the three p sum
                                              to 1

Home advantage is NOT a feature: is_home is 1 in every row except the
few finals played on neutral ground, so it carries almost no
information. It is in the model anyway, through the intercepts b_k: the target is "home wins",
"draw", "away wins", and the training rows have more home wins than away
wins at the same Elo gap, so b_home > b_away. A neutral-venue match
(the final) removes it by symmetry: predict A-vs-B with A at home, then
B-vs-A with B at home, and average the two.
"""

import json
import math
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
FEATURES_CSV = BASE_DIR / "data" / "processed" / "match_features.csv"
WEIGHTS_JSON = BASE_DIR / "data" / "reference" / "predictor_weights.json"

CLASSES = (-1, 0, 1)                 # away win, draw, home win
CLASS_NAMES = {-1: "away", 0: "draw", 1: "home"}


class PredictorError(Exception):
    """The model cannot be used. The message says what to run."""


# ---------------------------------------------------------------------------
# 1. Training (scikit-learn side)
# ---------------------------------------------------------------------------

TRAIN_FRACTION = 0.6      # oldest 60% of matches train, newest 40% test


def train(features_csv=FEATURES_CSV, out_json=WEIGHTS_JSON, verbose=True):
    """Fit the classifier and write its numbers to `out_json`.

    Holdout: the oldest 60% of matches (in date order) train, the newest
    40% are kept for scoring. Then the model is REFIT on all matches and
    that refit is what gets written, so the holdout score describes a
    slightly weaker model than the one shipped.
    """
    import numpy as np
    import pandas as pd
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import log_loss
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    df = pd.read_csv(features_csv)
    df = df[df["target"].notna()].copy()
    # The holdout is "the newest 40 %", so the rows must be in date order.
    # elo_score_updating.py writes them that way, but nothing checked it:
    # a re-sorted file would have silently scored the model on a random
    # 40 %. Files written before 1.1.0 have no timestamp column.
    if "timestamp" in df.columns:
        df = df.sort_values("timestamp", kind="stable")
    if df.empty:
        raise PredictorError(f"no played match in {features_csv}")

    X = (df["elo_home_before"] - df["elo_away_before"]).to_numpy().reshape(-1, 1)
    y = df["target"].astype(int).to_numpy()

    def make():
        return Pipeline([("scaler", StandardScaler()),
                         ("lr", LogisticRegression(max_iter=1000))])

    seasons = [int(s) for s in sorted(df["season"].unique())]
    report = {}
    if len(df) >= 100:
        cut = int(len(df) * TRAIN_FRACTION)
        train_mask = np.arange(len(df)) < cut

        pipe = make().fit(X[train_mask], y[train_mask])
        proba = pipe.predict_proba(X[~train_mask])

        # A "no-skill" baseline: always predict the training class
        # frequencies. If the model does not beat it, the Elo gap is
        # telling us nothing.
        freq = np.bincount(y[train_mask] + 1, minlength=3) / train_mask.sum()
        base = np.tile(freq, (int((~train_mask).sum()), 1))

        report = {
            "train_fraction": TRAIN_FRACTION,
            "train_rows": int(train_mask.sum()),
            "test_rows": int((~train_mask).sum()),
            "log_loss": float(log_loss(y[~train_mask], proba, labels=list(CLASSES))),
            "log_loss_no_skill": float(log_loss(y[~train_mask], base, labels=list(CLASSES))),
        }

    pipe = make().fit(X, y)
    scaler, lr = pipe.named_steps["scaler"], pipe.named_steps["lr"]
    if list(lr.classes_) != list(CLASSES):
        raise PredictorError(f"unexpected class order {lr.classes_}")

    weights = {
        "_comment": "Fitted by model/predictor.py. x = elo_home - elo_away; "
                    "x' = (x - mean) / scale; z_k = coef[k] * x' + intercept[k]; "
                    "p_k = softmax(z)_k. Classes in order: away, draw, home.",
        "trained_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "rows": int(len(df)),
        "seasons": seasons,
        "features": ["elo_diff"],
        "classes": list(CLASSES),
        "mean": float(scaler.mean_[0]),
        "scale": float(scaler.scale_[0]),
        "coef": [float(c[0]) for c in lr.coef_],
        "intercept": [float(b) for b in lr.intercept_],
        "holdout": report,
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(weights, indent=2), encoding="utf-8")

    if verbose:
        print(f"trained on {len(df)} rows, seasons {seasons}")
        if report:
            print(f"holdout (newest {1 - report['train_fraction']:.0%} of matches, "
                  f"{report['train_rows']} train / {report['test_rows']} test): "
                  f"log loss {report['log_loss']:.4f} "
                  f"(no-skill {report['log_loss_no_skill']:.4f})")
        print("mean %.3f  scale %.3f" % (weights["mean"], weights["scale"]))
        for k, w, b in zip(CLASSES, weights["coef"], weights["intercept"]):
            print(f"  {CLASS_NAMES[k]:5} w = {w:+.4f}   b = {b:+.4f}")
        print(f"wrote {out_json}")
    return weights


# ---------------------------------------------------------------------------
# 2. Prediction (pure Python side)
# ---------------------------------------------------------------------------

class Probs:
    """The three probabilities of one match, plus how they were computed.

    p_home / p_draw / p_away sum to 1. `trace` is a dict of the
    intermediate numbers (x, x', z per class) for the expert log; it is
    None unless the model was asked for it, because building a dict per
    match is the only cost worth skipping in a Monte Carlo loop.
    """

    __slots__ = ("p_home", "p_draw", "p_away", "trace")

    def __init__(self, p_home, p_draw, p_away, trace=None):
        self.p_home, self.p_draw, self.p_away = p_home, p_draw, p_away
        self.trace = trace

    def as_tuple(self):
        return (self.p_home, self.p_draw, self.p_away)

    def __repr__(self):
        return f"Probs(home={self.p_home:.3f}, draw={self.p_draw:.3f}, away={self.p_away:.3f})"


class MatchModel:
    """Computes P(home), P(draw), P(away) from two Elo ratings."""

    def __init__(self, weights):
        self.mean = float(weights["mean"])
        self.scale = float(weights["scale"]) or 1.0
        self.coef = [float(c) for c in weights["coef"]]
        self.intercept = [float(b) for b in weights["intercept"]]
        self.classes = tuple(weights.get("classes", CLASSES))
        self.meta = {k: weights.get(k) for k in ("trained_at", "rows", "seasons", "holdout")}
        if len(self.coef) != 3 or len(self.intercept) != 3:
            raise PredictorError("weights must hold exactly three classes")

    @classmethod
    def load(cls, path=WEIGHTS_JSON):
        path = Path(path)
        if not path.is_file():
            raise PredictorError(
                f"{path.name} not found. Train the model first:\n"
                f"    python -m model.predictor --train")
        return cls(json.loads(path.read_text(encoding="utf-8")))

    # ---------- the maths ----------
    def scores(self, elo_home, elo_away):
        """(x, x', [z_away, z_draw, z_home])."""
        x = elo_home - elo_away
        xs = (x - self.mean) / self.scale
        z = [w * xs + b for w, b in zip(self.coef, self.intercept)]
        return x, xs, z

    def probabilities(self, elo_home, elo_away, neutral=False, trace=False):
        """P(home), P(draw), P(away) for one match.

        neutral=True averages the match with its mirror image (B hosting
        A), which cancels the home-advantage term hidden in the
        intercepts. Used for the final.
        """
        if neutral:
            a = self.probabilities(elo_home, elo_away, trace=trace)
            b = self.probabilities(elo_away, elo_home, trace=trace)
            probs = Probs((a.p_home + b.p_away) / 2, (a.p_draw + b.p_draw) / 2,
                          (a.p_away + b.p_home) / 2)
            if trace:
                probs.trace = {"neutral": True, "as_home": a.trace, "mirrored": b.trace}
            return probs

        x, xs, z = self.scores(elo_home, elo_away)
        # Subtract the max before exp: with |z| beyond ~700, exp overflows
        # a float, and the softmax is unchanged by a constant shift.
        top = max(z)
        e = [math.exp(v - top) for v in z]
        total = sum(e)
        p_away, p_draw, p_home = (v / total for v in e)
        probs = Probs(p_home, p_draw, p_away)
        if trace:
            probs.trace = {
                "neutral": False,
                "elo_home": elo_home, "elo_away": elo_away,
                "x": x, "mean": self.mean, "scale": self.scale, "x_scaled": xs,
                "z": {"away": z[0], "draw": z[1], "home": z[2]},
                "coef": {"away": self.coef[0], "draw": self.coef[1], "home": self.coef[2]},
                "intercept": {"away": self.intercept[0], "draw": self.intercept[1],
                              "home": self.intercept[2]},
            }
        return probs


def format_trace(t, digits=3):
    """The trace of probabilities(trace=True) as lines of text for a log."""
    if t is None:
        return []
    if t.get("neutral"):
        lines = ["neutral venue: average of the two orientations"]
        lines += ["  A at home: " + line for line in format_trace(t["as_home"], digits)]
        lines += ["  B at home: " + line for line in format_trace(t["mirrored"], digits)]
        return lines
    f = f"{{:.{digits}f}}"
    lines = [
        f"x = R_home - R_away = {f.format(t['elo_home'])} - {f.format(t['elo_away'])} = {f.format(t['x'])}",
        f"x' = (x - {f.format(t['mean'])}) / {f.format(t['scale'])} = {f.format(t['x_scaled'])}",
    ]
    for k in ("home", "draw", "away"):
        lines.append(f"z_{k} = {t['coef'][k]:+.4f} * x' {t['intercept'][k]:+.4f} = {f.format(t['z'][k])}")
    return lines


if __name__ == "__main__":
    if "--train" in sys.argv:
        train()
    else:
        model = MatchModel.load()
        for gap in (-300, -100, 0, 100, 300):
            p = model.probabilities(1600 + gap, 1600)
            print(f"gap {gap:+5}: home {p.p_home:.3f}  draw {p.p_draw:.3f}  away {p.p_away:.3f}")
        print("neutral, gap 0:", model.probabilities(1600, 1600, neutral=True))
