import pandas as pd
import numpy as np
import os
import joblib
import sys
import argparse

# Paths
DATA_DIR = './data'
BASE_STATS_PATH = os.path.join(DATA_DIR, 'hero_base_stats.csv')
META_STATS_PATH = os.path.join(DATA_DIR, 'hero_meta_performance.csv')
MODEL_PATH = os.path.join(DATA_DIR, 'draft_model_rf.pkl')

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

def get_hero_id(name, name_to_id):
    name_clean = name.strip().lower()
    return name_to_id.get(name_clean)

def recommend(allies, enemies, top_k=5):
    df_stats, clf = load_resources()
    
    # Mappings
    name_to_id = {name.lower(): pid for name, pid in zip(df_stats['Hero_Name'], df_stats['Hero_ID'])}
    id_to_name = {pid: name for name, pid in name_to_id.items()}
    
    # Validation
    ally_ids = []
    for name in allies:
        hid = get_hero_id(name, name_to_id)
        if hid: ally_ids.append(hid)
        else: print(f"Warning: Ally hero '{name}' not found.")
            
    enemy_ids = []
    for name in enemies:
        hid = get_hero_id(name, name_to_id)
        if hid: enemy_ids.append(hid)
        else: print(f"Warning: Enemy hero '{name}' not found.")
        
    # Feature Engineering Prep (Must match train_model.py)
    hero_ids = sorted(df_stats['Hero_ID'].unique())
    id_to_idx = {hid: i for i, hid in enumerate(hero_ids)}
    n_heroes = len(hero_ids)
    
    stat_cols = ['Primary_Lane', 'Damage_Type', 'Hard_CC_Count', 'Flex_Pick_Score', 'Escape_Reliability', 
                 'Difficulty', 'Economy_Dependency', 'Early_Power', 'Mid_Power', 'Late_Power']
    stats_map = df_stats.set_index('Hero_ID')[stat_cols].to_dict('index')
    
    # Filter taken heroes
    taken_ids = set(ally_ids + enemy_ids)
    candidates = [h for h in hero_ids if h not in taken_ids]
    
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
        if h in lane_map:
            lane = lane_map[h]
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
    
    print(f"\n--- Top {top_k} Recommendations ---")
    for i in range(min(top_k, len(results))):
        pid, score = results[i]
        name = id_to_name[pid]
        # Get role/stats for display
        s = stats_map[pid]
        role_map = {1: 'Exp', 2: 'Mid', 3: 'Roam', 4: 'Jungle', 5: 'Gold'}
        role = role_map.get(s['Primary_Lane'], 'Unknown')
        print(f"{i+1}. {name.title()} ({role}) - Score: {score:.4f}")
        
if __name__ == "__main__":
    print("\n=== MOBA DRAFT RECOMMENDER TESTS ===\n")

    # Scenario 1: The "Safe Opener"
    # Logic: Empty board. Should recommend strong Roamers or Flexible picks.
    print("--- Scenario 1: First Pick (Roam Priority) ---")
    recommend(allies=[], enemies=["Lancelot"])
    
    # Scenario 2: The "M7 Gold Lane"
    # Logic: Team has Exp, Roam, Jungle, Mid. Needs Gold Lane (Magic Dmg preferred due to YZ/Haya).
    print("\n--- Scenario 2: Filling Gold Lane (M7 Match) ---")
    recommend(allies=['Yu Zhong', 'Chou', 'Hayabusa', 'Valentina'], 
              enemies=['Lancelot', 'Grock', 'Claude', 'Lapu-Lapu', 'Lunox'])
              
    # Scenario 3: "We Need Magic!"
    # Logic: 4 Physical Heroes. Model MUST suggest a Mage for Mid.
    print("\n--- Scenario 3: Balancing Damage Type (Needs Mage) ---")
    recommend(allies=['Saber', 'Brody', 'Chou', 'Yu Zhong'], enemies=['Tigreal'])
    
    # Scenario 4: "Stop the Fanny"
    # Logic: Enemy has Fanny (High Mobility). Model should suggest Hard CC (Khufra, Franco, Kaja).
    print("\n--- Scenario 4: Counter-Pick (Anti-Fanny) ---")
    recommend(allies=['Clint'], enemies=['Fanny'])
    
    # Scenario 5: "Exp Lane Duel"
    # Logic: Team needs an Exp Laner to face Dyroth (Strong 1v1).
    print("\n--- Scenario 5: Exp Lane Fill (Vs Dyroth) ---")
    recommend(allies=['Pharsa', 'Tigreal', 'Granger', 'Nolan'], enemies=['Dyrroth'])
