import pandas as pd
import numpy as np
import os
import json
import random

# Paths
DATA_DIR = './data'
BASE_STATS_PATH = os.path.join(DATA_DIR, 'hero_base_stats.csv')
META_STATS_PATH = os.path.join(DATA_DIR, 'hero_meta_performance.csv')
COUNTER_PATH = os.path.join(DATA_DIR, 'hero_counter_stats.csv')
COMPAT_PATH = os.path.join(DATA_DIR, 'hero_compatibility_stats.csv')
REAL_LOGS_PATH = os.path.join(DATA_DIR, 'match_logs_real.csv')
OUTPUT_PATH = os.path.join(DATA_DIR, 'training_data_hybrid.csv')

# Constraints
MAX_RELATION_LOOKUP = 5 # Top 5 counters/partners

def load_data():
    """Lengths stats maps from CSVs"""
    if not os.path.exists(BASE_STATS_PATH) or not os.path.exists(META_STATS_PATH):
        raise FileNotFoundError("Stats files missing")
        
    df_base = pd.read_csv(BASE_STATS_PATH)
    df_meta = pd.read_csv(META_STATS_PATH)
    
    # Map Name -> ID and ID -> Stats
    name_to_id = {name.lower(): pid for name, pid in zip(df_base['Hero_Name'], df_base['Hero_ID'])}
    id_to_stats = df_base.set_index('Hero_ID').to_dict('index')
    
    # Meta Stats for Power Spikes
    id_to_meta = df_meta.set_index('Hero_ID')[['Early_Power', 'Mid_Power', 'Late_Power']].to_dict('index')
    
    # Load Relations
    counters = {}
    synergies = {}
    
    if os.path.exists(COUNTER_PATH):
        df_count = pd.read_csv(COUNTER_PATH)
        for _, row in df_count.iterrows():
            counters[row['Hero_ID']] = {
                'strong': json.loads(row['Strong_Against_JSON']),
                'weak': json.loads(row['Weak_Against_JSON'])
            }

    if os.path.exists(COMPAT_PATH):
        df_comp = pd.read_csv(COMPAT_PATH)
        for _, row in df_comp.iterrows():
            synergies[row['Hero_ID']] = {
                'best': json.loads(row['Best_Teammate_JSON']),
                'worst': json.loads(row['Worst_Teammate_JSON'])
            }
            
    return name_to_id, id_to_stats, id_to_meta, counters, synergies

def parse_real_logs(name_to_id, id_to_meta):
    """Parses user provided match logs"""
    real_samples = []
    
    if not os.path.exists(REAL_LOGS_PATH):
        print("No real logs found, skipping real data ingestion.")
        return []
        
    df_real = pd.read_csv(REAL_LOGS_PATH)
    print(f"Loading {len(df_real)} real matches...")
    
    for _, row in df_real.iterrows():
        try:
            win_str = row['Winning_Team']
            lose_str = row['Losing_Team']
            
            # Helper to parse "Name:Role"
            def parse_team(team_str):
                ids = []
                parts = team_str.split('|')
                for p in parts:
                    name_part = p.split(':')[0].strip().replace('"', '')
                    if name_part.lower() in name_to_id:
                        ids.append(name_to_id[name_part.lower()])
                return ids

            win_ids = parse_team(win_str)
            lose_ids = parse_team(lose_str)
            duration = float(row.get('Game_Duration', 15)) 
            
            if len(win_ids) == 5 and len(lose_ids) == 5:
                for i in range(5):
                    candidate = win_ids[i]
                    allies = win_ids[:i] 
                    enemies = lose_ids 
                    
                    # Strategic Weight Calculation
                    # 1. Base Real Data Weight
                    weight = 3.0
                    
                    # 2. Temporal Fit Bonus
                    # Did this hero contribute to the specific win condition (Fast vs Long)?
                    stats = id_to_meta.get(candidate, {})
                    is_aligned = False
                    
                    if duration <= 13: # Fast Game
                        if stats.get('Early_Power', 0) > 0.6: 
                            is_aligned = True
                    elif duration >= 18: # Long Game
                        if stats.get('Late_Power', 0) > 0.6: 
                            is_aligned = True
                    else: # Mid Game
                        if stats.get('Mid_Power', 0) > 0.6:
                            is_aligned = True
                            
                    if is_aligned:
                        weight = 6.0 # Double weight for "Perfect Fit" samples
                    
                    real_samples.append({
                        'enemy_ids': str(enemies),
                        'ally_ids': str(allies),
                        'candidate_id': candidate,
                        'label': 1, 
                        'is_real': weight
                    })
                    
        except Exception as e:
            print(f"Error parsing match {row.get('Match_ID', '?')}: {e}")
            
    return real_samples

def generate_synthetic_samples(id_to_stats, counters, synergies, n_samples=3000):
    """Generates mock data based on rules"""
    samples = []
    hero_ids = list(id_to_stats.keys())
    
    print(f"Generating {n_samples} synthetic samples...")
    
    samples = []
    target_pos = n_samples // 2
    target_neg = n_samples - target_pos
    
    count_pos = 0
    count_neg = 0
    
    attempts = 0
    max_attempts = n_samples * 5 # Prevent infinite loop
    
    while (count_pos < target_pos or count_neg < target_neg) and attempts < max_attempts:
        attempts += 1
        
        # Random draft state
        n_allies = random.randint(1, 4) # At least 1 ally to have context
        ally_ids = random.sample(hero_ids, n_allies)
        remaining = [h for h in hero_ids if h not in ally_ids]
        candidate = random.choice(remaining)
        
        # Calculate Heuristics
        # 1. Damage Type Rule
        dmg_types = [id_to_stats[h]['Damage_Type'] for h in ally_ids]
        cand_dmg = id_to_stats[candidate]['Damage_Type']
        dmg_types.append(cand_dmg)
        phys = dmg_types.count(1)
        magic = dmg_types.count(2)
        bad_damage = (phys > 3) or (magic > 3)
        
        # 2. Hard Lane Constraint (Strict Check)
        # We need to check if the team ALREADY has the candidate's Primary Role
        # AND if they also already have the candidate's Secondary Role.
        
        # Count roles in current draft
        role_counts = {1:0, 2:0, 3:0, 4:0, 5:0}
        for h in ally_ids:
            p_lane = id_to_stats[h]['Primary_Lane']
            role_counts[p_lane] = role_counts.get(p_lane, 0) + 1
            
        cand_primary = id_to_stats[candidate]['Primary_Lane']
        cand_secondary = id_to_stats[candidate].get('Secondary_Lane', 0)
        
        lane_clash = False
        
        # Logic: 
        # If Primary is Taken (>0), check Secondary.
        # If Secondary is 0 (None) OR Secondary is also Taken, then it's a CLASH.
        
        if role_counts.get(cand_primary, 0) > 0:
            # Primary is full. Can we Flex?
            if cand_secondary == 0:
                lane_clash = True # No secondary option
            elif role_counts.get(cand_secondary, 0) > 0:
                lane_clash = True # Secondary also full
            else:
                # Secondary is Open -> Valid Flex
                pass 
        
        # Note: This ignores 'Flex_Pick_Score' variable for the *Rule*, 
        # but allows the Model to learn Flex_Pick_Score from the *Features*.
        # We just want to label "Bad Drafts" correctly.

        # Determine if this random pick IS bad or good
        is_bad = bad_damage or lane_clash
        
        if is_bad:
            if count_neg < target_neg:
                samples.append({
                    'enemy_ids': "[]", # Simplified for mock
                    'ally_ids': str(ally_ids),
                    'candidate_id': candidate,
                    'label': 0,
                    'is_real': 1.0
                })
                count_neg += 1
        else:
            if count_pos < target_pos:
                samples.append({
                    'enemy_ids': "[]",
                    'ally_ids': str(ally_ids),
                    'candidate_id': candidate,
                    'label': 1,
                    'is_real': 1.0
                })
                count_pos += 1
                
    return samples

def main():
    try:
        name_to_id, id_to_stats, id_to_meta, counters, synergies = load_data()
        
        real_data = parse_real_logs(name_to_id, id_to_meta)
        synth_data = generate_synthetic_samples(id_to_stats, counters, synergies)
        
        all_data = real_data + synth_data
        
        df = pd.DataFrame(all_data)
        df.to_csv(OUTPUT_PATH, index=False)
        
        print(f"Success! Saved {len(df)} training samples to {OUTPUT_PATH}")
        print(f"Real Samples: {len(real_data)}")
        print(f"Synthetic Samples: {len(synth_data)}")
        
    except Exception as e:
        print(f"Failed to generate data: {e}")

if __name__ == "__main__":
    main()
