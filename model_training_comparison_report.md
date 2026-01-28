# Model Training Comparison Report
## Scenario: Swiss+Knockout vs Including Grand Finals

### Accuracy
- **Baseline (Swiss + Knockout)**: 0.6196
- **With Grand Finals**: 0.6132
- **Difference**: -0.0064

### Strategic Feature Importance Change
Values indicate how much the model relies on specific hero attributes.

| Feature            |   Importance (Baseline) |   Importance (With GF) |   Change |
|:-------------------|------------------------:|-----------------------:|---------:|
| Late_Power         |                  0.0644 |                 0.0647 |   0.0004 |
| Mid_Power          |                  0.0446 |                 0.0514 |   0.0068 |
| Early_Power        |                  0.0395 |                 0.0418 |   0.0023 |
| Difficulty         |                  0.0208 |                 0.0204 |  -0.0004 |
| Flex_Pick_Score    |                  0.0187 |                 0.0203 |   0.0015 |
| Economy_Dependency |                  0.0180 |                 0.0181 |   0.0001 |
| Primary_Lane       |                  0.0152 |                 0.0158 |   0.0005 |
| Hard_CC_Count      |                  0.0145 |                 0.0136 |  -0.0008 |
| Escape_Reliability |                  0.0125 |                 0.0122 |  -0.0003 |
| Damage_Type        |                  0.0071 |                 0.0072 |   0.0001 |

### Interpretation
- **Accuracy**: Higher is better. A significant drop might indicate the new data conflicts with old patterns (meta shift).
- **Feature Importance**: Changes here show if the model is prioritizing different aspects (e.g., Early Power vs Late Power) due to the new Knockout games.
