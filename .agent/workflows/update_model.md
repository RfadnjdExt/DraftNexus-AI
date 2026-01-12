---
description: How to retrain the ML model after adding new match logs
---

Follow these steps whenever you add new rows to `data/match_logs_real.csv`:

1.  **Generate Dataset**
    Process the new real logs, apply temporal weights, and combine them with fresh synthetic data.
    ```bash
    python scripts/generate_training_data.py
    ```

2.  **Retrain Model**
    Train the Random Forest on the updated dataset.
    ```bash
    # // turbo
    python scripts/train_model.py
    ```

3.  **Verify (Optional)**
    Run a quick inference test to ensure the model is working.
    ```bash
    python scripts/recommend_hero.py
    ```
