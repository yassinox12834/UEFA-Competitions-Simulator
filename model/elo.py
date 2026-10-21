import math


formula1 = lambda z : 1 / (1 + math.e ** -z)

def update_elo(rating_old, rating_opponent, actual, k, home=True):
    """
    Update a team's Elo rating after a match.
    
    Args:
        rating_old: Team's rating before the match
        rating_opponent: Opponent's rating before the match
        actual: Match result from this team's perspective (1.0=win, 0.5=draw, 0.0=loss)
        k: K factor (from coefs dict)
        home: True if this team is home, False if away
    
    Returns:
        rating_new: Updated rating
    """
    
    # Calculate Elo difference
    if home:
        elo_diff = rating_old - rating_opponent
    else:
        elo_diff = rating_old - rating_opponent
    
    # Calculate expected win probability via sigmoid
    expected = 1.0 / (1.0 + 10 ** (-elo_diff / 400))
    
    # Update rating
    rating_new = rating_old + k * (actual - expected)
    
    return rating_new



print(formula1(1.2))