"""Fit the Poisson goal model: goals scored ~ Elo gap.

Reads   data/processed/match_features.csv   Elo before each match, is_home
        data/processed/fixtures_25.csv      the 90-minute goals
Writes  data/reference/goal_weights.json    mu_home, mu_away, gamma

One row per team per match, so every match gives two rows:

    log(lambda) = b0 + gamma * s + h * is_home

    s        signed Elo gap in units of 400: +d for the home row, -d for the away row
    is_home  1 for a home row at a real home ground, 0 otherwise
    lambda   expected goals of that team

Afterwards:  mu_away = exp(b0),  mu_home = exp(b0 + h).

Run:  python -m model.fit_goals
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import PoissonRegressor

BASE_DIR = Path(__file__).resolve().parents[1]
FEATURES_CSV = BASE_DIR / "data" / "processed" / "match_features.csv"
FIXTURES_CSV = BASE_DIR / "data" / "processed" / "fixtures_25.csv"
WEIGHTS_JSON = BASE_DIR / "data" / "reference" / "goal_weights.json"

KEY = ["timestamp", "home_team", "away_team"]   # identifies one match in both files
ELO_SCALE = 400.0                               # same scale as the Elo formula


def load_joined():
    """One row per played match: Elo before, is_home, ft_home, ft_away, d."""
    features = pd.read_csv(FEATURES_CSV)
    fixtures = pd.read_csv(FIXTURES_CSV)
    goals = fixtures[KEY + ["ft_home", "ft_away"]]
    df = features.merge(goals, on=KEY, how="inner", validate="one_to_one")
    df = df.dropna(subset=["ft_home", "ft_away"]).reset_index(drop=True)
    df["d"] = (df["elo_home_before"] - df["elo_away_before"]) / ELO_SCALE
    return df


def stack(df):
    """Two rows per match, home rows first, then away rows."""
    signed_gap = np.concatenate([df["d"], -df["d"]])
    is_home = np.concatenate([df["is_home"], np.zeros(len(df))])
    goals = np.concatenate([df["ft_home"], df["ft_away"]])
    X = np.column_stack([signed_gap, is_home])
    return X, goals


def fit(df=None):
    """Fit and return {"mu_home", "mu_away", "gamma", "matches"}."""
    df = load_joined() if df is None else df
    X, y = stack(df)
    model = PoissonRegressor(alpha=0.0, max_iter=1000).fit(X, y)
    gamma, h = model.coef_
    return {
        "mu_home": float(np.exp(model.intercept_ + h)),
        "mu_away": float(np.exp(model.intercept_)),
        "gamma": float(gamma),
        "matches": int(len(df)),
    }


def save_weights(weights, path=WEIGHTS_JSON):
    payload = {"_comment": "Poisson goal model, written by model/fit_goals.py from "
                           "match_features.csv and fixtures_25.csv. "
                           "Rebuild with: python -m model.fit_goals",
               **weights}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


if __name__ == "__main__":
    weights = fit()
    out = save_weights(weights)
    print(f"gamma    = {weights['gamma']:.4f}")
    print(f"mu_home  = {weights['mu_home']:.4f}")
    print(f"mu_away  = {weights['mu_away']:.4f}")
    print(f"matches  = {weights['matches']}")
    print(f"wrote {out}")