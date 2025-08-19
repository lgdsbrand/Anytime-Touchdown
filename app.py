# app.py
import streamlit as st
import pandas as pd
from src.data_loader import get_matchups_for_week, get_default_season_week

# ---- Page Config ----
st.set_page_config(page_title="NFL Anytime TD Dashboard", layout="wide")

# ---- Sidebar Controls ----
default_season, default_week = get_default_season_week()
season = st.sidebar.number_input("Season", min_value=2018, max_value=2100,
                                  value=default_season, step=1)
week = st.sidebar.number_input("Week (REG)", min_value=1, max_value=18,
                                value=default_week, step=1)

# Pull live schedule for selected week
matchups = get_matchups_for_week(season=season, week=week)

if not matchups:
    st.warning("No regular-season games found for that week/season.")
    st.stop()

# Dropdown for quick jump (keeps all games displayed below)
game_labels = {gid: info["label"] for gid, info in matchups.items()}
selected_gid = st.sidebar.selectbox(
    "🔍 Jump to a matchup",
    options=["All Games"] + list(game_labels.keys()),
    format_func=lambda x: "All Games" if x == "All Games" else game_labels[x]
)

# ---- Placeholder: This would eventually be replaced with your model output ----
# For now, generate fake predictions to show the layout
def mock_predictions_for_game(game_info):
    players = [
        {"Player": "Player A", "Team": game_info["home"], "Position": "RB", "Opponent": game_info["away"], "Projected ATD": 0.45, "Book Odds": 2.10},
        {"Player": "Player B", "Team": game_info["away"], "Position": "WR", "Opponent": game_info["home"], "Projected ATD": 0.35, "Book Odds": 2.80}
    ]
    df = pd.DataFrame(players)
    df["Edge"] = df["Projected ATD"] - (1 / df["Book Odds"])
    # Format probabilities nicely
    df["Projected ATD"] = (df["Projected ATD"] * 100).round(1).astype(str) + "%"
    df["Edge"] = (df["Edge"] * 100).round(1).astype(str) + "%"
    return df[["Player", "Team", "Position", "Opponent", "Projected ATD", "Book Odds", "Edge"]]

# ---- Main Page ----
for gid, info in matchups.items():
    if selected_gid != "All Games" and gid != selected_gid:
        continue

    st.markdown(f"---\n### 🏈 {info['away']} at {info['home']}")
    st.caption(f"Kickoff: {info['label'].split('—')[-1].strip()} | Week {info['week']} • {info['season']}")

    # Replace this with real model outputs once ready
    predictions_df = mock_predictions_for_game(info)

    st.dataframe(predictions_df, use_container_width=True)

st.markdown("---")
st.info("⚡ Once the ATD model is wired in, these tables will update automatically each Tuesday & Saturday with live data.")
