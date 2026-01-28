import streamlit as st
import pandas as pd
import numpy as np
import os
import joblib

# Setup Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, '..')
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
LOGS_PATH = os.path.join(DATA_DIR, 'match_logs_real.csv')
BASE_STATS_PATH = os.path.join(DATA_DIR, 'hero_base_stats.csv')
META_STATS_PATH = os.path.join(DATA_DIR, 'hero_meta_performance.csv')
MODEL_PATH = os.path.join(DATA_DIR, 'draft_model_rf.pkl')

st.set_page_config(page_title="DraftNexus AI", layout="wide", page_icon="⚔️")

# --- DATA LOADING ---
@st.cache_data
def load_hero_data():
    if not os.path.exists(BASE_STATS_PATH):
        st.error(f"Hero Stats not found at {BASE_STATS_PATH}")
        return [], {}, pd.DataFrame()
    
    df = pd.read_csv(BASE_STATS_PATH)
    
    # Hero List for Selectbox
    hero_list = sorted(df['Hero_Name'].unique().tolist())
    
    # Icon Map: Name -> URL
    if 'Icon_URL' in df.columns:
        icon_series = df.set_index('Hero_Name')['Icon_URL'].dropna()
        icon_map = icon_series.to_dict()
    else:
        icon_map = {}
        
    return hero_list, icon_map, df

@st.cache_resource
def load_model_resources():
    if not os.path.exists(MODEL_PATH) or not os.path.exists(META_STATS_PATH):
        return None, None
        
    clf = joblib.load(MODEL_PATH)
    df_meta = pd.read_csv(META_STATS_PATH)
    return clf, df_meta

heroes, ICON_MAP, DF_BASE = load_hero_data()
CLF, DF_META = load_model_resources()

# --- HELPER FUNCTIONS ---
def get_hero_icon(hero_name):
    return ICON_MAP.get(hero_name, "https://static.wikia.nocookie.net/mobile-legends/images/0/05/Empty_Icon.png/revision/latest?cb=20171025063000")

def get_real_match_heroes():
    if not os.path.exists(LOGS_PATH): return set()
    try:
        df = pd.read_csv(LOGS_PATH)
        heroes = set()
        for col in ['Winning_Team', 'Losing_Team']:
            # Handle potential float/NaN values strictly
            if col in df.columns:
                series = df[col].dropna().astype(str)
                for val in series:
                    if '|' in val:
                        picks = val.split('|')
                        for p in picks:
                            if ':' in p:
                                heroes.add(p.split(':')[0])
        return heroes
    except Exception as e:
        print(f"Error reading match logs: {e}")
        return set()

def predict_hero_role(hero_name):
    """
    Predicts the most likely role for a hero based on:
    1. Real Match Logs (Frequency)
    2. Base Stats (Primary Lane)
    """
    if not hero_name: return None
    
    # 1. Check Real Logs
    role_counts = {}
    if os.path.exists(LOGS_PATH):
        try:
            df = pd.read_csv(LOGS_PATH)
            for col in ['Winning_Team', 'Losing_Team']:
                if col in df.columns:
                    series = df[col].dropna().astype(str)
                    for val in series:
                        for pick in val.split('|'):
                            if ':' in pick:
                                h, r = pick.split(':')
                                if h == hero_name:
                                    role_counts[r] = role_counts.get(r, 0) + 1
        except: pass
        
    if role_counts:
        # Return most frequent role
        return max(role_counts, key=role_counts.get)
        
    # 2. Fallback to Base Stats
    # Map ID -> Primary Lane Int -> String
    # We need a reverse map from name -> ID first
    # DF_BASE is already loaded
    try:
        row = DF_BASE[DF_BASE['Hero_Name'] == hero_name].iloc[0]
        lane_int = row['Primary_Lane']
        role_map = {1: 'Exp', 2: 'Mid', 3: 'Roam', 4: 'Jungle', 5: 'Gold'}
        return role_map.get(lane_int, 'Flex')
    except:
        return 'Flex'

def predict_team_roles(hero_names):
    """
    Assigns roles to a list of heroes optimizing for conflict resolution.
    E.g. If Granger (Gold) and Freya (Exp/Gold) are picked, Granger gets Gold, Freya gets Exp.
    """
    if not hero_names: return {}
    
    # 1. Gather Candidates for each hero
    # format: { 'HeroName': {'Preferred': 'Gold', 'Options': ['Gold', 'Exp'], 'Score': 10} }
    hero_data = {}
    
    role_map_int = {1: 'Exp', 2: 'Mid', 3: 'Roam', 4: 'Jungle', 5: 'Gold'}
    
    # Pre-scan logs for frequency "cache"
    log_freqs = {} # (Hero, Role) -> count
    if os.path.exists(LOGS_PATH):
        try:
            df = pd.read_csv(LOGS_PATH, dtype={'Day': str})
            for col in ['Winning_Team', 'Losing_Team']:
                if col in df.columns:
                    series = df[col].dropna().astype(str)
                    for val in series:
                        for pick in val.split('|'):
                            if ':' in pick:
                                h, r = pick.split(':')
                                log_freqs[(h, r)] = log_freqs.get((h, r), 0) + 1
        except: pass

    for h in hero_names:
        if not h: continue
        options = set()
        preferred = None
        max_freq = 0
        
        # A. From Logs
        h_log_roles = [r for (name, r) in log_freqs.keys() if name == h]
        for r in h_log_roles:
            freq = log_freqs[(h, r)]
            options.add(r)
            if freq > max_freq:
                max_freq = freq
                preferred = r
                
        # B. From Base Stats
        try:
            row = DF_BASE[DF_BASE['Hero_Name'] == h].iloc[0]
            p_lane = role_map_int.get(row['Primary_Lane'])
            s_lane = role_map_int.get(row['Secondary_Lane']) # If exists
            
            if p_lane: 
                options.add(p_lane)
                if not preferred: preferred = p_lane
            if s_lane: options.add(s_lane)
        except: pass
        
        # Fallback
        if not options: options = {'Exp', 'Mid', 'Roam', 'Jungle', 'Gold'} # All valid if unknown
        if not preferred: preferred = list(options)[0]
        
        # Scarcity Score: Fewer options = Higher Priority
        # Also boost if hero has VERY high pick rate in one role
        score = 10 - len(options) 
        
        hero_data[h] = {
            'preferred': preferred,
            'options': list(options),
            'priority': score
        }
        
    # 2. Assignment (Greedy by Priority)
    # Sort heroes by priority (Highest first)
    sorted_heroes = sorted(hero_data.keys(), key=lambda x: hero_data[x]['priority'], reverse=True)
    
    assignments = {}
    filled_roles = set()
    
    # Pass 1: Try Preferred
    delayed = []
    
    for h in sorted_heroes:
        pref = hero_data[h]['preferred']
        if pref not in filled_roles:
            assignments[h] = pref
            filled_roles.add(pref)
        else:
            delayed.append(h)
            
    # Pass 2: Try Options
    for h in delayed:
        assigned = False
        # Try other options
        for opt in hero_data[h]['options']:
            if opt not in filled_roles:
                assignments[h] = opt
                filled_roles.add(opt)
                assigned = True
                break
        
        if not assigned:
            # Force Assign Preferred (Duplicate)
            assignments[h] = hero_data[h]['preferred']
            
    return assignments

def get_recommendations(allies, enemies, banned=None, restrict_pool=False):
    # Prepare Data
    if DF_BASE.empty or CLF is None: return []
    if banned is None: banned = []
    
    # Merge for stats
    if 'Hero_ID' not in DF_META.columns or 'Hero_ID' not in DF_BASE.columns:
        return []
        
    df_stats = pd.merge(DF_BASE, DF_META[['Hero_ID', 'Early_Power', 'Mid_Power', 'Late_Power']], on='Hero_ID', how='left')
    
    # Mappings
    name_to_id = {name: pid for name, pid in zip(df_stats['Hero_Name'], df_stats['Hero_ID'])}
    id_to_name = {pid: name for name, pid in name_to_id.items()}
    lane_int_map = {'Exp':1, 'Mid':2, 'Roam':3, 'Jungle':4, 'Gold':5}

    # IDs
    ally_ids = [name_to_id[n] for n in allies if n in name_to_id]
    enemy_ids = [name_to_id[n] for n in enemies if n in name_to_id]
    banned_ids = [name_to_id[n] for n in banned if n in name_to_id]
    taken = set(ally_ids + enemy_ids + banned_ids)
    
    # Real Pool Filtering
    valid_pool = None
    if restrict_pool:
        real_hero_names = get_real_match_heroes()
        valid_pool = set()
        for name in real_hero_names:
            if name in name_to_id:
                valid_pool.add(name_to_id[name])
    
    # Candidates
    hero_ids = sorted(df_stats['Hero_ID'].unique())
    id_to_idx = {hid: i for i, hid in enumerate(hero_ids)}
    n_heroes = len(hero_ids)
    
    candidates = []
    for h in hero_ids:
        if h in taken: continue
        if valid_pool is not None and h not in valid_pool: continue
        candidates.append(h)
        
    if not candidates: return []
    
    # Prepare Context Vectors
    ally_vec = np.zeros(n_heroes)
    enemy_vec = np.zeros(n_heroes)
    roles_vec = [0.0] * 5
    
    # Use Predicted Roles for Allies to populate roles_vec
    # This gives the model context on what roles we ALREADY have
    for name in allies:
        predicted_role = predict_hero_role(name)
        if predicted_role in lane_int_map:
            l_idx = lane_int_map[predicted_role] - 1
            roles_vec[l_idx] += 1.0

    # Populate One-Hot Vectors
    for h in ally_ids:
        if h in id_to_idx: ally_vec[id_to_idx[h]] = 1
            
    for h in enemy_ids:
        if h in id_to_idx: enemy_vec[id_to_idx[h]] = 1
        
    # Feature Map
    stat_cols = ['Primary_Lane', 'Damage_Type', 'Hard_CC_Count', 'Flex_Pick_Score', 'Escape_Reliability', 
                 'Difficulty', 'Economy_Dependency', 'Early_Power', 'Mid_Power', 'Late_Power']
    stats_map = df_stats.set_index('Hero_ID')[stat_cols].to_dict('index')
    
    X_pred = []
    valid_cands = []
    
    for cid in candidates:
        stats = stats_map.get(cid)
        if not stats: continue
        
        cand_vec = [stats[c] for c in stat_cols]
        full_vec = np.concatenate([ally_vec, enemy_vec, roles_vec, cand_vec])
        X_pred.append(full_vec)
        valid_cands.append(cid)
        
    if not X_pred: return []
    
    # Predict
    probs = CLF.predict_proba(X_pred)[:, 1]
    
    # Result Format
    results = []
    role_map_int = {1: 'Exp', 2: 'Mid', 3: 'Roam', 4: 'Jungle', 5: 'Gold'}
    for i, pid in enumerate(valid_cands):
        name = id_to_name[pid]
        # Candidate's natural role
        role = role_map_int.get(stats_map[pid]['Primary_Lane'], 'Flex')
        icon = get_hero_icon(name)
        results.append((name, probs[i], role, icon))
        
    results.sort(key=lambda x: x[1], reverse=True)
    return results

# --- HELPER: GAME AUTO-INCREMENT ---
def calculate_next_game_number(team_a, team_b):
    if not team_a or not team_b: return "1"
    
    if os.path.exists(LOGS_PATH):
        try:
            df = pd.read_csv(LOGS_PATH)
            # Normalize names for comparison (optional, but good practice)
            ta = team_a.strip()
            tb = team_b.strip()
            
            # Filter matches involving THESE two teams
            mask = (
                ((df['Winner_Name'] == ta) & (df['Loser_Name'] == tb)) |
                ((df['Winner_Name'] == tb) & (df['Loser_Name'] == ta))
            )
            relevant_games = df[mask]
            
            if relevant_games.empty:
                return "1"
                
            # Extract numbers from "Game X"
            # Assumes format "Game <Number>"
            import re
            max_num = 0
            for val in relevant_games['Game'].astype(str):
                match = re.search(r'\d+', val)
                if match:
                    num = int(match.group())
                    if num > max_num: max_num = num
            
            return f"{max_num + 1}"
            
        except Exception as e:
            print(f"Error calculating game number: {e}")
            return "1"
    return "1"

def swap_teams():
    w = st.session_state.get('input_winner', '')
    l = st.session_state.get('input_loser', '')
    st.session_state['input_winner'] = l
    st.session_state['input_loser'] = w

# --- UI COMPONENTS ---
def render_logger():
    st.header("📝 Match Logger")
    roles = ['Exp', 'Jungle', 'Mid', 'Roam', 'Gold']
    
    
    # --- MATCH METADATA (Interactive - Outside Form) ---
    st.subheader("Match Metadata")
    
    with st.container():
        
        # --- Stage Select ---
        stage = st.selectbox("Stage", ["Knockout Stage", "Swiss Stage", "Grand Finals"], index=0)
        
        
        c1, c2, c3, c4 = st.columns([2, 0.5, 2, 1])
        
        # Initialize session state if not present (prevents key errors on first run)
        if 'input_winner' not in st.session_state: st.session_state['input_winner'] = ""
        if 'input_loser' not in st.session_state: st.session_state['input_loser'] = ""

        with c1: 
            winner_name = st.text_input("Winner Team Name", key="input_winner")
        with c2: 
            st.write("") # Spacer
            st.write("")
            st.button("🔄", on_click=swap_teams, help="Swap Winner and Loser")
        with c3: 
            loser_name = st.text_input("Loser Team Name", key="input_loser")
        with c4: 
            day = st.text_input("Day (e.g. Day 1)")
            
        # Preview Next Game Number
        next_game_val = calculate_next_game_number(st.session_state.input_winner, st.session_state.input_loser)
        st.caption(f"🎮 Next Game: **{next_game_val}** (Auto-Detected)")
            
        duration = st.text_input("Duration (mm:ss)", value="15:00")

    # --- HERO SELECTION (Form - Batch Submission) ---
    with st.form("match_entry_form"):
        st.divider()
        col_win, col_lose = st.columns(2)
        with col_win:
            st.success("### 🏆 Winning Team")
            win_heroes = []
            for role in roles:
                h = st.selectbox(f"Winner {role}", [""] + heroes, key=f"win_{role}")
                if h: win_heroes.append(f"{h}:{role}")
        
        with col_lose:
            st.error("### ❌ Losing Team")
            lose_heroes = []
            for role in roles:
                h = st.selectbox(f"Loser {role}", [""] + heroes, key=f"lose_{role}")
                if h: lose_heroes.append(f"{h}:{role}")

        # ID Logic
        if os.path.exists(LOGS_PATH):
            try:
                df = pd.read_csv(LOGS_PATH)
                next_id = df['Match_ID'].max() + 1 if not df.empty else 1
            except: next_id = 1
        else: next_id = 1
            
        st.info(f"🆔 Next Match ID will be: **{next_id}**")
        submitted = st.form_submit_button("💾 Save Match Log", type="primary")

        if submitted:
            if len(win_heroes) != 5 or len(lose_heroes) != 5:
                st.warning("⚠️ Please select exactly 5 heroes for each team.")
            elif not winner_name or not loser_name:
                st.warning("⚠️ Please enter Team Names.")
            else:
                # Save Logic
                if os.path.exists(LOGS_PATH):
                    df_current = pd.read_csv(LOGS_PATH, dtype={'Day': str})
                    # Migration: If Stage missing, add it
                    if 'Stage' not in df_current.columns:
                        df_current['Stage'] = 'Swiss Stage'
                    
                    new_id = df_current['Match_ID'].max() + 1 if not df_current.empty else 1
                else:
                    new_id = 1
                    df_current = pd.DataFrame(columns=['Match_ID', 'Winning_Team', 'Losing_Team', 'Game_Duration', 'Winner_Name', 'Loser_Name', 'Day', 'Game', 'Stage'])

                new_entry = {
                    'Match_ID': new_id,
                    'Winning_Team': "|".join(win_heroes),
                    'Losing_Team': "|".join(lose_heroes),
                    'Game_Duration': duration,
                    'Winner_Name': winner_name,
                    'Loser_Name': loser_name,
                    'Day': day,
                    'Game': next_game_val,
                    'Stage': stage
                }
                
                df_updated = pd.concat([df_current, pd.DataFrame([new_entry])], ignore_index=True)
                df_updated.to_csv(LOGS_PATH, index=False)
                st.toast(f"✅ Match {new_id} Saved Successfully!")
                st.rerun()

    # History
    st.divider()
    st.subheader("📊 Match History")
    if os.path.exists(LOGS_PATH):
        df_logs = pd.read_csv(LOGS_PATH, dtype={'Day': str}).sort_values('Match_ID', ascending=False)
        for index, row in df_logs.iterrows():
            with st.container():
                st.markdown(f"""
                <div style="background-color: #1E1E1E; padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #333;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <h4 style="margin: 0;">Match #{row['Match_ID']} <span style="font-size: 0.8em; color: #888;">({row.get('Stage', 'Swiss Stage')})</span></h4>
                        <span style="background-color: #333; padding: 5px 10px; border-radius: 5px; font-size: 0.8em;">
                            {row.get('Day', 'Unknown')} | {row.get('Game', 'Unknown')} | ⏱️ {row['Game_Duration']}
                        </span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <div style="width: 48%; color: #4CAF50;">
                            <strong>🏆 WIN: {row.get('Winner_Name', 'Unknown')}</strong><br>
                            {render_team_html(row['Winning_Team'], "left")}
                        </div>
                        <div style="width: 48%; color: #F44336; text-align: right;">
                            <strong>❌ LOSE: {row.get('Loser_Name', 'Unknown')}</strong><br>
                            {render_team_html(row['Losing_Team'], "right")}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No logs found yet.")

def render_team_html(team_str, align="left"):
    if pd.isna(team_str): return ""
    picks = team_str.split('|')
    html_parts = [f'<div style="display: flex; gap: 5px; flex-wrap: wrap; justify-content: {align}; margin-top: 5px;">']
    for pick in picks:
        if ':' in pick:
            h_name, role = pick.split(':')
            icon_url = get_hero_icon(h_name)
            html_parts.append(f'<img src="{icon_url}" title="{h_name} ({role})" style="width: 32px; height: 32px; border-radius: 50%; border: 1px solid #555;">')
    html_parts.append('</div>')
    return "".join(html_parts)


def render_recommender():
    st.header("🔮 Draft Recommender")
    
    if CLF is None or DF_BASE.empty:
        st.error("Model or Stats not found. Please train the model first.")
        return

    # --- BANNED HEROES INPUTS ---
    with st.expander("🚫 Banned Heroes (10 Slots)", expanded=True):
        banned = []
        b_cols1 = st.columns(5)
        b_cols2 = st.columns(5)
        
        for i in range(5):
            with b_cols1[i]:
                h = st.selectbox(f"Ban {i+1}", [""] + heroes, key=f"ban_p_{i}")
                if h: banned.append(h)
        for i in range(5):
            with b_cols2[i]:
                h = st.selectbox(f"Ban {i+6}", [""] + heroes, key=f"ban_p_{i+5}")
                if h: banned.append(h)

    # --- ENEMY TEAM INPUTS ---
    st.error("### ⚔️ Enemy Team (Flex)")
    enemies = []
    
    # 1. Gather current selections from state to run batch prediction
    current_enemies = []
    for i in range(5):
        key = f"enemy_p_{i}"
        if key in st.session_state and st.session_state[key]:
            current_enemies.append(st.session_state[key])
            
    enemy_role_map = predict_team_roles(current_enemies)
    
    e_cols = st.columns(5)
    for i in range(5):
        with e_cols[i]:
            # Filter options: Exclude banned?
            avail_heroes = [h for h in heroes if h not in banned]
            h = st.selectbox(f"Enemy {i+1}", [""] + avail_heroes, key=f"enemy_p_{i}")
            if h: 
                enemies.append(h)
                # DISPLAY PREDICTED ROLE
                pred_role = enemy_role_map.get(h, "Unknown")
                st.caption(f"Detected: **{pred_role}**")
    
    # --- ALLY TEAM INPUTS (UPDATED: FLEX & SMART) ---
    st.success("### 🛡️ Allied Team (Flex & Predict)")
    allies = []
    filled_roles = set()
    
    # 1. Gather current selections
    current_allies = []
    for i in range(5):
        key = f"ally_p_{i}"
        if key in st.session_state and st.session_state[key]:
            current_allies.append(st.session_state[key])
            
    ally_role_map = predict_team_roles(current_allies)
    
    a_cols = st.columns(5)
    
    for i in range(5):
        with a_cols[i]:
            # Filter: Exclude enemies + banned
            exclude = set(enemies + banned + allies) 
            avail_heroes = [h for h in heroes if h not in exclude]
            
            h = st.selectbox(f"Ally {i+1}", [""] + avail_heroes, key=f"ally_p_{i}")
            
            if h: 
                allies.append(h)
                # DISPLAY PREDICTED ROLE
                pred_role = ally_role_map.get(h, "Unknown")
                if pred_role != "Unknown":
                    filled_roles.add(pred_role)
                st.caption(f"Detected: **{pred_role}**")

    # --- CONTROLS ---
    st.divider()
    
    if st.toggle("Restrict to Real Match Heroes", value=True, help="Only recommend heroes that have appeared in your real match logs."):
        restrict_pool = True
    else:
        restrict_pool = False

    # Real-time Analysis
    if enemies or allies or banned: # trigger if banned are set too? meaningful context usually needs picks, but ok.
        with st.spinner("Analyzing Draft..."):
            recs = get_recommendations(allies, enemies, banned, restrict_pool)
            if recs:
                st.subheader("✨ Best Pick per Role")
                cols = st.columns(5)
                
                # Setup Display Roles
                display_roles = ['Exp', 'Jungle', 'Mid', 'Roam', 'Gold']
                
                # Group best recommendations by role
                best_by_role = {r: None for r in display_roles}
                
                # Find best rec for each role
                for r in recs:
                    name, score, role, icon = r
                    if role in display_roles:
                        if best_by_role[role] is None:
                            best_by_role[role] = r

                for i, target in enumerate(display_roles):
                    with cols[i]:
                        is_filled = target in filled_roles
                        header_text = f"{target} (Alt)" if is_filled else target
                        header_color = "#888" if is_filled else "#EEE"
                        
                        st.markdown(f"<h5 style='text-align: center; color: {header_color};'>{header_text}</h5>", unsafe_allow_html=True)
                        hero_data = best_by_role[target]
                        
                        if hero_data:
                            name, score, role, icon = hero_data
                            border_color = "#888" if is_filled else "#FF4B4B" 
                            opacity = "0.7" if is_filled else "1.0"
                            
                            st.markdown(f"""
                            <div style="text-align: center; background-color: #262730; padding: 10px; border-radius: 10px; border: 1px solid #444; opacity: {opacity};">
                                <img src="{icon}" style="width: 64px; height: 64px; border-radius: 50%; border: 2px solid {border_color}; margin-bottom: 5px;">
                                <h5 style="margin: 0;">{name}</h5>
                                <h4 style="color: #4CAF50; margin: 5px 0 0 0;">{(score*100):.1f}%</h4>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                             st.markdown(f"""
                            <div style="text-align: center; padding: 20px; color: #555;">
                                <i>No Rec</i>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.info("Select heroes to get recommendations.")
    else:
        st.info("Start by selecting Enemy or Allied heroes.")

# --- MAIN APP ---
def main():
    st.sidebar.title("DraftNexus AI")
    # Swap order to make Recommender default
    mode = st.sidebar.radio("Navigation", ["Draft Recommender", "Match Logger"])
    
    if mode == "Match Logger":
        render_logger()
    else:
        render_recommender()

if __name__ == "__main__":
    main()
