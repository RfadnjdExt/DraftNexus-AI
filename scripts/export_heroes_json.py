import pandas as pd
import os
import json

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, '../data')
ASSETS_DIR = os.path.join(SCRIPT_DIR, '../android/app/src/main/assets')

STATS_PATH = os.path.join(DATA_DIR, 'hero_base_stats.csv')
JSON_PATH = os.path.join(ASSETS_DIR, 'heroes.json')

def export_json():
    if not os.path.exists(STATS_PATH):
        print("Stats file not found")
        return

    df = pd.read_csv(STATS_PATH)
    
    # Convert to list of dicts
    # We want strict types for Kotlin parsing
    # --- FILTERING LOGIC START ---
    MATCH_LOGS_PATH = os.path.join(DATA_DIR, 'match_logs_real.csv')
    used_hero_ids = set()
    
    # 1. Build Name -> ID Map from DF (which loaded hero_base_stats.csv)
    name_to_id = {}
    for _, row in df.iterrows():
        name_to_id[str(row['Hero_Name'])] = int(row['Hero_ID'])
        
    if os.path.exists(MATCH_LOGS_PATH):
        print(f"Filtering heroes based on {MATCH_LOGS_PATH}...")
        try:
            logs_df = pd.read_csv(MATCH_LOGS_PATH)
            
            def parse_team_str(team_str):
                # Format: "Hero1:Role|Hero2:Role|..."
                if not isinstance(team_str, str): return []
                parts = team_str.split('|')
                ids = []
                for p in parts:
                    # p is "HeroName:Role"
                    if ':' in p:
                        h_name = p.split(':')[0].strip()
                        if h_name in name_to_id:
                            ids.append(name_to_id[h_name])
                return ids

            # Helper for simple columns (if any)
            # match_logs_real.csv has 'Winning_Team' and 'Losing_Team' columns as strings
            
            for col in ['Winning_Team', 'Losing_Team']:
                if col in logs_df.columns:
                    for val in logs_df[col]:
                        used_hero_ids.update(parse_team_str(val))
                 
            print(f"Found {len(used_hero_ids)} unique used heroes in REAL LOGS.")
        except Exception as e:
            print(f"Error reading match logs: {e}")
            used_hero_ids = set() # Empty means 'don't filter' usually, but here strict?
            # User said "only show that been used". If error, maybe show all (provisional) or show none?
            # Let's fallback to Show All if error to avoid empty app.
            
    else:
        print("Match logs not found. Exporting ALL heroes.")

    # --- FILTERING LOGIC END ---

    heroes = []
    
    for _, row in df.iterrows():
        h_id = int(row['Hero_ID'])
        
        # Check if used in real logs
        in_real_logs = (h_id in used_hero_ids) if used_hero_ids else True
        
        hero = {
            "id": h_id,
            "name": str(row['Hero_Name']),
            "primaryLane": int(row['Primary_Lane']),
            "secondaryLane": int(row['Secondary_Lane']),
            "iconUrl": str(row['Icon_URL']) if pd.notna(row['Icon_URL']) else "",
            "inRealLogs": in_real_logs,
            # Stats for Inference
            "stats": [
                float(row['Primary_Lane']),
                float(row['Damage_Type']),
                float(row['Hard_CC_Count']),
                float(row['Flex_Pick_Score']),
                float(row['Escape_Reliability']),
                float(row['Difficulty']),
                float(row['Economy_Dependency']),
                # These might be missing if we don't merge META stats
                # For now let's just use base stats + placeholders for power
                # In real implementation we should merge meta performance too
                0.0, # Early Power
                0.0, # Mid Power
                0.0  # Late Power
            ]
        }
        heroes.append(hero)
        
    # Ensure Assets dir exists
    os.makedirs(ASSETS_DIR, exist_ok=True)
    
    with open(JSON_PATH, 'w') as f:
        json.dump(heroes, f, indent=2)
        
    print(f"Exported {len(heroes)} heroes to {JSON_PATH}")

if __name__ == "__main__":
    export_json()
