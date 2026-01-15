import streamlit as st
import pandas as pd
import os
import sys

# Setup Paths
# Use absolute path relative to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, '..')
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
LOGS_PATH = os.path.join(DATA_DIR, 'match_logs_real.csv')
BASE_STATS_PATH = os.path.join(DATA_DIR, 'hero_base_stats.csv')

st.set_page_config(page_title="DraftNexus Log Entry", layout="wide")

@st.cache_data
def load_heroes():
    if not os.path.exists(BASE_STATS_PATH):
        st.error(f"Hero Stats not found at {BASE_STATS_PATH}")
        return []
    df = pd.read_csv(BASE_STATS_PATH)
    return sorted(df['Hero_Name'].unique().tolist())

# Load Data
heroes = load_heroes()
roles = ['Exp', 'Jungle', 'Mid', 'Roam', 'Gold']

st.title("🛡️ DraftNexus Match Logger")
st.markdown("Easily add new match logs to the dataset.")

# --- Form Interface ---
with st.form("match_entry_form"):
    st.subheader("Match Metadata")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        winner_name = st.text_input("Winner Team Name")
    with c2:
        loser_name = st.text_input("Loser Team Name")
    with c3:
        day = st.text_input("Day (e.g. Day 1)")
    with c4:
        game_num = st.text_input("Game (e.g. Game 1)")
        
    duration = st.text_input("Duration (mm:ss)", value="15:00")

    st.divider()
    
    # Teams Input
    col_win, col_lose = st.columns(2)
    
    with col_win:
        st.success("### 🏆 Winning Team")
        win_heroes = []
        for i, role in enumerate(roles):
            h = st.selectbox(f"Winner {role}", [""] + heroes, key=f"win_{role}")
            if h:
                win_heroes.append(f"{h}:{role}")
    
    with col_lose:
        st.error("### ❌ Losing Team")
        lose_heroes = []
        for i, role in enumerate(roles):
            h = st.selectbox(f"Loser {role}", [""] + heroes, key=f"lose_{role}")
            if h:
                lose_heroes.append(f"{h}:{role}")

    # Display Next ID
    if os.path.exists(LOGS_PATH):
        try:
            df = pd.read_csv(LOGS_PATH)
            next_id = df['Match_ID'].max() + 1
        except:
            next_id = 1
    else:
        next_id = 1
        
    st.info(f"🆔 Next Match ID will be: **{next_id}**")

    submitted = st.form_submit_button("💾 Save Match Log", type="primary")

    if submitted:
        # Validation
        if len(win_heroes) != 5 or len(lose_heroes) != 5:
            st.warning("⚠️ Please select exactly 5 heroes for each team.")
        elif not winner_name or not loser_name:
            st.warning("⚠️ Please enter Team Names.")
        else:
            # Construct Entry
            # Format: "Hero:Role|Hero:Role..."
            win_str = "|".join(win_heroes)
            lose_str = "|".join(lose_heroes)
            
            # Determine New Match ID (Recalculate to be safe)
            if os.path.exists(LOGS_PATH):
                df_current = pd.read_csv(LOGS_PATH)
                if not df_current.empty:
                    new_id = df_current['Match_ID'].max() + 1
                else:
                    new_id = 1
            else:
                new_id = 1
                df_current = pd.DataFrame(columns=['Match_ID', 'Winning_Team', 'Losing_Team', 'Game_Duration', 'Winner_Name', 'Loser_Name', 'Day', 'Game'])

            new_entry = {
                'Match_ID': new_id,
                'Winning_Team': win_str,
                'Losing_Team': lose_str,
                'Game_Duration': duration,
                'Winner_Name': winner_name,
                'Loser_Name': loser_name,
                'Day': day,
                'Game': game_num
            }
            
            # Append using pandas to ensure CSV safety
            df_new = pd.DataFrame([new_entry])
            
            # Use 'a' for append mode, but pandas to_csv header logic is tricky with append
            # Safest is to concat and write all (files are small)
            df_updated = pd.concat([df_current, df_new], ignore_index=True)
            df_updated.to_csv(LOGS_PATH, index=False)
            
            st.toast(f"✅ Match {new_id} Saved Successfully!")
            st.rerun() # Refresh to show new log immediately

# --- Preview Section ---
st.divider()
st.subheader("📊 All Match Logs")
if os.path.exists(LOGS_PATH):
    df_logs = pd.read_csv(LOGS_PATH)
    # Show all logs, sorted by latest first
    st.dataframe(df_logs.sort_values('Match_ID', ascending=False), use_container_width=True)
else:
    st.info("No logs found yet.")
