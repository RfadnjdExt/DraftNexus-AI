# Model Training Comparison Report
## Scenario: Swiss Stage vs Swiss + Knockout (Day 1)

### Accuracy
- **Baseline (Swiss Only)**: 0.6215
- **With Knockout Day 1**: 0.6412
- **Difference**: +0.0197

### Strategic Feature Importance Change
Values indicate how much the model relies on specific hero attributes.

| Feature            |   Importance (Swiss) |   Importance (Swiss+KO) |   Change |
|:-------------------|---------------------:|------------------------:|---------:|
| Late_Power         |               0.0648 |                  0.0678 |   0.0030 |
| Mid_Power          |               0.0488 |                  0.0484 |  -0.0005 |
| Early_Power        |               0.0405 |                  0.0442 |   0.0037 |
| Difficulty         |               0.0219 |                  0.0218 |  -0.0001 |
| Flex_Pick_Score    |               0.0194 |                  0.0190 |  -0.0003 |
| Economy_Dependency |               0.0169 |                  0.0169 |   0.0000 |
| Primary_Lane       |               0.0162 |                  0.0152 |  -0.0010 |
| Hard_CC_Count      |               0.0167 |                  0.0143 |  -0.0024 |
| Escape_Reliability |               0.0125 |                  0.0117 |  -0.0009 |
| Damage_Type        |               0.0089 |                  0.0079 |  -0.0010 |

### Interpretation
- **Accuracy**: Higher is better. A significant drop might indicate the new data conflicts with old patterns (meta shift).
- **Feature Importance**: Changes here show if the model is prioritizing different aspects (e.g., Early Power vs Late Power) due to the new Knockout games.
