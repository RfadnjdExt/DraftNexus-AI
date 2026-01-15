import pandas as pd
import os

# Define paths
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data'))
BASE_STATS_PATH = os.path.join(DATA_DIR, 'hero_base_stats.csv')
META_PERF_PATH = os.path.join(DATA_DIR, 'hero_meta_performance.csv')

def load_data():
    """Loads and merges the hero datasets."""
    if not os.path.exists(BASE_STATS_PATH) or not os.path.exists(META_PERF_PATH):
        print("Error: Data files not found.")
        return None

    df_base = pd.read_csv(BASE_STATS_PATH)
    df_meta = pd.read_csv(META_PERF_PATH)

    # Merge on Hero_ID
    # keeping all base columns and adding meta info
    df_merged = pd.merge(df_base, df_meta, on='Hero_ID', how='inner')

    print(f"Data Loaded Successfully using {BASE_STATS_PATH} and {META_PERF_PATH}")
    print(f"Total Heroes: {len(df_merged)}")
    return df_merged

def perform_eda(df):
    """Performs basic Exploratory Data Analysis"""
    print("\n--- Dataset Info ---")
    print(df.info())

    print("\n--- Descriptive Statistics (Numerical) ---")
    print(df.describe())

    print("\n--- Missing Values Strategy ---")
    missing = df.isnull().sum()
    print(missing[missing > 0])

    print("\n--- Strategic Metrics Analysis ---")

    # Check Difficulty Distribution
    print("\nDifficulty Level Distribution:")
    print(df['Difficulty'].describe())

    # Check Flex Pick Score Distribution
    print("\nFlex Pick Score Counts:")
    print(df['Flex_Pick_Score'].value_counts().sort_index())

    # Check Escape Reliability Distribution
    print("\nEscape Reliability Counts:")
    print(df['Escape_Reliability'].value_counts().sort_index())

    print("\n--- Correlation Check (Difficulty vs Win Rate) ---")
    correlation = df[['Difficulty', 'Base_Win_Rate', 'Ban_Rate']].corr()
    print(correlation)

    # Check Damage Type Balance for Constraints
    print("\n--- Damage Type Distribution (For Constraint Rules) ---")
    print(df['Damage_Type'].value_counts())
    # 1=Physical, 2=Magic, 3=True (usually mixed or specific)

if __name__ == "__main__":
    df = load_data()
    if df is not None:
        perform_eda(df)
