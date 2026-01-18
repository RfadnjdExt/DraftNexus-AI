import pandas as pd
import os
import sys
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
    # A. Baseline: Swiss Stage Only
    df_swiss = df_full[df_full['Stage'] == 'Swiss Stage']
    print(f"Subset Swiss: {len(df_swiss)} matches")
    
    # B. Comparison: Swiss + Knockout Day 1
    # Condition: Swiss Stage OR (Knockout AND Day 1)
    # Note: Currently Day 1 is the only day in Knockout, so it's effectively everything, 
    # but let's be explicit to match the request "Day 1 vs Swiss".
    mask_ko_day1 = (df_full['Stage'] == 'Knockout Stage') & (df_full['Day'] == '1')
    df_ko = pd.concat([df_swiss, df_full[mask_ko_day1]])
    print(f"Subset Swiss + KO Day 1: {len(df_ko)} matches")
    
    # 3. Train Baseline
    print("\n--- Training Baseline (Swiss Only) ---")
    training_data_swiss = generate_data(df_logs_override=df_swiss)
    res_swiss = train_model(df_train_override=training_data_swiss, save_model=False)
    
    # 4. Train Comparison
    print("\n--- Training Comparison (Swiss + KO Day 1) ---")
    training_data_ko = generate_data(df_logs_override=df_ko)
    res_ko = train_model(df_train_override=training_data_ko, save_model=False)
    
    # 5. Generate Report
    print("\nGenerating Report...")
    with open('model_training_comparison_report.md', 'w') as f:
        f.write("# Model Training Comparison Report\n")
        f.write("## Scenario: Swiss Stage vs Swiss + Knockout (Day 1)\n\n")
        
        # A. Accuracy
        f.write("### Accuracy\n")
        f.write(f"- **Baseline (Swiss Only)**: {res_swiss['accuracy']:.4f}\n")
        f.write(f"- **With Knockout Day 1**: {res_ko['accuracy']:.4f}\n")
        diff = res_ko['accuracy'] - res_swiss['accuracy']
        f.write(f"- **Difference**: {diff:+.4f}\n\n")
        
        # B. Feature Importance (Stats)
        f.write("### Strategic Feature Importance Change\n")
        f.write("Values indicate how much the model relies on specific hero attributes.\n\n")
        
        stat_names = res_swiss['stat_feature_names']
        imp_swiss = res_swiss['feature_importances'][-len(stat_names):]
        imp_ko = res_ko['feature_importances'][-len(stat_names):]
        
        df_imp = pd.DataFrame({
            'Feature': stat_names,
            'Importance (Swiss)': imp_swiss,
            'Importance (Swiss+KO)': imp_ko
        })
        df_imp['Change'] = df_imp['Importance (Swiss+KO)'] - df_imp['Importance (Swiss)']
        df_imp = df_imp.sort_values('Importance (Swiss+KO)', ascending=False)
        
        f.write(df_imp.to_markdown(index=False, floatfmt=".4f"))
        f.write("\n\n")
        
        f.write("### Interpretation\n")
        f.write("- **Accuracy**: Higher is better. A significant drop might indicate the new data conflicts with old patterns (meta shift).\n")
        f.write("- **Feature Importance**: Changes here show if the model is prioritizing different aspects (e.g., Early Power vs Late Power) due to the new Knockout games.\n")

    print("Success! Report saved to 'model_training_comparison_report.md'")

if __name__ == "__main__":
    main()
