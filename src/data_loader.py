import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime as dt
from collections import OrderedDict

SEASON_TYPE_MAP = {
    "pre": 1,
    "reg": 2,
    "post": 3
}

def fetch_espn_schedule(season=2025, week=1, season_type="reg"):
    stype_code = SEASON_TYPE_MAP[season_type]
    url = f"https://www.espn.com/nfl/schedule/_/week/{week}/year/{season}/seasontype/{stype_code}"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    games = []
    tables = soup.find_all("table")

    for table in tables:
        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) >= 3:
                matchup = cols[0].get_text(strip=True)
                time_str = cols[1].get_text(strip=True)
                network = cols[2].get_text(strip=True)

                if " at " not in matchup:
                    continue

                away, home = matchup.split(" at ")
                game_id = f"{season}_W{week}_T{stype_code}_{home}_{away}"

                games.append({
                    "game_id": game_id,
                    "season": season,
                    "week": week,
                    "season_type": season_type,
                    "home": home,
                    "away": away,
                    "kickoff_et": time_str,
                    "network": network
                })

    df = pd.DataFrame(games).drop_duplicates(subset=["game_id"])
    return df

def get_matchups_for_week(season=2025, week=1, season_type="reg") -> "OrderedDict[str, dict]":
    df = fetch_espn_schedule(season=season, week=week, season_type=season_type)
    out = OrderedDict()
    for _, row in df.iterrows():
        label = f"{row['away']} at {row['home']} — {row['kickoff_et']} ET"
        out[row["game_id"]] = {
            "label": label,
            "home": row["home"],
            "away": row["away"],
            "kickoff_et": row["kickoff_et"],
            "network": row["network"],
            "season": row["season"],
            "week": row["week"],
            "season_type": row["season_type"],
            "game_id": row["game_id"]
        }
    return out

def get_default_season_week() -> tuple[int, int, str]:
    today = dt.date.today()
    season = 2025
    week = 1
    season_type = "reg"  # Default to regular season
    return season, week, season_type

import os

def load_cached_matchups(season: int, week: int, season_type: str = "reg") -> "OrderedDict[str, dict]":
    path = f"data/week{week}_{season_type}_{season}_matchups.csv"
    if not os.path.exists(path):
        print(f"[!] Cached matchups not found: {path}")
        return {}

    df = pd.read_csv(path)
    out = OrderedDict()
    for _, row in df.iterrows():
        out[row["game_id"]] = {
            "label": row["label"],
            "home": row["home"],
            "away": row["away"],
            "kickoff_et": row["kickoff_et"],
            "network": row["network"],
            "season": row["season"],
            "week": row["week"],
            "season_type": row["season_type"],
            "game_id": row["game_id"]
        }
    return out
