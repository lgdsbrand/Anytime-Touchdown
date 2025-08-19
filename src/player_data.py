# src/player_data.py
from __future__ import annotations

import math
from functools import lru_cache
from typing import Dict, Iterable, List

import numpy as np
import pandas as pd

try:
    import nfl_data_py as nfl
except Exception as e:
    raise ImportError(
        "nfl_data_py is required. Add it to requirements.txt and redeploy.\n"
        "pip install nfl_data_py pyarrow"
    )


# Simple logo mapping via ESPN CDN (works with lowercase team abbrs)
def team_logo_url(team_abbr: str) -> str:
    if not isinstance(team_abbr, str) or not team_abbr:
        return ""
    return f"https://a.espncdn.com/i/teamlogos/nfl/500/{team_abbr.lower()}.png"


SKILL_POS = {"RB", "WR", "TE", "QB"}


@lru_cache(maxsize=2)
def load_rosters_for_season(season: int) -> pd.DataFrame:
    df = nfl.import_rosters([season])
    # Normalize common fields
    rename = {
        "team": "team",
        "position": "position",
        "full_name": "player_name",
        "gsis_id": "player_id",
        "status": "status",
        "depth_chart_position": "depth_chart_position",
        "depth_chart_order": "depth_chart_order",
    }
    for k in list(rename.keys()):
        if k not in df.columns:
            rename.pop(k, None)
    df = df.rename(columns=rename)
    # Filter to active-ish and skill positions if possible
    if "status" in df.columns:
        df = df[df["status"].astype(str).str.upper().isin(["ACT", "ACTIVE", "INJURED_RESERVE", "RES"]) | df["status"].isna()]
    if "position" in df.columns:
        df = df[df["position"].isin(SKILL_POS)]
    return df


@lru_cache(maxsize=4)
def load_weekly_prev(season_prev: int) -> pd.DataFrame:
    # Last season weekly stats to create a baseline ATD probability
    wk = nfl.import_weekly_data([season_prev], downcast=True)
    # Keep core fields
    keep_cols = [
        "player_id",
        "player_name",
        "recent_team",
        "position",
        "season",
        "week",
        "game_id",
        "rushing_tds",
        "receiving_tds",
        "kick_return_tds",
        "punt_return_tds",
        "fumble_return_tds",
        "int_return_tds",
    ]
    wk = wk[[c for c in keep_cols if c in wk.columns]].copy()
    # Total non-passing TDs
    td_cols = [c for c in keep_cols if c.endswith("_tds") and c != "passing_tds"]
    wk["nonpass_tds"] = wk[td_cols].sum(axis=1)
    return wk


def baseline_atd_from_prev(wk_prev: pd.DataFrame) -> pd.DataFrame:
    # Aggregate per player: games played and total non-passing TDs
    agg = (
        wk_prev.groupby(["player_id", "player_name", "recent_team", "position"], dropna=False)
        .agg(
            games=("game_id", "nunique"),
            tds=("nonpass_tds", "sum"),
        )
        .reset_index()
    )
    agg["games"] = agg["games"].replace(0, np.nan)
    agg["rate_per_game"] = (agg["tds"] / agg["games"]).fillna(0.0)

    # Poisson conversion: p(score >=1) = 1 - exp(-lambda) with lambda = rate_per_game
    agg["atd_prob"] = 1 - np.exp(-agg["rate_per_game"].clip(lower=0, upper=2.0))

    # Keep skill positions only
    agg = agg[agg["position"].isin(SKILL_POS)].copy()
    # Clean team col
    agg.rename(columns={"recent_team": "team"}, inplace=True)
    return agg[["player_id", "player_name", "team", "position", "atd_prob"]]


def select_team_players(agg_prev: pd.DataFrame, team: str, k_skill: int = 8, include_qb: bool = True) -> pd.DataFrame:
    tdf = agg_prev[agg_prev["team"] == team].copy()
    # Separate QBs so we can ensure at least one QB appears
    qb = tdf[tdf["position"] == "QB"].sort_values("atd_prob", ascending=False).head(1) if include_qb else tdf.iloc[0:0]
    skill = tdf[tdf["position"].isin({"RB", "WR", "TE"})].sort_values("atd_prob", ascending=False).head(k_skill)
    out = pd.concat([qb, skill], ignore_index=True)
    out["team"] = team
    return out


def get_players_for_matchups(matchups: Dict[str, Dict], season: int) -> pd.DataFrame:
    # Use previous season stats as a baseline for Week 1; as season progresses you can blend current-season form
    season_prev = season - 1
    wk_prev = load_weekly_prev(season_prev)
    base = baseline_atd_from_prev(wk_prev)

    # Roster used only for potential enrichment (not strictly required here)
    # roster = load_rosters_for_season(season)

    rows = []
    for gid, info in matchups.items():
        home = info["home"]
        away = info["away"]

        home_players = select_team_players(base, home, k_skill=8, include_qb=True)
        away_players = select_team_players(base, away, k_skill=8, include_qb=True)

        home_players = home_players.assign(opponent=away, game_id=gid)
        away_players = away_players.assign(opponent=home, game_id=gid)

        rows.append(home_players)
        rows.append(away_players)

    df = pd.concat(rows, ignore_index=True)

    # Attach logos
    df["logo"] = df["team"].apply(team_logo_url)

    # Final ordering
    df = df[["game_id", "player_name", "team", "position", "opponent", "atd_prob", "logo"]]
    return df

