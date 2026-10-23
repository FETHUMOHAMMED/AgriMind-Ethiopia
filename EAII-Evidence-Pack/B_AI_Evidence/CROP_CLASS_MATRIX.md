# AgriMind Crop-by-Crop AI Class Matrix

**Status:** Phase A — taxonomy defined, public data verification IN PROGRESS
**Date:** 2026-10-23
**Last verified:** (update each time a class is verified)
**Scope:** 6 Ethiopian priority crops + 3 existing dev crops

## ⚠️ Status Legend — Read This First

| Mark | Meaning |
|---|---|
| ✅ **VERIFIED** | Actual count confirmed on disk by script or manual download |
| 🟡 **TO VERIFY** | Public dataset believed to exist; not yet downloaded/audited |
| 🔴 **UNKNOWN** | No information; requires investigation |
| ⛔ **NOT AVAILABLE** | Confirmed no viable public data exists |

**IMPORTANT:** Any 🟡 TO VERIFY number in this matrix is an ESTIMATE and must NOT
be cited in pitch materials, EAII submission, or funder conversations until
upgraded to ✅ VERIFIED.

---

## 1. Wheat

| Class | On-disk (verified) | Public source | Public count | Trainable now? | Blocker |
|---|---:|---|---:|---|---|
| healthy | 0 | PlantVillage / Kaggle / Mendeley | 🟡 TO VERIFY | 🔴 Pending | Data sourcing |
| brown_rust | 3 | PlantVillage | 🟡 TO VERIFY | 🔴 Pending | Data sourcing |
| yellow_rust | 0 | PlantVillage | 🟡 TO VERIFY | 🔴 Pending | Data sourcing |
| stem_rust | 0 | (Ethiopian variety) | 🔴 UNKNOWN | ⛔ Field required | No known public source |
| septoria | 0 | PlantVillage | 🟡 TO VERIFY | 🔴 Pending | Data sourcing |

**Phase B decision:** Pending data verification (target: ≥100 usable images/class
after deduplication and label audit).

---

## 2. Maize

| Class | On-disk (verified) | Public source | Public count | Trainable now? | Blocker |
|---|---:|---|---:|---|---|
| healthy | 0 | PlantVillage | 🟡 TO VERIFY | 🔴 Pending | Data sourcing |
| common_rust | 3 | PlantVillage | 🟡 TO VERIFY | 🔴 Pending | Data sourcing |
| northern_leaf_blight | 4 | PlantVillage | 🟡 TO VERIFY | 🔴 Pending | Data sourcing |
| gray_leaf_spot | 0 | PlantVillage | 🟡 TO VERIFY | 🔴 Pending | Data sourcing |
| fall_armyworm | 0 | Specialty datasets | 🔴 UNKNOWN | ⛔ Field required | Verify availability |

**Phase B decision:** Pending data verification.

---

## 3. Coffee

| Class | On-disk (verified) | Public source | Public count | Trainable now? | Blocker |
|---|---:|---|---:|---|---|
| healthy | 0 | PlantVillage | 🟡 TO VERIFY | 🔴 Pending | Data sourcing |
| leaf_rust | 4 | PlantVillage + RoCoLe | 🟡 TO VERIFY | 🔴 Pending | Data sourcing |
| berry_disease | 0 | RoCoLe | 🟡 TO VERIFY | 🔴 Pending | Data sourcing |
| wilt | 0 | (Ethiopian) | 🔴 UNKNOWN | ⛔ Field required | No known public source |

**Phase B decision:** Pending data verification. RoCoLe access requires
institutional request (not direct download).

---

## 4. Teff

| Class | On-disk (verified) | Public source | Public count | Trainable now? | Blocker |
|---|---:|---|---:|---|---|
| healthy | 0 | Kaggle / Mendeley | 🟡 TO VERIFY | 🔴 Pending | Verify existence + quality |
| rust | 0 | Kaggle / Mendeley | 🟡 TO VERIFY | 🔴 Pending | Verify existence + quality |

**Phase B decision:** Conditional. If verified data < 100 images/class → defer
to Phase C (field collection at Debre Zeit ARC).

---

## 5. Enset

| Class | On-disk (verified) | Public source | Public count | Trainable now? | Blocker |
|---|---:|---|---:|---|---|
| healthy | 0 | None known | 🔴 UNKNOWN | ⛔ Field required | No public data |
| bacterial_wilt | 0 | None known | 🔴 UNKNOWN | ⛔ Field required | No public data |

**Phase B decision:** ⛔ DO NOT TRAIN. Enset requires Phase C field collection
with Areka ARC. Do not cite enset AI capability in any pitch material until
field data is collected and validated.

---

## 6. Root Crops (Assess Each Separately)

**First decision needed:** which specific root crops?

| Crop | On-disk | Public source | Public count | Trainable now? |
|---|---:|---|---:|---|
| Sweet potato | 0 | PlantVillage | 🟡 TO VERIFY | 🔴 Pending |
| Cassava | 0 | Multiple public datasets | 🟡 TO VERIFY | 🔴 Pending |
| Taro | 0 | None significant | 🔴 UNKNOWN | ⛔ Field required |
| Irish potato | 2,158 | Already in model | ✅ VERIFIED | ✅ Already trained (v2) |

**Phase B decision:** Sweet potato and cassava pending verification. Taro
deferred. Irish potato preserved as existing development work.

---

## 7–9. Existing Dev Crops (Preserve, Do Not Retrain)

| Crop | Classes | On-disk (verified) | Model status |
|---|---|---:|---|
| Tomato | 7 | 12,767 ✅ | Trained (v2, 95.27% leakage-controlled) |
| Pepper | 2 | 2,475 ✅ | Trained (v2) |
| Potato | 3 | 2,158 ✅ | Trained (v2) |

**Decision:** Keep these models deployed. Do not retrain during Phase B.

---

## Phase Sequence

| Phase | Timing | Action | Exit criterion |
|---|---|---|---|
| **A (now)** | Oct–Nov 2026 | Taxonomy + public data search + verification | All classes marked ✅ or ⛔ |
| **B** | Nov 2026–Jan 2027 | Train classes with ≥100 verified images | Per-class F1 documented |
| **C** | Q1–Q2 2027 | Field collection at ARC sites | 200+ field images/class |
| **D** | Q3 2027 | Retrain on Ethiopian field data | Independent field test |
| **E** | Q4 2027 | Controlled pilot with DAs | Field validation passes |

**Timeline estimates are planning targets, not guaranteed delivery dates.**

---

## Verification Protocol — How to Fill This Matrix

For every 🟡 TO VERIFY row:

1. **Locate the dataset** — direct download, Kaggle, Mendeley, or institutional request
2. **Download sample** — minimum 20 images to assess
3. **Count images per class** — actual count after download
4. **Check license** — must permit ML training + redistribution or derivative use
5. **Audit labels** — sample 20 images; what % match the class label?
6. **Check split quality** — if a public split exists, does it leak near-duplicates?
7. **Update matrix** — change 🟡 to ✅ with verified count, or ⛔ if unavailable

**Only after this 7-step process may a class be marked trainable.**

---

## Honest Disclosure

**What this matrix establishes:**
- Class taxonomy for 6 Ethiopian priority crops + 3 existing dev crops
- On-disk image counts (verified by script)
- Which classes need public data (marked 🟡)
- Which classes have no known path (marked ⛔)
- Phased execution plan

**What this matrix does NOT establish:**
- That any public dataset actually contains the estimated counts
- That any Phase B model will perform well on Ethiopian field images
- That enset AI diagnosis is feasible in the near term
- That public-dataset performance transfers to Ethiopian farms

**All Phase B results must be labeled "public-dataset-trained, Ethiopian field
validation pending" until Phase D/E.**