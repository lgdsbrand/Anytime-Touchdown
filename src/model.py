import pandas as pd
from src.player_data import get_players_for_matchups

def predict_week(matchups: dict, season: int) -> pd.DataFrame:
    """Return ATD predictions for all players in given matchups."""
    df = get_players_for_matchups(matchups, season=season)

    # Replace baseline with model logic later
    df["atd_prob"] = df["atd_prob"]  # ← placeholder

    return df

