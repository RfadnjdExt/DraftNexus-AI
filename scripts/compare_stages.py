import pandas as pd
import os

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), '../data')
LOGS_PATH = os.path.join(DATA_DIR, 'match_logs_real.csv')
OUTPUT_FILE = 'stage_comparison_report.md'

def parse_duration(dur_str):
    try:
        if ':' in str(dur_str):
            m, s = dur_str.split(':')
            return int(m) * 60 + int(s)
        return 0
    except:
        return 0

def format_duration(seconds):
    return f"{int(seconds // 60)}m {int(seconds % 60)}s"

def get_stats_for_stage(df_stage):
    if df_stage.empty:
        return {"games": 0, "avg_dur": 0, "top_picks": []}
    
    # 1. Games
    n_games = len(df_stage)
    
    # 2. Duration
    durations = df_stage['Game_Duration'].apply(parse_duration)
    avg_dur = durations.mean()
    
    # 3. Picks & Win Rates
    pick_counts = {}
    wins = {}
    
    for _, row in df_stage.iterrows():
        # Winning Team
        winner = row['Winning_Team']
        if isinstance(winner, str):
            for p in winner.split('|'):
                if ':' in p:
                    h = p.split(':')[0]
                    pick_counts[h] = pick_counts.get(h, 0) + 1
                    wins[h] = wins.get(h, 0) + 1
                    
        # Losing Team
        loser = row['Losing_Team']
        if isinstance(loser, str):
            for p in loser.split('|'):
                if ':' in p:
                    h = p.split(':')[0]
                    pick_counts[h] = pick_counts.get(h, 0) + 1
    
    # Top Picks
    sorted_picks = sorted(pick_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    top_picks_fmt = [f"{h} ({c})" for h, c in sorted_picks]
    
    # Top Win Rate (min 3 games)
    hero_stats = []
    for h, count in pick_counts.items():
        if count >= 3:
            w = wins.get(h, 0)
            wr = (w / count) * 100
            hero_stats.append((h, wr, count))
            
    sorted_wr = sorted(hero_stats, key=lambda x: x[1], reverse=True)[:3]
    top_wr_fmt = [f"{h} ({wr:.1f}%)" for h, wr, c in sorted_wr]

    return {
        "games": n_games,
        "avg_dur": avg_dur,
        "top_picks": top_picks_fmt,
        "top_wr": top_wr_fmt
    }

def main():
    if not os.path.exists(LOGS_PATH):
        print("Log file not found.")
        return

    # Read with string Day to avoid issues
    df = pd.read_csv(LOGS_PATH, dtype={'Day': str})
    
    # Identify Stages
    # Order: Swiss -> Knockout -> Grand Finals (Custom sort)
    stages = ['Swiss Stage', 'Knockout Stage', 'Grand Finals']
    
    # Generate Report
    with open(OUTPUT_FILE, 'w') as f:
        f.write("# Tournament Stage Comparison\n\n")
        f.write("Comparing performance metrics across all tournament stages.\n\n")
        
        # Summary Table
        f.write("## Overview\n")
        f.write("| Stage | Games | Avg Duration | Top Picks | Highest Win Rate (Min 3) |\n")
        f.write("|---|---|---|---|---|\n")
        
        for stage in stages:
            stage_data = df[df['Stage'] == stage]
            stats = get_stats_for_stage(stage_data)
            
            dur_str = format_duration(stats['avg_dur'])
            picks_str = ", ".join(stats['top_picks'])
            wr_str = ", ".join(stats['top_wr'])
            
            f.write(f"| **{stage}** | {stats['games']} | {dur_str} | {picks_str} | {wr_str} |\n")
            
        f.write("\n")
        f.write("## Detailed Notes\n")
        f.write("- **Swiss Stage**: Initial qualifier rounds.\n")
        f.write("- **Knockout Stage**: Elimination rounds.\n")
        f.write("- **Grand Finals**: Final championship match.\n")

    print(f"Report generated: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
