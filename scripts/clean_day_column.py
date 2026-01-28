import pandas as pd
import os

LOGS_PATH = os.path.join('data', 'match_logs_real.csv')

if os.path.exists(LOGS_PATH):
    # Read all as string to avoid auto-conversion
    df = pd.read_csv(LOGS_PATH, dtype={'Day': str})
    
    # Function to clean day
    def clean_day(val):
        if pd.isna(val) or val == 'nan':
            return ""
        val = str(val).strip()
        if val.endswith('.0'):
            return val[:-2]
        return val

    df['Day'] = df['Day'].apply(clean_day)
    
    # Save back
    df.to_csv(LOGS_PATH, index=False)
    print("Cleaned Day column in match_logs_real.csv")
else:
    print("File not found")
