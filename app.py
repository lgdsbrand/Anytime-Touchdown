import streamlit as st
import pandas as pd
from src.data_loader import get_matchups_for_week
from src.player_data import get_players_for_matchups

st.set_page_config(page_title="NFL Anytime TD Dashboard", layout="wide")

# ---- Sidebar controls ----
default_season, default_week, default_type = 2025, 1, "reg"

season = st.sidebar.number_input("Season", min_value=2018, max_value=2100, value=default_season, step=1)
week = st.sidebar.number_input("Week", min_value=1, max_value=22, value=default_week, step=1)
season_type = st.sidebar.selectbox("Season Type", options=["reg", "post", "pre"], index=["reg", "post", "pre"].index(default_type))
pos_filter = st.sidebar.selectbox("Position filter", options=["All", "RB", "WR", "TE", "QB"])

# ---- Load matchups ----
matchups = get_matchups_for_week(season=season, week=week, season_type="reg")

if not matchups:
    st.warning("No games found for that week/season.")
    st.stop()

# ---- Jump to matchup dropdown ----
selected_gid = st.sidebar.selectbox(
    "🔍 Jump to matchup",
    options=["All Games"] + list(matchups.keys()),
    format_func=lambda gid: "All Games" if gid == "All Games" else matchups[gid]["label"]
)

# ---- Load player data ----
players_df = get_players_for_matchups(matchups, season=season)

if pos_filter != "All":
    players_df = players_df[players_df["position"] == pos_filter]

# ---- Page header ----
st.title("🏈 Anytime Touchdown Dashboard")
st.caption(f"Week {week} • {season_type.title()} Season • {season}")

# ---- Render matchups ----
for gid, info in matchups.items():
    if selected_gid != "All Games" and gid != selected_gid:
        continue

    st.markdown("---")
    st.subheader(f"{info['away']} at {info['home']}")
    st.caption(f"Kickoff: {info['kickoff_et']} • Network: {info['network']}")

    game_df = players_df[players_df["game_id"] == gid].copy()
    if game_df.empty:
        st.info("No players available for this matchup.")
        continue

    game_df["Projected ATD"] = (game_df["atd_prob"] * 100).round(1)
    game_df.rename(columns={
        "player_name": "Player",
        "team": "Team",
        "position": "Position",
        "opponent": "Opponent",
        "logo": "Logo"
    }, inplace=True)

    show_cols = ["Logo", "Player", "Team", "Position", "Opponent", "Projected ATD"]
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
st.info("Next step: plug in model predictions to replace baseline ATD and add sportsbook odds + edge.")
