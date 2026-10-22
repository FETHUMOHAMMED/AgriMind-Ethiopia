# AgriMind-Ethiopia: EAII Submission Summary

**Date:** 2026-10-19
**Prepared for:** Ethiopian Artificial Intelligence Institute (EAII)

---

## What Works

### Deployed Application
- Flutter mobile app with login, registration, crop diagnosis, prediction history, and profile management
- FastAPI backend with JWT authentication, prediction history, feedback system
- Live production model: `agrimind_mobilenetv2.pth` (19-class, MobileNetV2, PlantVillage-derived)
- Confidence threshold: 0.30; uncertain predictions return explicit "Unknown / Uncertain" to the user
- All backend tests pass: 8/8 pytest
- All Flutter tests pass; `flutter analyze` reports 0 issues
- **No fabricated fallbacks** ? model unavailable returns HTTP 503, invalid image returns HTTP 400

### Evaluated Candidate Model (not deployed)
- `agrimind_mobilenetv2_v2.pth` (15-class, MobileNetV2, retrained on the same source data with leakage-controlled splitting)
- **- **Top-1 accuracy: 95.27%** on 3,106 held-out images evaluated under Scenario B's documented duplicate-exclusion protocol
- Top-3: 99.48%; Macro-F1: 0.9508; Weighted-F1: 0.9529
- All 15 supported classes have per-class F1 >= 0.89

### Evaluation Infrastructure
- Reproducible train/val/test split (`splits.json`, seed=42, stratified)
- Three sensitivity scenarios (original / Scenario A / Scenario B) with documented results
- pHash + SHA-256 duplicate audit across train/val and train/test boundaries
- Every reported number traceable to a preserved CSV/JSON/report file

---

## What Has Been Evaluated

### Model Performance (v2, evaluated candidate)
| Split | Test Images | Top-1 | Top-3 | Macro-F1 | Weighted-F1 |
|---|---|---|---|---|---|
| Original | 3,114 | 95.28% | 99.49% | 0.9509 | 0.9530 |
| Scenario A (3 byte-identical test duplicates excluded) | 3,111 | 95.27% | 99.49% | 0.9508 | 0.9530 |
| Scenario B (3 test duplicates + 5 same-leaf candidates excluded) | 3,106 | 95.27% | 99.48% | 0.9508 | 0.9529 |

**Interpretation:** 
Scenario B achieved 95.27% Top-1 accuracy on 3,106 held-out images 
after excluding three confirmed byte-identical test-set duplicates and 
five additional suspected same-leaf candidates. 
The result is stable relative to the original test evaluation at 
the reported precision. This is a partial leakage-control sensitivity 
analysis, not proof that all dataset leakage has been eliminated. 
One byte-identical duplicate was identified across the original training 
and validation partitions; its effect on validation metrics and checkpoint 
selection has not been independently quantified. 
The evaluation uses public-dataset-derived images and does not establish 
diagnostic accuracy on Ethiopian farms.

### Duplicate Audit
- **Test-set leakage:** 3 confirmed byte-identical duplicates (SHA-256 match). Documented in all reports.
- **Train/val leakage:** 1 confirmed byte-identical duplicate. Documented with explicit statement that its effect on val metrics and checkpoint selection has NOT been independently quantified.
- **Root cause:** all 4 confirmed duplicates belong to the same PlantVillage "GHLB_PS ... Day 13" photography session. This is a structural artifact of filename-based random splitting, not random error.

### Dataset Integrity
- Total unique images in project: **20,669** (PlantVillage-derived, public reference imagery)
- Folders containing copies of the same 20,669 images: **3** (`flat_crops/`, `ethiopian_crops/`, `Original_31_Images/`)
- Total file instances across all 3 folders: 62,007
- Field-verified images (`Field_Verified: TRUE`): **0 of 20,669**

---

## What Remains Unverified

### Ethiopian Field Data
- **Independently collected Ethiopian field photographs: 0**
- **Expert-verified (Tier 2) Ethiopian images: 0**
- **Lab-confirmed (Tier 3) Ethiopian images: 0**
- The dataset registers and folder names (`ethiopian_crops/`, `Original_31_Images/`) reference intended Phase 2 content and an earlier project phase ? NOT actual Ethiopian field collection.
- The register `DATASET_REGISTER_MASTER.csv` is a planning template with future-dated collection entries (Nov/Dec 2026). It is a plan, not a record of completed collection.

### Model Validation
- The reported 95.27% test accuracy is on a held-out split of a public-dataset-derived corpus. It is **NOT evidence of Ethiopian farm accuracy.**
- Field-validated disease diagnosis: NOT DEMONSTRATED
- Lab-confirmed disease diagnosis: NOT DEMONSTRATED

### Coverage
- **Teff is 0% implemented** (0 images across `teff/healthy`, `teff/rust`)
- Healthy reference images are missing for coffee, maize, and wheat
- Supported scope for the evaluated v2 model is 15 classes across tomato, pepper, and potato only

### Deferred Audits
- Broader duplicate audit beyond the 15 pHash candidates ? same threshold would need to be re-justified
- Effects of train/val duplicate on epoch selection ? requires controlled experiment, not currently performed

---

## Phase 2 Roadmap (Documented, Not Started)

### Ethiopian Field Data Collection
- 5 partner Agricultural Research Centers identified:
  - Jimma ARC (Coffee)
  - Melkassa ARC (Maize)
  - Kulumsa ARC (Wheat)
  - Debre Zeit ARC (Teff)
  - Areka ARC (Enset)
- Tier 2 expert-assessment protocol
- Tier 3 lab-confirmation protocol (PCR / culture)

### Splitting Improvement
- Group images by photography session BEFORE random partition (would eliminate the Day-13-series structural leakage)
- Stratify by both crop/disease class AND collection session

### Model Improvement
- Retrain with the corrected split
- Add teff and healthy-reference coverage
- Deploy v2 after EAII-authorized review

---

## What's Deployed vs. Evaluated

| Layer | In Production | In Evidence Pack |
|---|---|---|
| Model | `agrimind_mobilenetv2.pth` (v1, 19 classes, threshold 0.30) | `agrimind_mobilenetv2_v2.pth` (v2, 15 classes, evaluated at 95.27%) |
| Backend predictor | `real_predictor.py` (v1 paths) | v2 checkpoint preserved, unchanged by any audit action |
| Splits | `splits.json` (original, used to train both v1 and v2) | `splits_scenarioA.json`, `splits_scenarioB.json` (sensitivity analysis) |
| Reports | ? | 4? classification reports, 4? confusion matrices, 2? audits, 2? disclosure documents |

**The v2 model is evaluated but not deployed. The v1 model is deployed but not evaluated under the leakage-controlled protocol. This distinction is documented everywhere and reflected in the CRITICAL_DISCLOSURE_INVENTORY_VS_FIELD_DATA.txt file.**

---

## Evidence File Index

### Dataset Evidence (`A_Dataset_Evidence/`)
- `CRITICAL_DISCLOSURE_INVENTORY_VS_FIELD_DATA.txt` ? **primary honesty anchor**
- `ETHIOPIAN_CROPS_PROVENANCE_AUDIT.csv` (20,669 rows, all `Field_Verified: FALSE`)
- `ETHIOPIAN_CROPS_PROVENANCE_AUDIT_SUMMARY.txt`
- `_obsolete/` (legacy files, clearly named with `_ORIGINAL_WRONG_NAME` marker)

### Model Evidence (`B_AI_Evidence/Metrics/`)
- `CLASSIFICATION_REPORT_v2_TEST.txt` (original split)
- `CLASSIFICATION_REPORT_v2_TEST_SPLITS.txt` (reproducible rerun)
- `CLASSIFICATION_REPORT_v2_TEST_SCENARIOA.txt`
- `CLASSIFICATION_REPORT_v2_TEST_SCENARIOB.txt`
- `confusion_matrix_v2_test*.csv` (4 files)
- `LEAKAGE_CONTROLLED_EVALUATION_SUMMARY.txt` (three-way comparison)
- `TRAIN_VAL_PHASH_AUDIT.csv` / `.txt` (train/val audit)
- `TRAIN_VAL_AUDIT_INTERPRETATION.txt` (corrected wording per advisor guidance)
- `phash_train_test_contact_sheet.jpg` (visual reference)

### Splits (`backend/app/ai/datasets/`)
- `splits.json` (original, 3,114 test images)
- `splits_scenarioA.json` (3,111 test images)
- `splits_scenarioB.json` (3,106 test images)
- `splits_v2_PRIOR_8PAIR_ATTEMPT.json` (earlier attempt, preserved)

### Checkpoints (`backend/app/ai/model/`)
- `agrimind_mobilenetv2.pth` ? v1, 19 classes, SHA256 `9b2a3c05...`
- `agrimind_mobilenetv2_v2.pth` ? v2, 15 classes, SHA256 `5d17fede...`

---

## Recommended EAII Framing

> "AgriMind-Ethiopia has built a working crop-disease diagnosis application with a MobileNetV2 model that achieves 95.27% top-1 accuracy on a held-out, leakage-controlled split of a 20,669-image public-dataset-derived corpus covering 15 crop-disease classes across tomato, pepper, and potato. Three confirmed byte-identical test-set duplicates and one train/val duplicate have been identified and documented; the reported result is stable to within 0.01 percentage points after excluding them. The project has 0 confirmed Ethiopian field photographs. A Phase 2 field-data collection plan has been designed with 5 partner Agricultural Research Centers under Tier 2 expert-assessment and Tier 3 lab-confirmation protocols."

---

*End of submission summary.*
