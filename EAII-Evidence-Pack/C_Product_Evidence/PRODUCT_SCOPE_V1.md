# AgriMind Product Scope — First Version (DA-Facing)

**Primary user:** Agricultural Development Agent (DA)
**Secondary user:** Cooperative advisor / expert reviewer
**Buyer:** Cooperative or union (to be validated)

## What the app must do (v1)

1. **Record a field case**
   - Crop (dropdown, includes unsupported crops)
   - Location (GPS or manual)
   - Date, growth stage
   - Symptoms (text + photos)

2. **Capture images with guidance**
   - Prompt for the correct plant part (leaf / berry / whole plant)
   - Flag poor-quality images (blurry, too dark)
   - Suggest retake if image won't be useful

3. **AI assessment — only when supported**
   - Coffee: 4 classes (healthy, leaf_rust, cercospora, phoma)
   - Wheat: 3 classes (healthy, septoria, stripe_rust)
   - Tomato/pepper/potato: existing classes (from current production model)
   - **All other crops**: "AI diagnosis not available — case recorded for referral"

4. **Communicate uncertainty**
   - Confidence score with explanation
   - "Low confidence — verify with expert" (threshold set per crop)
   - Explicit "Unknown" state when model can't classify

5. **Support expert referral**
   - Export case as a structured summary (crop, symptoms, photos, AI result)
   - Share to WhatsApp / email / cooperative system
   - Track referral status

6. **Record the outcome**
   - Specialist's conclusion (when it comes back)
   - Action taken by farmer
   - Follow-up date

## What the app must NOT do (v1)

- ❌ Prescribe pesticide doses
- ❌ Diagnose crops outside supported classes
- ❌ Replace expert judgment for high-risk cases
- ❌ Claim accuracy on regions where we haven't validated

## Treatment recommendations

- Provided for supported classes only, with "agronomist review required" flag
- Generic advice for unsupported classes: "consult expert"
- No pesticide dosage recommendations until agronomist-validated

## Success metrics (for the pilot)

**Workflow:**
- DA can record a complete case in < 5 minutes
- Referral flow works end-to-end
- Outcome recorded for 80%+ of cases

**AI (supported crops only):**
- Agronomist agrees with AI on ≥ 85% of 20 sampled cases
- Zero unsafe recommendations
- AI abstains on unsupported cases 100% of the time

**Business:**
- Cooperative manager agrees to discuss paid continuation
- Named budget source identified