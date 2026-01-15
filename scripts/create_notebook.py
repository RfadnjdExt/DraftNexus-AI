import json

cells = []

# Cell 1: Imports & Style
source1 = [
    "import pandas as pd\n",
    "import matplotlib.pyplot as plt\n",
    "import seaborn as sns\n",
    "import os\\n",
    "\n",
    "%matplotlib inline\n",
    "\n",
    "# Set \"Official\" Style\n",
    "sns.set_theme(style=\"darkgrid\", context=\"talk\")\n",
    "plt.rcParams['font.family'] = 'sans-serif'\n",
    "plt.rcParams['figure.facecolor'] = '#f0f0f0'\n",
    "\n",
    "DATA_DIR = '../data'\\n",
    "BASE_STATS_PATH = os.path.join(DATA_DIR, 'hero_base_stats.csv')\n",
    "META_STATS_PATH = os.path.join(DATA_DIR, 'hero_meta_performance.csv')"
]
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": source1
})

# Cell 2: Loader
source2 = [
    "def load_and_merge_data():\n",
    "    if not os.path.exists(BASE_STATS_PATH) or not os.path.exists(META_STATS_PATH):\n",
    "        print(\"Error: Data files not found.\")\n",
    "        return None\n",
    "\n",
    "    df_base = pd.read_csv(BASE_STATS_PATH)\n",
    "    df_meta = pd.read_csv(META_STATS_PATH)\n",
    "    df = pd.merge(df_base, df_meta, on='Hero_ID')\n",
    "    \n",
    "    lane_map = {1: 'Exp Lane', 2: 'Mid Lane', 3: 'Roamer', 4: 'Jungler', 5: 'Gold Lane'}\n",
    "    df['Lane_Name'] = df['Primary_Lane'].map(lane_map)\n",
    "    return df\n",
    "\n",
    "df = load_and_merge_data()\n",
    "print(f\"Loaded {len(df)} heroes for analytics.\")"
]
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": source2
})

# Cell 3: Professional Meta Matrix with Quadrants
source3 = [
    "def plot_official_meta_matrix(df):\n",
    "    plt.figure(figsize=(14, 10), facecolor='white')\n",
    "    \n",
    "    # Metrics\n",
    "    mean_pr = df['Pick_Rate'].mean()\n",
    "    mean_wr = 0.50 # Baseline 50%\n",
    "    \n",
    "    # Custom Role Colors - Esports Style\n",
    "    role_colors = {\n",
    "        'Exp Lane': '#e74c3c',   # Red (Fighter)\n",
    "        'Mid Lane': '#9b59b6',   # Purple (Mage)\n",
    "        'Roamer':   '#f1c40f',   # Yellow (Support/Tank)\n",
    "        'Jungler':  '#2ecc71',   # Green (Assassin)\n",
    "        'Gold Lane':'#3498db'    # Blue (Marksman)\n",
    "    }\n",
    "    \n",
    "    # Scatter Plot\n",
    "    sns.scatterplot(\n",
    "        data=df, \n",
    "        x='Pick_Rate', \n",
    "        y='Base_Win_Rate', \n",
    "        hue='Lane_Name', \n",
    "        style='Lane_Name', \n",
    "        palette=role_colors,\n",
    "        s=150, \n",
    "        alpha=0.9,\n",
    "        edgecolor='black',\n",
    "        linewidth=1\n",
    "    )\n",
    "    \n",
    "    # --- Quadrants ---\n",
    "    plt.axhline(mean_wr, color='black', linestyle='--', alpha=0.3)\n",
    "    plt.axvline(mean_pr, color='black', linestyle='--', alpha=0.3)\n",
    "    \n",
    "    # Quadrant Labels\n",
    "    # Top Right: High Win, High Pick\n",
    "    plt.text(df['Pick_Rate'].max()*0.9, 0.58, \"S-TIER\\n(Meta / OP)\", \n",
    "             fontsize=14, color='green', fontweight='bold', ha='right')\n",
    "             \n",
    "    # Top Left: High Win, Low Pick\n",
    "    plt.text(0, 0.58, \"A-TIER\\n(Hidden Gems)\", \n",
    "             fontsize=14, color='orange', fontweight='bold', ha='left')\n",
    "\n",
    "    # Bottom Right: Low Win, High Pick\n",
    "    plt.text(df['Pick_Rate'].max()*0.9, 0.42, \"POPULAR BUT RISK\\n(Comfort Picks)\", \n",
    "             fontsize=12, color='gray', ha='right')\n",
    "\n",
    "    # Bottom Left: Low Win, Low Pick\n",
    "    plt.text(0, 0.42, \"OFF-META\\n(Underpowered)\", \n",
    "             fontsize=12, color='red', ha='left')\n",
    "\n",
    "    # --- Smart Annotations ---\n",
    "    # Label only significant heroes to keep it clean\n",
    "    for line in range(0, df.shape[0]):\n",
    "        row = df.iloc[line]\n",
    "        # Condition: Top 10% Pick Rate OR >54% WR OR <44% WR\n",
    "        if row['Pick_Rate'] > df['Pick_Rate'].quantile(0.90) or \\\n",
    "           row['Base_Win_Rate'] > 0.55 or \\\n",
    "           row['Base_Win_Rate'] < 0.45:\n",
    "            \n",
    "            plt.text(\n",
    "                row['Pick_Rate']+0.002, \n",
    "                row['Base_Win_Rate']+0.002, \n",
    "                row['Hero_Name'], \n",
    "                horizontalalignment='left', \n",
    "                size='medium', \n",
    "                color='#333333',\n",
    "                weight='semibold'\n",
    "            )\n",
    "\n",
    "    plt.title('Official Meta Matrix: Hero Performance Analysis', fontsize=20, pad=20, weight='bold')\n",
    "    plt.xlabel('Popularity (Pick Rate)', fontsize=14, labelpad=10)\n",
    "    plt.ylabel('Efficiency (Win Rate)', fontsize=14, labelpad=10)\n",
    "    plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', title='Role / Lane', frameon=False)\n",
    "    \n",
    "    sns.despine()\n",
    "    plt.tight_layout()\n",
    "    plt.savefig('./analysis_plots/official_meta_matrix.png', dpi=300) # High Res Save\n",
    "    plt.show()\n",
    "\n",
    "plot_official_meta_matrix(df)"
]
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": source3
})

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "codemirror_mode": {
                "name": "ipython",
                "version": 3
            },
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.8"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

with open(os.path.join(os.path.dirname(__file__), '../notebooks/visualize_analytics.ipynb'), 'w') as f:
    json.dump(notebook, f, indent=1)
    
print("Enhanced Professional Notebook created.")
