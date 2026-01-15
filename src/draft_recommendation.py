import pandas as pd
import numpy as np
import os
import joblib
import sys
import argparse

# Paths
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data'))
BASE_STATS_PATH = os.path.join(DATA_DIR, 'hero_base_stats.csv')
META_STATS_PATH = os.path.join(DATA_DIR, 'hero_meta_performance.csv')
MODEL_PATH = os.path.join(DATA_DIR, 'draft_model_rf.pkl')
REAL_LOGS_PATH = os.path.join(DATA_DIR, 'match_logs_real.csv')

def load_resources():
    if not os.path.exists(BASE_STATS_PATH) or not os.path.exists(MODEL_PATH) or not os.path.exists(META_STATS_PATH):
        print("Error: Missing data or model file.")
        sys.exit(1)

    df_base = pd.read_csv(BASE_STATS_PATH)
    df_meta = pd.read_csv(META_STATS_PATH)
    clf = joblib.load(MODEL_PATH)

    # Merge Base + Meta
    df_stats = pd.merge(df_base, df_meta[['Hero_ID', 'Early_Power', 'Mid_Power', 'Late_Power']], on='Hero_ID', how='left')

    return df_stats, clf

def get_real_match_heroes(name_to_id):
    """Extracts a set of Hero IDs that have appeared in real match logs."""
    # Load Real Logs to find "M7 Heroes" (Heroes actually played)
    RESTRICT_TO_REAL_DATA = True # Set to False to recommend ALL heroes

    allowed_ids = None
    if RESTRICT_TO_REAL_DATA and os.path.exists(REAL_LOGS_PATH):
        try:
            df_real = pd.read_csv(REAL_LOGS_PATH)
            real_heroes = set()
            for _, row in df_real.iterrows():
                # Parse 'Winning_Team' and 'Losing_Team' strings
                for team_str_col in ['Winning_Team', 'Losing_Team']:
                    team_str = row[team_str_col]
                    if pd.isna(team_str): continue # Skip if NaN
                    
                    parts = str(team_str).split('|')
                    for p in parts:
                        name_part = p.split(':')[0].strip().replace('"', '')
                        if name_part.lower() in name_to_id:
                            real_heroes.add(name_to_id[name_part.lower()])
            
            allowed_ids = real_heroes
            print(f"Filter Active: Restricted to {len(allowed_ids)} heroes found in real matches.")
        except Exception as e:
            print(f"Error reading match logs: {e}. Allowing all heroes.")
            allowed_ids = None # Fallback to allowing all heroes if error
    else:
        print("Filter Inactive: Recommending from ALL heroes.")
        allowed_ids = None # Explicitly set to None if filter is inactive or file not found

    return allowed_ids

def get_hero_id(name, name_to_id):
    name_clean = name.strip().lower()
    return name_to_id.get(name_clean)

def recommend(allies, enemies, top_k=5, restrict=True):
    df_stats, clf = load_resources()

    # Mappings
    name_to_id = {name.lower(): pid for name, pid in zip(df_stats['Hero_Name'], df_stats['Hero_ID'])}
    id_to_name = {pid: name for name, pid in name_to_id.items()}

    # Get Allowed Heroes from Real Logs
    # Filtering Logic (M7 Data)
    allowed_ids = None
    if restrict:
        if os.path.exists(REAL_LOGS_PATH):
            try:
                df_real = pd.read_csv(REAL_LOGS_PATH)
                real_heroes = set()
                for _, row in df_real.iterrows():
                    for team_str_col in ['Winning_Team', 'Losing_Team']:
                        team_str = row[team_str_col]
                        if pd.isna(team_str): continue
                        parts = str(team_str).split('|')
                        for p in parts:
                            name_part = p.split(':')[0].strip().replace('"', '')
                            if name_part.lower() in name_to_id:
                                real_heroes.add(name_to_id[name_part.lower()])
                allowed_ids = real_heroes
                print(f"Filter Active: Restricted to {len(allowed_ids)} heroes found in real matches.")
            except Exception as e:
                print(f"Error reading match logs: {e}. Allowing all heroes.")
        else:
             print("Warning: Real logs not found. Filter ignored.")
    else:
        print("Filter Inactive: Recommending from ALL heroes.")

    # Validation
    # Role Parser
    role_name_map = {
        'exp': 1, 'mid': 2, 'roam': 3, 'jungle': 4, 'gold': 5,
        'explane': 1, 'midlane': 2, 'roamer': 3, 'jungler': 4, 'goldlane': 5
    }

    def parse_team_input(team_list, team_type="Ally"):
        ids = []
        roles = {}
        for entry in team_list:
            if ':' in entry:
                name_part, role_parts = entry.split(':', 1)
                target_role = role_name_map.get(role_parts.strip().lower())
            else:
                name_part = entry
                target_role = None

            hid = get_hero_id(name_part, name_to_id)
            if hid: 
                ids.append(hid)
                if target_role:
                    roles[hid] = target_role
            else: 
                print(f"Warning: {team_type} hero '{entry}' not found.")
        return ids, roles

    # Parse Inputs
    ally_ids, ally_roles = parse_team_input(allies, "Ally")
    enemy_ids, enemy_roles = parse_team_input(enemies, "Enemy")

    # Feature Engineering Prep (Must match train_model.py)
    hero_ids = sorted(df_stats['Hero_ID'].unique())
    id_to_idx = {hid: i for i, hid in enumerate(hero_ids)}
    n_heroes = len(hero_ids)

    stat_cols = ['Primary_Lane', 'Damage_Type', 'Hard_CC_Count', 'Flex_Pick_Score', 'Escape_Reliability',
                 'Difficulty', 'Economy_Dependency', 'Early_Power', 'Mid_Power', 'Late_Power']
    stats_map = df_stats.set_index('Hero_ID')[stat_cols].to_dict('index')

    # Filter taken heroes
    taken_ids = set(ally_ids + enemy_ids)
    
    # Filter candidates: Must be in permitted list AND not taken
    candidates = []
    for h in hero_ids:
        if h in taken_ids:
            continue
        if allowed_ids is not None and h not in allowed_ids:
            continue
        candidates.append(h)

    print(f"\nAnalyzing {len(candidates)} candidates for Allied Team: {allies} vs Enemy Team: {enemies}...")

    predictions = []

    # Base Vectors (Context)
    ally_vec = np.zeros(n_heroes)
    enemy_vec = np.zeros(n_heroes)

    # Precompute Role Map
    lane_map = df_stats.set_index('Hero_ID')['Primary_Lane'].to_dict()
    roles_vec = [0.0] * 5

    for h in ally_ids:
        if h in id_to_idx: ally_vec[id_to_idx[h]] = 1
        
        # Check for override, else allow default
        lane = ally_roles.get(h, lane_map.get(h, 0))
        
        if 1 <= lane <= 5:
                roles_vec[lane-1] += 1.0

    for h in enemy_ids:
        if h in id_to_idx: enemy_vec[id_to_idx[h]] = 1

    # Evaluate Candidates
    X_pred = []
    valid_candidates = []

    for cand_id in candidates:
        c_stats = stats_map.get(cand_id)
        if not c_stats: continue

        cand_vec = [
            c_stats['Primary_Lane'],
            c_stats['Damage_Type'],
            c_stats['Hard_CC_Count'],
            c_stats['Flex_Pick_Score'],
            c_stats['Escape_Reliability'],
            c_stats['Difficulty'],
            c_stats['Economy_Dependency'],
            c_stats['Early_Power'],
            c_stats['Mid_Power'],
            c_stats['Late_Power']
        ]

        full_vec = np.concatenate([ally_vec, enemy_vec, roles_vec, cand_vec])
        X_pred.append(full_vec)
        valid_candidates.append(cand_id)

    if not X_pred:
        print("No valid candidates found.")
        return

    # Batch Predict Probabilities
    # We want Probability of Class 1 (Good Pick)
    probs = clf.predict_proba(X_pred)[:, 1]

    # Rank
    results = []
    for i, pid in enumerate(valid_candidates):
        score = probs[i]
        results.append((pid, score))

    results.sort(key=lambda x: x[1], reverse=True)

    # Group by Lane
    lane_recommendations = {1: [], 2: [], 3: [], 4: [], 5: []}
    role_map_display = {1: 'Exp Lane', 2: 'Mid Lane', 3: 'Roamer', 4: 'Jungler', 5: 'Gold Lane'}

    for pid, score in results:
        s = stats_map[pid]
        lane = s.get('Primary_Lane', 0)
        if lane in lane_recommendations:
            lane_recommendations[lane].append((pid, score))

    print(f"\n--- Best Picks by Role (Top 3 per Lane) ---")
    for lane in range(1, 6):
        role_name = role_map_display[lane]
        picks = lane_recommendations[lane]
        
        print(f"[{role_name}]")
        if picks:
            # Get top 3 for this lane
            for i in range(min(3, len(picks))):
                pid, score = picks[i]
                name = id_to_name[pid]
                print(f"  {i+1}. {name.title():<15} (Score: {score:.4f})")
        else:
            print(f"  No suitable candidates found.")


    print(f"\n--- Overall Top {top_k} Recommendations ---")
    for i in range(min(top_k, len(results))):
        pid, score = results[i]
        name = id_to_name[pid]
        s = stats_map[pid]
        role = role_map_display.get(s['Primary_Lane'], 'Unknown')
        print(f"{i+1}. {name.title()} ({role}) - Score: {score:.4f}")

if __name__ == "__main__":
    print("\n=== MOBA DRAFT RECOMMENDER TESTS ===\n")

    # Scenario 1: The "Safe Opener"
    # Logic: Empty board. Should recommend strong Roamers or Flexible picks.
    print("--- Scenario 1: First Pick (Roam Priority) ---")
    recommend(allies=["Leomord:Jungle", "Freya"], enemies=["Valir:Mid", "Tigreal:Roam"])
