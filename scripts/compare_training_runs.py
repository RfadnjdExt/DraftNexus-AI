import pandas as pd
import os
import sys
# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.generate_training_data_new import generate_data
from scripts.train_draft_model import train_model

def main():
    print("Starting Model Comparison...")
    
    # 1. Load Real Logs
    logs_path = os.path.join('data', 'match_logs_real.csv')
    if not os.path.exists(logs_path):
        print("No match logs found.")
        return
        
    df_full = pd.read_csv(logs_path)
    
    # ensure string types for filtering
    df_full['Stage'] = df_full['Stage'].astype(str)
    df_full['Day'] = df_full['Day'].astype(str)
    
    # 2. Prepare Data Subsets
    # A. Baseline: Swiss + Knockout (Pre-Grand Finals)
    df_baseline = df_full[df_full['Stage'].isin(['Swiss Stage', 'Knockout Stage'])]
    print(f"Subset Baseline (Swiss + KO): {len(df_baseline)} matches")
    
    # B. Comparison: All Stages (Including Grand Finals)
    df_all = df_full
    print(f"Subset All (Swiss + KO + GF): {len(df_all)} matches")
    
    # 3. Train Baseline
    print("\n--- Training Baseline (Swiss + KO) ---")
    training_data_base = generate_data(df_logs_override=df_baseline)
    res_base = train_model(df_train_override=training_data_base, save_model=False)
    
    # 4. Train Comparison
    print("\n--- Training Comparison (All Stages) ---")
    training_data_all = generate_data(df_logs_override=df_all)
    res_all = train_model(df_train_override=training_data_all, save_model=False)
    
    # 5. Generate Report
    print("\nGenerating Report...")
    with open('model_training_comparison_report.md', 'w') as f:
        f.write("# Model Training Comparison Report\n")
        f.write("## Scenario: Swiss+Knockout vs Including Grand Finals\n\n")
        
        # A. Accuracy

        f.write("### Accuracy\n")
        f.write(f"- **Baseline (Swiss + Knockout)**: {res_base['accuracy']:.4f}\n")
        f.write(f"- **With Grand Finals**: {res_all['accuracy']:.4f}\n")
        diff = res_all['accuracy'] - res_base['accuracy']
        f.write(f"- **Difference**: {diff:+.4f}\n\n")
        
        # B. Feature Importance (Stats)
        f.write("### Strategic Feature Importance Change\n")
        f.write("Values indicate how much the model relies on specific hero attributes.\n\n")
        
        stat_names = res_base['stat_feature_names']
        imp_base = res_base['feature_importances'][-len(stat_names):]
        imp_all = res_all['feature_importances'][-len(stat_names):]
        
        df_imp = pd.DataFrame({
            'Feature': stat_names,
            'Importance (Baseline)': imp_base,
            'Importance (With GF)': imp_all
        })
        df_imp['Change'] = df_imp['Importance (With GF)'] - df_imp['Importance (Baseline)']
        df_imp = df_imp.sort_values('Importance (With GF)', ascending=False)
        
        f.write(df_imp.to_markdown(index=False, floatfmt=".4f"))
        f.write("\n\n")
        
        f.write("### Interpretation\n")
        f.write("- **Accuracy**: Higher is better. A significant drop might indicate the new data conflicts with old patterns (meta shift).\n")
        f.write("- **Feature Importance**: Changes here show if the model is prioritizing different aspects (e.g., Early Power vs Late Power) due to the new Knockout games.\n")

    print("Success! Report saved to 'model_training_comparison_report.md'")

if __name__ == "__main__":
    main()
