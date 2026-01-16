# DraftNexus AI 🛡️⚔️

DraftNexus-AI is a comprehensive tool for Mobile Legends: Bang Bang (MLBB) designed to assist in drafting, match logging, and analytics. It leverages machine learning to provide real-time hero recommendations based on team composition and enemy picks.

## ✨ Features

### 1. 🔮 Draft Recommender (Real-time)
*   **Role-Based Input**: Dedicated inputs for Allied roles (Exp, Jungle, Mid, Roam, Gold).
*   **Flex Enemy Input**: 5 flexible slots for Enemy picks.
*   **🚫 Ban Support**: 10 slots to exclude banned heroes from recommendations.
*   **Smart Suggestions**:
    *   **Best Pick per Role**: Displays the top recommended hero for each role.
    *   **Alternative Recommendations**: Automatically suggests alternatives if the best hero is already picked (marked as `(Alt)`).
    *   **Real Data Restriction**: Toggle to suggest *only* heroes present in your `match_logs_real.csv` history.

### 2. 📝 Match Logger
*   Log match details: Teams, Winner/Loser, Game Duration, and metadata.
*   Auto-Save to CSV (`data/match_logs_real.csv`) for future model training.
*   Match History view with icons and details.

### 3. 📊 Analytics & Training
*   **Seed Data**: `seed_heroes.js` to fetch latest hero stats and icons from API.
*   **Model Training**: `train_model.py` to retrain the RandomForest model using your custom match logs.
*   **Visualization**: Generate meta maps (`visualize_analytics.py`), power curves, and difficulty charts.

## 🚀 Getting Started

### Prerequisites
*   Python 3.10+
*   Node.js (optional, for fetching fresh API data)

### Installation
1.  Clone the repository:
    ```bash
    git clone https://github.com/RfadnjdExt/DraftNexus-AI.git
    cd DraftNexus-AI
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Usage
**Run the Main App:**
```bash
streamlit run scripts/data_entry_app.py
```

**Retrain Model (after adding new logs):**
```bash
# 1. Generate/Augment Training Data
python scripts/generate_training_data.py

# 2. Train Model
python scripts/train_model.py
```

## 🛠️ Project Structure
*   `scripts/`: Application logic, training scripts, and utilities.
*   `data/`: CSV datasets (Base stats, Match logs, Meta performance).
*   `analysis_plots/`: Generated analytics plots.

---
*Powered by Scikit-Learn, Streamlit, and Pandas.*
