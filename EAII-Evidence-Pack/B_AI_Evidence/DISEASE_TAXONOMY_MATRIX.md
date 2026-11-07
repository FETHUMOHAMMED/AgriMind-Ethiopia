# Disease Taxonomy Matrix — Verified and Proposed Classes

Legend:
- ✅ VERIFIED: In training config, images counted
- 🟡 PROPOSED: Candidate for future work, no data yet
- ❌ NOT-PHOTO-DETECTABLE: Requires field inspection beyond image

## Coffee

### Currently supported (VERIFIED — from training config)
| Class | Image part | Count | Who verified labels? | Photo-sufficient? |
|---|---|---:|---|---|
| healthy | leaf | 720 | Kaggle benchmark (source unclear) | ✅ |
| leaf_rust | leaf (underside) | 842 | Kaggle benchmark | ✅ |
| cercospora | leaf | 506 | Kaggle benchmark | ✅ |
| phoma | leaf | 461 | Kaggle benchmark | ✅ |

### Proposed candidates (no data — needs research)
| Class | Image part needed | Photo-sufficient? | Data exists? |
|---|---|---|---|
| coffee_berry_disease | berry (sunken lesions) | ✅ Likely | 🔴 None verified |
| coffee_wilt | whole plant (wilting, yellowing) | ❌ Not from single leaf | 🔴 None |
| leaf_spot/blight | leaf | ✅ | 🟡 Needs specialist confirmation of label consistency |
| unknown / uncertain | any | ✅ App outcome (must include) | — |

### Coffee taxonomy decision
- **Keep current 4 classes** as the experimental model's scope
- **Add "Unknown/Uncertain"** as an explicit app outcome (not just model class)
- **Berry disease** requires berry images + specialist labels — Phase C research
- **Wilt** requires whole-plant workflow + expert referral — Phase C research

## Wheat

### Currently supported (VERIFIED — Holeta training)
| Class | Image part | Count | Who verified? | Photo-sufficient? |
|---|---|---:|---|---|
| healthy | leaf | 102 | Holeta researchers (plant pathologists) | ✅ |
| septoria | leaf (necrotic lesions) | 97 | Holeta researchers | ✅ |
| stripe_rust | leaf (yellow-orange pustules) | 208 | Holeta researchers | ✅ |

### Proposed (no data)
| Class | Image part | Photo-sufficient? | Data exists? |
|---|---|---|---|
| leaf_rust | leaf (brown pustules) | ✅ | 🔴 No Ethiopian data |
| FHB (Fusarium head blight) | spike/head (bleached spikelets) | ❌ Not from leaf | 🔴 No Ethiopian data |
| stem_rust | stem + leaf | ✅ | 🔴 No Ethiopian data |

### Wheat taxonomy decision
- **Keep current 3 classes** as experimental scope
- **Do not expand to 5 classes** without Ethiopian data for the new classes
- **FHB requires spike images**, not leaf images — different data collection protocol
- **Leaf rust and stem rust** require Phase C data collection

## Maize, Teff, Enset

### Maize — Phase A research
| Candidate disease | Image part | Notes |
|---|---|---|
| fall_armyworm | leaf + whorl | Major Ethiopian pest |
| northern_leaf_blight | leaf | Published PlantVillage data |
| common_rust | leaf | Published PlantVillage data |
| healthy | leaf | — |

**Decision:** Taxonomy research only. Do not train until Ethiopian field
data is verified.

### Teff — Phase A research
| Candidate disease | Image part | Notes |
|---|---|---|
| teff_rust | leaf | Little public data |
| head_smudge | head | Little public data |
| healthy | leaf | — |

**Decision:** Defer until Ethiopian specialist identifies priority diseases.

### Enset — Phase C only
| Candidate disease | Image part | Notes |
|---|---|---|
| bacterial_wilt | whole plant | No public data. Requires field collection. |
| healthy | whole plant | — |

**Decision:** No AI capability until Phase C field collection at Areka ARC.

## The "Unknown" Outcome Is a Feature, Not a Failure

Every model in production must return either:
1. A supported class with confidence in [0, 1]
2. **"Unknown / Uncertain"** with explanation

For unsupported crops, the app returns:
- "This crop is not yet supported by AgriMind AI. Recording case for expert referral."

This is not a limitation of the AI — it is the correct safety behavior.