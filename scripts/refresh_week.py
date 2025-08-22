import pandas as pd
from src.data_loader import get_matchups_for_week
from src.player_data import get_players_for_matchups
from src.model import predict_week  # You’ll wire this in soon
import datetime as dt
import os

def get_current_week():
    today = dt.date.today()
    season = today.year if today.month >= 8 else today.year - 1
    season_type = "reg"

    # Estimate week number (you can wire this to a real tracker later)
    week = 1
    return season, week, season_type

def refresh_and_cache():
    season, week, season_type = get_current_week()
    print(f"[✓] Refreshing Week {week}, {season_type} {season}")

    # Get matchups
    matchups = get_matchups_for_week(season=season, week=week, season_type=season_type)
    if not matchups:
        print("[!] No matchups found — aborting.")
        return

    # Save matchups to CSV
    matchups_df = pd.DataFrame(matchups.values())
    os.makedirs("data", exist_ok=True)
    matchups_path = f"data/week{week}_{season_type}_{season}_matchups.csv"
    matchups_df.to_csv(matchups_path, index=False)
    print(f"[✓] Saved matchups to {matchups_path}")

    # Get player list and predictions
    players_df = get_players_for_matchups(matchups, season=season)
    predictions_df = predict_week(matchups, season=season)  # Replace baseline later

    # Save predictions to CSV
    predictions_path = f"data/week{week}_{season_type}_{season}_predictions.csv"
    predictions_df.to_csv(predictions_path, index=False)
    print(f"[✓] Saved predictions to {predictions_path}")

if __name__ == "__main__":
    refresh_and_cache()
