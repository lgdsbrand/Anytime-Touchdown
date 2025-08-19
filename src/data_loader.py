# src/data_loader.py
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, asdict
from functools import lru_cache
from typing import Dict, List, Optional, Tuple
from collections import OrderedDict

import pandas as pd


NFLVERSE_SCHEDULE_URLS = [
    # Primary raw URL
    "https://raw.githubusercontent.com/nflverse/nflfastR-data/master/schedules/sched_{season}.csv",
    # Fallback raw URL
    "https://github.com/nflverse/nflfastR-data/blob/master/schedules/sched_{season}.csv?raw=1",
]


@dataclass(frozen=True)
class Game:
    game_id: str
    season: int
    week: int
    home_team: str
    away_team: str
    kickoff_utc: dt.datetime  # timezone-aware in UTC

    @property
    def label(self) -> str:
        # Streamlit-friendly label, e.g., "BUF at KC — Sun 4:25 PM ET"
        local = self.kickoff_utc.astimezone(dt.timezone(dt.timedelta(hours=-4)))  # ET with DST approximation
        dow = local.strftime("%a")
        tstr = local.strftime("%-I:%M %p ET") if hasattr(local, "strftime") else local.strftime("%I:%M %p ET")
        return f"{self.away_team} at {self.home_team} — {dow} {tstr}"


def _approx_et_tz() -> dt.tzinfo:
    # Simple EDT/EST approximation without external deps
    # Use UTC-4 between Mar–Oct, else UTC-5. Good enough for display.
    month = dt.datetime.utcnow().month
    offset = -4 if 3 <= month <= 10 else -5
    return dt.timezone(dt.timedelta(hours=offset))


def _to_utc(ts: pd.Timestamp) -> dt.datetime:
    if ts.tzinfo is None:
        return ts.tz_localize("UTC").to_pydatetime()
    return ts.tz_convert("UTC").to_pydatetime()


@lru_cache(maxsize=6)
def fetch_schedule(season: int) -> pd.DataFrame:
    last_err = None
    for url_tmpl in NFLVERSE_SCHEDULE_URLS:
        url = url_tmpl.format(season=season)
        try:
            df = pd.read_csv(url)
            # Normalize column names used downstream
            cols = {c.lower(): c for c in df.columns}
            df.columns = [c.lower() for c in df.columns]

            # Pick kickoff column
            kickoff_col = None
            for cand in ["kickoff_in_utc", "start_time_utc", "game_time_utc"]:
                if cand in df.columns:
                    kickoff_col = cand
                    break

            if kickoff_col is None:
                # Fallback: combine game_date + gametime if available
                if "game_date" in df.columns and "gametime" in df.columns:
                    df["kickoff_dt"] = pd.to_datetime(df["game_date"] + " " + df["gametime"], errors="coerce", utc=True)
                else:
                    df["kickoff_dt"] = pd.NaT
            else:
                df["kickoff_dt"] = pd.to_datetime(df[kickoff_col], utc=True, errors="coerce")

            # Standardize types
            if "week" in df.columns:
                df["week"] = pd.to_numeric(df["week"], errors="coerce").astype("Int64")
            if "season" in df.columns:
                df["season"] = pd.to_numeric(df["season"], errors="coerce").astype("Int64")
            if "game_type" in df.columns:
                df["game_type"] = df["game_type"].astype(str)

            # Prefer nflverse_game_id then game_id
            if "nflverse_game_id" in df.columns:
                df["gid"] = df["nflverse_game_id"].astype(str)
            elif "game_id" in df.columns:
                df["gid"] = df["game_id"].astype(str)
            else:
                df["gid"] = (df["season"].astype(str) + "_" + df["week"].astype(str) + "_" + df["home_team"].astype(str))

            return df
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"Could not fetch schedule for season {season}: {last_err}")


def infer_display_season(today: Optional[dt.date] = None) -> int:
    # NFL regular season spans Sep–Jan. If it's Feb–Jul, show last season by default; Aug–Jan show current year.
    today = today or dt.date.today()
    if 2 <= today.month <= 7:
        return today.year - 1
    return today.year


def infer_display_week(df: pd.DataFrame, today: Optional[dt.datetime] = None) -> int:
    # Pick the next upcoming REG week; if none, last completed REG week.
    today = today or dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)
    reg = df[(df.get("game_type", "REG") == "REG") & df["kickoff_dt"].notna()].copy()
    if reg.empty:
        # Fallback: most common week
        return int(df["week"].dropna().astype(int).mode().iloc[0])
    upcoming = reg[reg["kickoff_dt"] >= today].sort_values("kickoff_dt")
    if not upcoming.empty:
        return int(upcoming["week"].iloc[0])
    return int(reg["week"].max())


def get_games(season: Optional[int] = None, week: Optional[int] = None) -> List[Game]:
    season = season or infer_display_season()
    df = fetch_schedule(season)
    if week is None:
        week = infer_display_week(df)

    mask = (df.get("game_type", "REG") == "REG") & (df["week"] == week)
    sub = df.loc[mask, ["gid", "season", "week", "home_team", "away_team", "kickoff_dt"]].dropna(subset=["home_team", "away_team"])

    games: List[Game] = []
    for _, r in sub.iterrows():
        if pd.isna(r["kickoff_dt"]):
            continue
        games.append(
            Game(
                game_id=str(r["gid"]),
                season=int(r["season"]),
                week=int(r["week"]),
                home_team=str(r["home_team"]),
                away_team=str(r["away_team"]),
                kickoff_utc=_to_utc(pd.to_datetime(r["kickoff_dt"], utc=True)),
            )
        )
    # Sort by kickoff
    games.sort(key=lambda g: g.kickoff_utc)
    return games


def get_matchups_for_week(season: Optional[int] = None, week: Optional[int] = None) -> "OrderedDict[str, Dict]":
    games = get_games(season=season, week=week)
    et = _approx_et_tz()
    out: "OrderedDict[str, Dict]" = OrderedDict()
    for g in games:
        local = g.kickoff_utc.astimezone(et)
        out[g.game_id] = {
            "label": g.label,
            "home": g.home_team,
            "away": g.away_team,
            "kickoff_utc": g.kickoff_utc.isoformat(),
            "kickoff_local": local.isoformat(),
            "season": g.season,
            "week": g.week,
            "game_id": g.game_id,
        }
    return out


def get_default_season_week() -> Tuple[int, int]:
    season = infer_display_season()
    week = infer_display_week(fetch_schedule(season))
    return season, week

