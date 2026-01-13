import pandas as pd
import numpy as np
import os
import ast
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib

# Paths
DATA_DIR = './data'
TRAIN_DATA_PATH = os.path.join(DATA_DIR, 'training_data_hybrid.csv')
BASE_STATS_PATH = os.path.join(DATA_DIR, 'hero_base_stats.csv')
META_STATS_PATH = os.path.join(DATA_DIR, 'hero_meta_performance.csv')
MODEL_OUTPUT_PATH = os.path.join(DATA_DIR, 'draft_model_rf.pkl')

def load_data():
    if not os.path.exists(TRAIN_DATA_PATH) or not os.path.exists(BASE_STATS_PATH) or not os.path.exists(META_STATS_PATH):
        raise FileNotFoundError("Data files missing.")

    df_train = pd.read_csv(TRAIN_DATA_PATH)
    df_base = pd.read_csv(BASE_STATS_PATH)
    df_meta = pd.read_csv(META_STATS_PATH)

    # Merge Base + Meta
    df_stats = pd.merge(df_base, df_meta[['Hero_ID', 'Early_Power', 'Mid_Power', 'Late_Power']], on='Hero_ID', how='left')

    return df_train, df_stats

def preprocess_features(df_train, df_stats):
    """
    Converts raw draft logs into ML Feature Vectors.
    Feature Vector = [Ally_OneHot (131)] + [Enemy_OneHot (131)] + [Candidate_Stats]
    """
    print("Preprocessing Features...")

    # map Hero ID to Index (0-130) for OneHot
    hero_ids = sorted(df_stats['Hero_ID'].unique())
    id_to_idx = {hid: i for i, hid in enumerate(hero_ids)}
    n_heroes = len(hero_ids)

    # Prepare Stats Map for Candidate
    # We want to give the model context about the candidate (is it hard? is it Flex?)
    # Columns to include:
    stat_cols = ['Primary_Lane', 'Damage_Type', 'Hard_CC_Count', 'Flex_Pick_Score', 'Escape_Reliability',
                 'Difficulty', 'Economy_Dependency', 'Early_Power', 'Mid_Power', 'Late_Power']
    stats_map = df_stats.set_index('Hero_ID')[stat_cols].to_dict('index')

    X = []
    y = df_train['label'].values

    # 'is_real' column now holds the actual weight value (e.g. 1.0 for mock, 3.0 or 5.0 for real)
    # We just cast it to float
    weights = df_train['is_real'].astype(float).values

    # Helper for Role Counts
    lane_map = df_stats.set_index('Hero_ID')['Primary_Lane'].to_dict()

    for _, row in df_train.iterrows():
        # Parse Lists
        try:
            ally_ids = ast.literal_eval(row['ally_ids'])
            enemy_ids = ast.literal_eval(row['enemy_ids'])
        except:
            # Fallback if string format is weird
            ally_ids = []
            enemy_ids = []

        cand_id = row['candidate_id']

        # 1. Composition Vectors
        ally_vec = np.zeros(n_heroes)
        enemy_vec = np.zeros(n_heroes)
        
        # 2. Role Counts
        # Vector: [Exp_Count, Mid_Count, Roam_Count, Jungle_Count, Gold_Count]
        roles_vec = [0.0] * 5

        for h in ally_ids:
            if h in id_to_idx: ally_vec[id_to_idx[h]] = 1
            if h in lane_map:
                lane = lane_map[h]
                if 1 <= lane <= 5:
                     roles_vec[lane-1] += 1.0

        for h in enemy_ids:
            if h in id_to_idx: enemy_vec[id_to_idx[h]] = 1

        # 3. Candidate Stats Vector
        c_stats = stats_map.get(cand_id, {k:0 for k in stat_cols})

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

        # Combine
        full_vec = np.concatenate([ally_vec, enemy_vec, roles_vec, cand_vec])
        X.append(full_vec)

    return np.array(X), y, weights, stat_cols

def train_model():
    df_train, df_stats = load_data()

    X, y, sample_weights, stat_feature_names = preprocess_features(df_train, df_stats)

    print(f"Feature Vector Size: {X.shape[1]}")

    # Split
    X_train, X_test, y_train, y_test, w_train, w_test = train_test_split(X, y, sample_weights, test_size=0.2, random_state=42)

    print("Training Random Forest...")
    clf = RandomForestClassifier(n_estimators=100, max_depth=15, class_weight='balanced', random_state=42)
    clf.fit(X_train, y_train, sample_weight=w_train)

    # Evaluate
    print("\n--- Model Evaluation ---")
    y_pred = clf.predict(X_test)
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    # Feature Importance (Simplified)
    # The first 131 are Allies, next 131 Enemies, last 7 are Candidate Stats
    # Actually, we added roles_vec (5) in between
    importances = clf.feature_importances_

    # Check Stat Importances
    print("\n--- Candidate Stat Importance ---")
    stat_imps = importances[-len(stat_feature_names):] 
    for name, imp in zip(stat_feature_names, stat_imps):
        print(f"{name}: {imp:.4f}")

    # Save
    joblib.dump(clf, MODEL_OUTPUT_PATH)
    print(f"\nModel saved to {MODEL_OUTPUT_PATH}")

if __name__ == "__main__":
    train_model()
