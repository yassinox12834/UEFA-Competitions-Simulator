"""Fit a three-class (away/draw/home) result classifier.

Reads
    data/processed/match_features.csv   written by elo_score_updating.py

Writes
    data/processed/predictions.csv      the unplayed rows, with
                                        p_away / p_draw / p_home added
"""

from pathlib import Path
from typing import Annotated
from csv import DictReader
import numpy as np
import pandas as pd
import warnings as wns
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

BASE_DIR = Path(__file__).resolve().parents[1]
FEATURES_CSV = BASE_DIR / "data" / "processed" / "match_features.csv"
OUT_PREDICTIONS_CSV = BASE_DIR / "data" / "processed" / "predictions.csv"

# Variable globale pour stocker le modèle entraîné et les derniers scores Elo connus
GLOBAL_PIPELINE = None
LATEST_ELO_SCORES = {}


def build_X(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "elo_diff": df["elo_home_before"] - df["elo_away_before"],
        "is_home":  df["is_home"],
    })


def load_and_train_model():
    """Charge les données et entraîne le modèle global pour la fonction predict."""
    global GLOBAL_PIPELINE, LATEST_ELO_SCORES
    
    if not FEATURES_CSV.exists():
        return
        
    df = pd.read_csv(FEATURES_CSV)
    played = df["target"].notna()
    df_train = df[played].copy()
    
    if df_train.empty:
        return

    # Sauvegarde du dernier Elo connu pour chaque équipe.
    # match_features.csv n'a que les Elo "before" (pré-match) ; comme les
    # lignes sont déjà en ordre chronologique, la dernière apparition d'une
    # équipe donne son Elo "before" le plus récent, qu'on utilise comme
    # approximation du dernier Elo connu.
    for _, row in df.iterrows():
        LATEST_ELO_SCORES[row["home_team"]] = row["elo_home_before"]
        LATEST_ELO_SCORES[row["away_team"]] = row["elo_away_before"]

    # Entraînement du pipeline global
    X = build_X(df_train)
    y = df_train["target"].astype(int)
    
    GLOBAL_PIPELINE = Pipeline([
        ("scaler", StandardScaler()),
        ("lr", LogisticRegression(max_iter=1000)),
    ])
    GLOBAL_PIPELINE.fit(X, y)


def main():
    global GLOBAL_PIPELINE
    
    df = pd.read_csv(FEATURES_CSV)

    played = df["target"].notna()
    df_train_pool = df[played].copy()
    df_predict = df[~played].copy()

    X = build_X(df_train_pool)
    y = df_train_pool["target"].astype(int)

    seasons = sorted(df_train_pool["season"].unique())
    if len(seasons) < 2:
        raise ValueError(
            f"Only {len(seasons)} season(s) with results, cannot hold one out to test on."
        )
    last_season = seasons[-1]
    train_mask = df_train_pool["season"] < last_season
    test_mask = ~train_mask

    print(f"Training on seasons {seasons[:-1]}, testing on {last_season}")
    print(f"Train rows: {int(train_mask.sum())}, test rows: {int(test_mask.sum())}")

    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("lr", LogisticRegression(max_iter=1000)),
    ])
    pipe.fit(X[train_mask], y[train_mask])

    proba_test = pipe.predict_proba(X[test_mask])
    print("classes:", pipe.classes_)  # expect [-1  0  1] -> away, draw, home
    print("log loss:", log_loss(y[test_mask], proba_test))
    print("coefficients:", pipe.named_steps["lr"].coef_)

    if not df_predict.empty:
        X_pred = build_X(df_predict)
        df_predict[["p_away", "p_draw", "p_home"]] = pipe.predict_proba(X_pred)
        df_predict.to_csv(OUT_PREDICTIONS_CSV, index=False)
        print(f"\nWrote {len(df_predict)} predictions to {OUT_PREDICTIONS_CSV}")
    else:
        print("\nNo unplayed fixtures found to predict.")
        
    # On prépare le modèle global pour les appels futurs de predict()
    load_and_train_model()


def predict(
    teams: tuple[Annotated[str, "home_team"], Annotated[str, "away_team"]], 
    /, 
    *, 
    neutral_venue: bool
):
    """Simule le match et retourne le gagnant textuel ou 'Match Nul'.

    La bulle d'aide IDLE affichera les détails grâce à ce Docstring.
    """
    if GLOBAL_PIPELINE is None:
        load_and_train_model()
        if GLOBAL_PIPELINE is None:
            raise RuntimeError("Le modèle n'a pas pu être entraîné. Vérifiez match_features.csv.")

    home_team, away_team = teams
    
    # Récupération des scores Elo (valeur par défaut à 1500 si l'équipe est inconnue)
    if home_team not in set(LATEST_ELO_SCORES.keys()):
        print(f"WARNING : {home_team} is not in LATEST_ELO_SCORES")

    if away_team not in set(LATEST_ELO_SCORES.keys()):
        print(f"WARNING : {away_team} is not in LATEST_ELO_SCORES")
    elo_home = LATEST_ELO_SCORES.get(home_team, 1500.0)
    elo_away = LATEST_ELO_SCORES.get(away_team, 1500.0)
    
    # Si le terrain est neutre, "is_home" vaut 0 (pas d'avantage à domicile)
    is_home_val = 0 if neutral_venue else 1
    
    # Création du DataFrame avec exactement la même structure que build_X
    X_single = pd.DataFrame({
        "elo_diff": [elo_home - elo_away],
        "is_home":  [is_home_val],
    })
    
    # Calcul des probabilités : [p_away, p_draw, p_home] d'après l'ordre [-1, 0, 1]
    probabilities = GLOBAL_PIPELINE.predict_proba(X_single)[0]
    
    print(f"\n--- Probabilités : {home_team} vs {away_team} ---")
    print(f"Terrain neutre : {neutral_venue}")
    print(f"Victoire Extérieur ({away_team}) : {probabilities[0]:.2%}")
    print(f"Match Nul                      : {probabilities[1]:.2%}")
    print(f"Victoire Domicile  ({home_team}) : {probabilities[2]:.2%}")
    
    # Tirage au sort du résultat final basé sur les probabilités calculées
    outcomes = [away_team, "Match Nul", home_team]
    simulated_result = np.random.choice(outcomes, p=probabilities)
    
    print(f"Resultat de la simulation : {simulated_result}")
    
    return simulated_result


if __name__ == "__main__":
    # Train the model
    main()

    # Get all teams from the CSV
    with open(FEATURES_CSV, "r", newline="") as f:
        reading = DictReader(f)

        all_teams = set()
        for row in reading:
            all_teams.add(row["home_team"])
            all_teams.add(row["away_team"])

    all_teams = list(all_teams)

    # Choose 2 different random teams
    home_team, away_team = np.random.choice(all_teams, size=2, replace=False)

    # Randomly decide whether the match is at a neutral venue
    neutral_venue = bool(np.random.choice([True, False]))

    print(f"\nRandom match: {home_team} vs {away_team}")
    print(f"Neutral venue: {neutral_venue}")

    # Simulate the match
    predict(
        (home_team, away_team),
        neutral_venue=neutral_venue
    )

