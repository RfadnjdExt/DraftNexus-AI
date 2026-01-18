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
            strong_json = json.loads(row['Strong_Against_JSON'])
            weak_json = json.loads(row['Weak_Against_JSON'])
            
            # Key Fix: Extract 'heroid' from the list of dicts
            counters[row['Hero_ID']] = {
                'strong': [x['heroid'] for x in strong_json if 'heroid' in x],
                'weak': [x['heroid'] for x in weak_json if 'heroid' in x]
            }

    if os.path.exists(COMPAT_PATH):
        df_comp = pd.read_csv(COMPAT_PATH)
        for _, row in df_comp.iterrows():
            best_json = json.loads(row['Best_Teammate_JSON'])
            worst_json = json.loads(row['Worst_Teammate_JSON'])
            
            # Key Fix: Extract 'heroid' from the list of dicts
            synergies[row['Hero_ID']] = {
                'best': [x['heroid'] for x in best_json if 'heroid' in x],
                'worst': [x['heroid'] for x in worst_json if 'heroid' in x]
            }

    return name_to_id, id_to_stats, id_to_meta, counters, synergies

def parse_real_logs(name_to_id, id_to_meta, df_override=None):
    """Parses user provided match logs"""
    real_samples = []

    if df_override is not None:
        df_real = df_override
    elif not os.path.exists(REAL_LOGS_PATH):
        print("No real logs found, skipping real data ingestion.")
        return []
    else:
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

def generate_synthetic_samples(id_to_stats, counters, synergies, n_samples=20000):
    """Generates mock data with FORCED strategic scenarios"""
    
    hero_ids = list(id_to_stats.keys())
    print(f"Generating {n_samples} synthetic samples with STRATEGIC BIAS...")

    samples = []
    
    # helper
    def add_sample(ally_ids, enemy_ids, candidate, label, weight=1.0):
        # Add some noise/random fillers to empty slots to simulate real games
        # But allow 20% to be pure (just the interaction)
        if random.random() > 0.2:
            n_extra_allies = random.randint(0, 4 - len(ally_ids))
            n_extra_enemies = random.randint(0, 5 - len(enemy_ids))
            
            # fill allies
            possible_allies = [h for h in hero_ids if h not in ally_ids and h not in enemy_ids and h != candidate]
            if len(possible_allies) > n_extra_allies:
                ally_ids = ally_ids + random.sample(possible_allies, n_extra_allies)
                
            # fill enemies
            possible_enemies = [h for h in hero_ids if h not in ally_ids and h not in enemy_ids and h != candidate]
            if len(possible_enemies) > n_extra_enemies:
                enemy_ids = enemy_ids + random.sample(possible_enemies, n_extra_enemies)

        samples.append({
            'enemy_ids': str(enemy_ids),
            'ally_ids': str(ally_ids),
            'candidate_id': candidate,
            'label': label,
            'is_real': weight
        })

    # 1. STRUCTURED GENERATION: Force Model to learn Counters
    print("Injecting Counter/Synergy Knowledge...")
    for hero, rels in counters.items():
        # Hero STRONG vs Enemy
        for enemy in rels.get('strong', []):
            # Good Pick
            for _ in range(3): # repeat to emphasize
                add_sample([], [enemy], hero, 1, weight=5.0)
            
            # Bad Pick (Reverse: Enemy picks Hero, we pick Weak victim)
            # If Hero is Strong vs Enemy, then Enemy is Weak vs Hero
            for _ in range(3):
                add_sample([], [hero], enemy, 0, weight=5.0)
                
        # Hero WEAK vs Enemy
        for enemy in rels.get('weak', []):
            # Bad Pick
            for _ in range(3):
                add_sample([], [enemy], hero, 0, weight=5.0)

    for hero, rels in synergies.items():
        # Best Teammate
        for mate in rels.get('best', []):
            # Good Pick
            for _ in range(3):
                add_sample([mate], [], hero, 1, weight=4.0)

    print(f"Injected {len(samples)} structured samples.")

    # 2. RANDOM GENERATION (To fill remaining volume and learn general stats)
    
    attempts = 0
    while len(samples) < n_samples:
        attempts += 1
        
        n_allies = random.randint(1, 4)
        n_enemies = random.randint(1, 5)
        
        draft_pool = random.sample(hero_ids, n_allies + n_enemies + 1)
        ally_ids = draft_pool[:n_allies]
        enemy_ids = draft_pool[n_allies : n_allies + n_enemies]
        candidate = draft_pool[-1]
        
        score = 0
        
        # Scoring Logic (Refined)
        cand_counters = counters.get(candidate, {'strong':[], 'weak':[]})
        for e in enemy_ids:
            if e in cand_counters.get('strong', []): score += 6 # Strong Counter Bonus
            if e in cand_counters.get('weak', []): score -= 6   # Hard Countered Penalty
            
        cand_syn = synergies.get(candidate, {'best':[], 'worst':[]})
        for a in ally_ids:
            if a in cand_syn.get('best', []): score += 3
            if a in cand_syn.get('worst', []): score -= 3
            
        # Role Penalty
        role_counts = {1:0, 2:0, 3:0, 4:0, 5:0}
        dtype_counts = {1:0, 2:0} # 1:Physical, 2:Magic
        
        for h in ally_ids:
            stats = id_to_stats[h]
            p = stats['Primary_Lane']
            d = stats.get('Damage_Type', 1) 
            role_counts[p] = role_counts.get(p, 0) + 1
            if d in dtype_counts: dtype_counts[d] += 1
        
        # Lane Constraint
        c_stats = id_to_stats[candidate]
        c_p = c_stats['Primary_Lane']
        c_d = c_stats.get('Damage_Type', 1)
        
        # If lane is taken and hero is not flexible (Sec Lane == 0) -> Penalize
        if role_counts.get(c_p, 0) > 0 and c_stats.get('Secondary_Lane', 0) == 0:
            score -= 10
            
        # Damage Type Balance (Don't let team be full Physical or full Magic)
        if c_d in dtype_counts and dtype_counts[c_d] >= 3:
            score -= 4 # Soft penalty for unbalance
            
        # Label Rules
        # Stricter threshold for "Good Pick" to ensure high quality
        if score >= 4: add_sample(ally_ids, enemy_ids, candidate, 1, 3.0)
        elif score <= -4: add_sample(ally_ids, enemy_ids, candidate, 0, 3.0)
        
        # Soft label for "noise" logic (occasionally add neutral samples if we need volume, but skip for now to keep signal clear)

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

def generate_data(df_logs_override=None):
    """External API for data generation"""
    name_to_id, id_to_stats, id_to_meta, counters, synergies = load_data()
    real_data = parse_real_logs(name_to_id, id_to_meta, df_override=df_logs_override)
    synth_data = generate_synthetic_samples(id_to_stats, counters, synergies, n_samples=5000) # Lower sample count for speed in comparison
    all_data = real_data + synth_data
    return pd.DataFrame(all_data)

if __name__ == "__main__":
    main()
