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

import json

# ... (Previous imports)

# Load Hero Icons from Map (using contoh_response.json as source for now)
ICON_MAP = {}
EXAMPLE_JSON_PATH = os.path.join(PROJECT_ROOT, 'examples', 'contoh_response.json')
if os.path.exists(EXAMPLE_JSON_PATH):
    try:
        with open(EXAMPLE_JSON_PATH, 'r') as f:
            data = json.load(f)
            # Extract main hero
            if 'data' in data and 'records' in data['data']:
                for rec in data['data']['records']:
                    d = rec.get('data', {})
                    # Main Hero
                    mh = d.get('main_hero', {}).get('data', {})
                    if mh.get('name') and mh.get('head'):
                        ICON_MAP[mh['name']] = mh['head']
                    
                    # Sub Heroes
                    for sub in d.get('sub_hero', []):
                        sh = sub.get('hero', {}).get('data', {})
                        if sh.get('name') and sh.get('head'):
                            ICON_MAP[sh['name']] = sh['head']
    except Exception as e:
        print(f"Error loading icons: {e}")

def get_hero_icon(hero_name):
    # Return mapped icon or a default placeholder
    return ICON_MAP.get(hero_name, "https://static.wikia.nocookie.net/mobile-legends/images/0/05/Empty_Icon.png/revision/latest?cb=20171025063000")

# ... (Rest of format logic)


# --- Form Interface ---
roles = ['Exp', 'Jungle', 'Mid', 'Roam', 'Gold']

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
st.subheader("📊 Match History")

if os.path.exists(LOGS_PATH):
    df_logs = pd.read_csv(LOGS_PATH)
    # Sort latest first
    df_logs = df_logs.sort_values('Match_ID', ascending=False)
    
    # Helper to render a team list with icons
    def render_team_html(team_str, align="left"):
        html_parts = []
        if pd.isna(team_str): return ""
        picks = team_str.split('|')
        
        # Flex container for icons
        html_parts.append(f'<div style="display: flex; gap: 5px; flex-wrap: wrap; justify-content: {align}; margin-top: 5px;">')
        
        for pick in picks:
            if ':' in pick:
                h_name, role = pick.split(':')
                icon_url = get_hero_icon(h_name)
                # Icon Image with Tooltip
                html_parts.append(f'''
                    <img src="{icon_url}" title="{h_name} ({role})" 
                         style="width: 32px; height: 32px; border-radius: 50%; border: 1px solid #555;">
                ''')
        html_parts.append('</div>')
        return "".join(html_parts)

    for index, row in df_logs.iterrows():
        with st.container():
            # Card Styling
            
            win_icons = render_team_html(row['Winning_Team'], "left")
            lose_icons = render_team_html(row['Losing_Team'], "right")
            
            st.markdown(f"""
            <div style="background-color: #1E1E1E; padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #333;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <h4 style="margin: 0;">Match #{row['Match_ID']}</h4>
                    <span style="background-color: #333; padding: 5px 10px; border-radius: 5px; font-size: 0.8em;">
                        {row.get('Day', 'Unknown')} | {row.get('Game', 'Unknown')} | ⏱️ {row['Game_Duration']}
                    </span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <div style="width: 48%; color: #4CAF50;">
                        <strong>🏆 WIN: {row.get('Winner_Name', 'Unknown')}</strong><br>
                        {win_icons}
                    </div>
                    <div style="width: 48%; color: #F44336; text-align: right;">
                        <strong>❌ LOSE: {row.get('Loser_Name', 'Unknown')}</strong><br>
                        {lose_icons}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("No logs found yet.")
