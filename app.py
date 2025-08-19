import streamlit as st
from utils import get_matchups_for_week, get_baseline_probs, get_player_list

# 📅 Define season parameters
season = st.sidebar.selectbox("Season", options=[2023, 2024, 2025])
week = st.sidebar.selectbox("Week", options=list(range(1, 19)))
season_type = st.sidebar.selectbox("Season Type", options=["regular", "postseason"])

# 🏈 Fetch matchups once and reuse
matchups = get_matchups_for_week(season=season, week=week, season_type=season_type)

# 🔍 Matchup selector
selected_gid = st.sidebar.selectbox(
    "Jump to matchup",
    options=["All Games"] + list(matchups.keys()),
    format_func=lambda gid: "All Games" if gid == "All Games" else matchups[gid]["label"]
)

# 📊 Display matchups
st.title("🏈 Anytime Touchdown Dashboard")
st.subheader(f"Week {week} • {season_type.title()} Season")

if selected_gid == "All Games":
    for gid, matchup in matchups.items():
        st.markdown(f"### {matchup['label']}")
        # Add your display logic here (e.g., player list, baseline probs)
        players = get_player_list(gid)
        probs = get_baseline_probs(gid)
        # Display logic...
else:
    matchup = matchups[selected_gid]
    st.markdown(f"### {matchup['label']}")
    players = get_player_list(selected_gid)
    probs = get_baseline_probs(selected_gid)
    # Display logic...

# 🧠 Placeholder for model predictions
# You can wire in your model outputs here once ready
