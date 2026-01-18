import pandas as pd
import os

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), '../data')
LOGS_PATH = os.path.join(DATA_DIR, 'match_logs_real.csv')

def parse_duration(dur_str):
    try:
        if ':' in str(dur_str):
            m, s = dur_str.split(':')
            return int(m) * 60 + int(s)
        return 900 # Default 15m
    except:
        return 900

def get_top_picks(df, top_n=5):
    picks = []
    for col in ['Winning_Team', 'Losing_Team']:
        for val in df[col].dropna():
            # Format: Hero:Role|Hero:Role...
            if '|' in str(val):
                for p in val.split('|'):
                    hero = p.split(':')[0]
                    picks.append(hero)
    
    return pd.Series(picks).value_counts().head(top_n)

def compare_stages():
    if not os.path.exists(LOGS_PATH):
        print("No match logs found.")
        return

    df = pd.read_csv(LOGS_PATH)
    
    # Ensure Day is string for consistent comparison
    df['Day'] = df['Day'].astype(str)
    
    # Filter Sets
    # Swiss Day 7
    subset_swiss = df[(df['Stage'] == 'Swiss Stage') & (df['Day'] == '7')]
    
    # Knockout Day 1
    subset_ko = df[(df['Stage'] == 'Knockout Stage') & (df['Day'] == '1')]
    
    print("-" * 50)
    print("COMPARISON: Swiss Stage Day 7 vs Knockout Stage Day 1")
    print("-" * 50)
    
    # 1. Basic Counts
    print(f"Games Played:")
    print(f"  Swiss (Day 7): {len(subset_swiss)}")
    print(f"  Knockout (Day 1): {len(subset_ko)}")
    print("")
    
    # 2. Duration
    dur_swiss = subset_swiss['Game_Duration'].apply(parse_duration)
    dur_ko = subset_ko['Game_Duration'].apply(parse_duration)
    
    avg_swiss = dur_swiss.mean() if not dur_swiss.empty else 0
    avg_ko = dur_ko.mean() if not dur_ko.empty else 0
    
    with open('comparison_report.md', 'w') as f:
        f.write("# Comparison Report\n")
        f.write("## Swiss Stage Day 7 vs Knockout Stage Day 1\n\n")
        
        f.write("### Games Played\n")
        f.write(f"- **Swiss (Day 7)**: {len(subset_swiss)}\n")
        f.write(f"- **Knockout (Day 1)**: {len(subset_ko)}\n\n")
        
        f.write("### Average Duration\n")
        f.write(f"- **Swiss (Day 7)**: {int(avg_swiss // 60)}m {int(avg_swiss % 60)}s\n")
        f.write(f"- **Knockout (Day 1)**: {int(avg_ko // 60)}m {int(avg_ko % 60)}s\n\n")
        
        f.write("### Top Picks Comparison\n")
        top_swiss = get_top_picks(subset_swiss)
        top_ko = get_top_picks(subset_ko)
        
        df_comp = pd.DataFrame({
            'Swiss (Day 7)': top_swiss,
            'Knockout (Day 1)': top_ko
        }).fillna(0).astype(int)
        
        df_comp = df_comp.sort_values('Knockout (Day 1)', ascending=False).head(10)
        f.write(df_comp.to_markdown())
        
    print("Report saved to comparison_report.md")

if __name__ == "__main__":
    compare_stages()
