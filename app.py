# app.py
import math
import numpy as np
import pandas as pd
import streamlit as st

from src.data_loader import get_matchups_for_week, get_default_season_week
from src.player_data import get_players_for_matchups  # you'll add this file below

st.set_page_config(page_title="NFL Anytime TD Dashboard", layout="wide")

# -------------- Sidebar controls --------------
default_season, default_week, default_type = 2025, 1, "reg"
with st.sidebar:
    st.title("Anytime TD")
    season = st.number_input("Season", min_value=2018, max_value=2100, value=default_season, step=1)
    week = st.number_input("Week (REG)", min_value=1, max_value=18, value=default_week, step=1)
    pos_filter = st.selectbox("Position filter", options=["All", "RB", "WR", "TE", "QB"])
    selected_gid = st.selectbox(
        "Jump to matchup",
        options=["All Games"] + list(get_matchups_for_week(season=season, week=week).keys()),
        format_func=lambda gid: "All Games" if gid == "All Games" else get_matchups_for_week(season=season, week=week)[gid]["label"],
    )

# -------------- Load slate + players --------------
matchups = get_matchups_for_week(season=season, week=week)
if not matchups:
    st.warning("No regular-season games found for that week/season.")
    st.stop()

# Get real players with a baseline ATD estimate per game
players_df = get_players_for_matchups(matchups, season=season)

# Optional: apply global position filter
if pos_filter != "All":
    players_df = players_df[players_df["position"] == pos_filter]

# -------------- Render --------------
st.header(f"Week {week} • {season} — Anytime TD Projections (baseline)")
st.caption("Projections currently use last season's non-passing TD rate per game as a baseline. Model integration coming next.")

for gid, info in matchups.items():
    if selected_gid != "All Games" and gid != selected_gid:
        continue

    st.markdown("---")
    st.subheader(f"{info['away']} at {info['home']}")
    st.caption(f"Kickoff: {info['label'].split('—')[-1].strip()} • Game ID: {gid}")

    game_df = players_df[players_df["game_id"] == gid].copy()
    if game_df.empty:
        st.info("No players available yet for this matchup.")
        continue

    # Display percentages nicely
    game_df["Projected ATD"] = (game_df["atd_prob"] * 100).round(1)
    game_df.rename(
        columns={
            "player_name": "Player",
            "team": "Team",
            "opponent": "Opponent",
            "position": "Position",
            "logo": "Logo",
        },
        inplace=True,
    )

    show_cols = ["Logo", "Player", "Team", "Position", "Opponent", "Projected ATD"]
    # Keep placeholders for your future columns if you want
    # game_df["Book Odds"] = np.nan
    # game_df["Edge"] = np.nan
    # show_cols += ["Book Odds", "Edge"]

    # Sort by baseline ATD desc
    game_df = game_df.sort_values("Projected ATD", ascending=False)

    st.dataframe(
        game_df[show_cols],
        use_container_width=True,
        column_config={
            "Logo": st.column_config.ImageColumn("Team", width=40),
            "Projected ATD": st.column_config.NumberColumn("Projected ATD", help="Baseline estimate from prior-season TD rate", format="%.1f%%"),
        },
        hide_index=True,
    )

    csv_bytes = game_df[["Player", "Team", "Position", "Opponent", "Projected ATD"]].to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download matchup CSV",
        data=csv_bytes,
        file_name=f"week{week}_{info['away']}_at_{info['home']}.csv",
        mime="text/csv",
    )

st.markdown("---")
st.info("Next steps: plug in the trained model to replace the baseline ATD, and later add sportsbook odds + edge.")
