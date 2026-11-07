# Priority Crop Matrix — Proposed Scoring

**Status:** PROPOSED, not final. Scores are draft estimates based on
current evidence. Marked [ASSUMED] where evidence is missing.

**Weights:** Severity 25% · User importance 20% · Data availability 20%
            Specialist validation 15% · Field feasibility 10% · Buyer 10%

## Scoring Table

| Crop | Severity | User importance | Data availability | Specialist | Field feasibility | Buyer | **Weighted** |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Coffee** | 4 [ASSUMED] | 5 | **4 [VERIFIED]** | 3 [ASSUMED] | 3 [ASSUMED] | 4 [ASSUMED] | **3.95** |
| **Wheat** | 4 [ASSUMED] | 4 | 3 [VERIFIED: 407] | 3 [ASSUMED] | 4 [ASSUMED] | 3 [ASSUMED] | **3.55** |
| **Maize** | 4 [ASSUMED] | 5 | **1 [VERIFIED: 0 imgs]** | 3 [ASSUMED] | 3 [ASSUMED] | 3 [ASSUMED] | **3.25** |
| **Teff** | 3 [ASSUMED] | 4 | **1 [VERIFIED: 0 imgs]** | 2 [ASSUMED] | 3 [ASSUMED] | 3 [ASSUMED] | **2.65** |
| **Enset** | 3 [ASSUMED] | 3 | **1 [VERIFIED: 0 imgs]** | 2 [ASSUMED] | 2 [ASSUMED] | 2 [ASSUMED] | **2.25** |

## What's Verified vs Assumed

### Verified data availability
- **Coffee**: 2,529 unique Ethiopian images verified (from Kaggle benchmark, pHash deduped)
- **Wheat**: 407 Ethiopian Holeta images verified
- **Maize/Teff/Enset**: 0 verified Ethiopian images

### Assumed — needs customer discovery to confirm
- Severity scores (no field interviews yet)
- User importance scores (no DA interviews yet)
- Specialist validation scores (no agronomist contacts confirmed)
- Field feasibility scores (no ARC access agreements)
- Buyer potential scores (no cooperative manager interviews yet)

## Interpretation

**What this matrix says:** based on verified data availability, coffee and
wheat are the two crops where AI development is grounded in real evidence.
Maize, teff, and enset are theoretically important but have no data.

**What this matrix does NOT say:** that coffee is more important than maize
to farmers. The "user importance: 5" for maize is assumed, not measured.
Only customer discovery can rank crop importance honestly.

## Decision Gate

Before committing to the production crop roadmap:
1. Complete 5-8 DA interviews (validates severity, user importance scores)
2. Complete 2-3 buyer interviews (validates buyer potential scores)
3. Confirm at least one specialist contact per crop (validates specialist score)
4. Re-score with actual evidence

The matrix is a framework for re-scoring after interviews, not a decision.