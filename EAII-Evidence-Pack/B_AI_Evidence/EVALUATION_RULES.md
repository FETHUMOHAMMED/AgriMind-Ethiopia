# AGRIMIND MODEL EVALUATION RULES

## Non-Negotiable Rules

### 1. Split by Case, Not by Photo
- Multiple images of the same plant MUST stay in the same split.
- Never train on one angle and test on another angle of the same plant.

### 2. Leave Farms/Sessions Out
- At least one evaluation must use entirely separate farms/sessions.
- This tests generalization to new conditions.

### 3. Test Different Regions/Seasons
- Random split is NOT enough.
- Test on a region or season the model has never seen.

### 4. Measure More Than Accuracy
Report:
- Per-class precision and recall
- Macro-F1 score
- Confusion matrix
- Calibration (how well confidence matches correctness)
- Abstention rate (how often the model says "uncertain")

### 5. Compare Against Context-Only Baseline
- If context-only performs unusually well, investigate data leakage.
- Check whether location, date, or collection patterns are leaking labels.

### 6. Document Reference Diagnosis Source
- Expert assessment
- Laboratory confirmation
- Field observation
- Farmer report
- Unverified label

## The Success Criterion

NOT: "Multimodal achieves 98%."

BUT: "Does multimodal improve performance on unseen Ethiopian field cases, across the disease classes and locations we intend to support, without creating misleading confidence?"