import pandas as pd
import json
import os

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), '../data')
BASE_STATS_PATH = os.path.join(DATA_DIR, 'hero_base_stats.csv')
COMPAT_PATH = os.path.join(DATA_DIR, 'hero_compatibility_stats.csv')
COUNTER_PATH = os.path.join(DATA_DIR, 'hero_counter_stats.csv')

# Manual Overrides for icons not found in relationships
MANUAL_ICONS = {
    77: "https://akmweb.youngjoygame.com/web/svnres/img/mlbb/homepage/100_9fb1784545a48aef42241fc7a719c575.png"  # Badang (User Provided)
}

def load_icons_from_json(json_str):
    """Recursively search for 'head' key in JSON string."""
    try:
        data = json.loads(json_str)
        # We just need ONE icon per hero ID found in the relationships
        # But wait, the icons in compat/counter stats are for the RELATED heroes, 
        # NOT necessarily the main Hero_ID (though sometimes they might be).
        # Actually, let's look at the structure:
        # Hero_ID (Main) -> Best_Teammate_JSON (List of heroes)
        # Inside Best_Teammate_JSON: [{ "hero": { "data": { "head": "URL" } }, "heroid": XYZ }]
        # This gives us icons for the RELATED heroes (heroid XYZ).
        # We can build a map of Hero_ID -> Icon_URL by iterating through ALL relationships.
        
        icons = {}
        if isinstance(data, list):
            for item in data:
                try:
                    hid = item.get('heroid')
                    icon = item.get('hero', {}).get('data', {}).get('head')
                    if hid and icon:
                        icons[hid] = icon
                except:
                    pass
        return icons
    except:
        return {}

def main():
    if not os.path.exists(BASE_STATS_PATH):
        print("Base stats not found.")
        return

    icon_map = {}
    
    # 1. Scrape from Compatibility Stats
    if os.path.exists(COMPAT_PATH):
        print("Scanning Compatibility Stats for icons...")
        df_comp = pd.read_csv(COMPAT_PATH)
        for _, row in df_comp.iterrows():
            # Check Best Teammates
            icons = load_icons_from_json(row['Best_Teammate_JSON'])
            icon_map.update(icons)
            # Check Worst Teammates
            icons = load_icons_from_json(row['Worst_Teammate_JSON'])
            icon_map.update(icons)
            
    # 2. Scrape from Counter Stats
    if os.path.exists(COUNTER_PATH):
        print("Scanning Counter Stats for icons...")
        df_count = pd.read_csv(COUNTER_PATH)
        for _, row in df_count.iterrows():
            # Check Strong Against
            icons = load_icons_from_json(row['Strong_Against_JSON'])
            icon_map.update(icons)
            # Check Weak Against
            icons = load_icons_from_json(row['Weak_Against_JSON'])
            icon_map.update(icons)
    
    # Apply Manual Overrides
    icon_map.update(MANUAL_ICONS)
            
    print(f"Found {len(icon_map)} unique hero icons.")
    
    # 3. Update Base Stats
    df_base = pd.read_csv(BASE_STATS_PATH)
    
    # Check if we already have Icon_URL
    if 'Icon_URL' not in df_base.columns:
        df_base['Icon_URL'] = None
        
    # Map icons
    # Note: df_base['Hero_ID'] matches the keys in icon_map
    df_base['Icon_URL'] = df_base['Hero_ID'].map(icon_map)
    
    # Fill missing with a placeholder or keep None
    missing = df_base['Icon_URL'].isna().sum()
    print(f"Heroes missing icons: {missing}")
    
    # Save back
    df_base.to_csv(BASE_STATS_PATH, index=False)
    print(f"Updated {BASE_STATS_PATH} with Icon URLs.")

if __name__ == "__main__":
    main()
