import streamlit as st
import pandas as pd

# Dummy data for illustration
matchups = {
    "Chiefs vs Ravens": [
        {"Player": "Travis Kelce", "Team": "Chiefs", "Logo": "https://a.espncdn.com/i/teamlogos/nfl/500/kc.png",
         "Position": "TE", "Opponent": "Ravens", "Projected ATD": 0.45, "Book Odds": 2.10},
        {"Player": "Lamar Jackson", "Team": "Ravens", "Logo": "https://a.espncdn.com/i/teamlogos/nfl/500/bal.png",
         "Position": "QB", "Opponent": "Chiefs", "Projected ATD": 0.38, "Book Odds": 2.50}
    ],
    "Bills vs Jets": [
        {"Player": "Stefon Diggs", "Team": "Bills", "Logo": "https://a.espncdn.com/i/teamlogos/nfl/500/buf.png",
         "Position": "WR", "Opponent": "Jets", "Projected ATD": 0.42, "Book Odds": 2.20},
        {"Player": "Breece Hall", "Team": "Jets", "Logo": "https://a.espncdn.com/i/teamlogos/nfl/500/nyj.png",
         "Position": "RB", "Opponent": "Bills", "Projected ATD": 0.36, "Book Odds": 2.80}
    ]
}

# Dropdown navigation
selected_game = st.selectbox("🔍 Jump to a matchup", options=list(matchups.keys()))

# Scroll to selected matchup (simulated with headers)
for game, players in matchups.items():
    st.markdown(f"---\n## 🏈 {game}")
    df = pd.DataFrame(players)
    df["Edge"] = df["Projected ATD"] - (1 / df["Book Odds"])
    df["Team Logo"] = df["Logo"].apply(lambda url: f"![]({url})")
    df_display = df[["Player", "Team Logo", "Position", "Opponent", "Projected ATD", "Book Odds", "Edge"]]
    st.markdown(df_display.to_markdown(index=False), unsafe_allow_html=True)

