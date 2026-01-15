import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Paths
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data'))
OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../analysis_plots'))
BASE_STATS_PATH = os.path.join(DATA_DIR, 'hero_base_stats.csv')
META_STATS_PATH = os.path.join(DATA_DIR, 'hero_meta_performance.csv')

def load_and_merge_data():
    if not os.path.exists(BASE_STATS_PATH) or not os.path.exists(META_STATS_PATH):
        print("Error: Data files not found.")
        return None

    df_base = pd.read_csv(BASE_STATS_PATH)
    df_meta = pd.read_csv(META_STATS_PATH)

    # Merge
    df = pd.merge(df_base, df_meta, on='Hero_ID')
    
    # Map Lane ID to Name
    lane_map = {1: 'Exp Lane', 2: 'Mid Lane', 3: 'Roamer', 4: 'Jungler', 5: 'Gold Lane'}
    df['Lane_Name'] = df['Primary_Lane'].map(lane_map)
    
    return df

def plot_meta_matrix(df):
    """Scatter Plot: Pick Rate vs Win Rate"""
    plt.figure(figsize=(12, 8))
    sns.set_style("whitegrid")
    
    # Scatter
    scatter = sns.scatterplot(
        data=df, 
        x='Pick_Rate', 
        y='Base_Win_Rate', 
        hue='Lane_Name', 
        style='Lane_Name', 
        s=100, 
        alpha=0.8
    )
    
    # Add Threshold Lines
    plt.axhline(0.50, color='gray', linestyle='--', alpha=0.5, label='50% Win Rate')
    plt.axvline(df['Pick_Rate'].mean(), color='gray', linestyle=':', alpha=0.5, label='Avg Pick Rate')

    # Annotate Top/Unique Heroes
    # Annotate extreme outliers
    for line in range(0, df.shape[0]):
        row = df.iloc[line]
        # Label if high pick rate OR high win rate
        if row['Pick_Rate'] > 0.4 or row['Base_Win_Rate'] > 0.54 or row['Base_Win_Rate'] < 0.44:
            plt.text(
                row['Pick_Rate']+0.005, 
                row['Base_Win_Rate'], 
                row['Hero_Name'], 
                horizontalalignment='left', 
                size='small', 
                color='black'
            )

    plt.title('Meta Matrix: Popularity vs Efficiency', fontsize=16)
    plt.xlabel('Pick Rate (Popularity)', fontsize=12)
    plt.ylabel('Win Rate (Efficiency)', fontsize=12)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    output_path = os.path.join(OUTPUT_DIR, '1_meta_matrix.png')
    plt.tight_layout()
    plt.savefig(output_path)
    print(f"Saved {output_path}")
    plt.close()

def plot_power_curve_by_role(df):
    """Grouped Bar Chart: Power Spikes by Role"""
    # Melt data for sns
    power_cols = ['Early_Power', 'Mid_Power', 'Late_Power']
    df_melt = df.melt(id_vars=['Lane_Name'], value_vars=power_cols, var_name='Game_Phase', value_name='Power_Score')
    
    plt.figure(figsize=(12, 6))
    
    sns.barplot(
        data=df_melt,
        x='Lane_Name',
        y='Power_Score',
        hue='Game_Phase',
        palette='viridis',
        ci=None  # Remove error bars for cleaner look
    )
    
    plt.title('Avg Hero Power Spikes by Role', fontsize=16)
    plt.ylabel('Power Score (0-1)', fontsize=12)
    plt.xlabel('Role', fontsize=12)
    plt.ylim(0.3, 0.8) # Zoom in on the relevant range
    plt.legend(title='Phase')
    
    output_path = os.path.join(OUTPUT_DIR, '2_power_curve.png')
    plt.tight_layout()
    plt.savefig(output_path)
    print(f"Saved {output_path}")
    plt.close()

def plot_difficulty_impact(df):
    """Reg Plot: Difficulty vs Win Rate"""
    plt.figure(figsize=(10, 6))
    
    sns.regplot(
        data=df,
        x='Difficulty',
        y='Base_Win_Rate',
        scatter_kws={'alpha':0.5},
        line_kws={'color':'red'}
    )
    
    plt.title('Does Difficulty Correlate to Wins?', fontsize=16)
    plt.xlabel('Difficulty (0-100)', fontsize=12)
    plt.ylabel('Win Rate', fontsize=12)
    
    # Correlation
    corr = df[['Difficulty', 'Base_Win_Rate']].corr().iloc[0,1]
    plt.text(10, 0.55, f'Correlation: {corr:.2f}', fontsize=12, color='red', bbox=dict(facecolor='white', alpha=0.8))
    
    output_path = os.path.join(OUTPUT_DIR, '3_difficulty_analysis.png')
    plt.tight_layout()
    plt.savefig(output_path)
    print(f"Saved {output_path}")
    plt.close()

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    df = load_and_merge_data()
    if df is not None:
        print(f"Loaded {len(df)} heroes.")
        plot_meta_matrix(df)
        plot_power_curve_by_role(df)
        plot_difficulty_impact(df)
        print("All plots generated successfully.")

if __name__ == "__main__":
    main()
