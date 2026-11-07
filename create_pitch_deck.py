"""
Generate an honest, submission-ready EAII pitch deck for AgriMind-Ethiopia.

Fixes all round-53 overclaims:
  - Removes "Early Ethiopian Dataset" (slide 1)
  - Removes "We have Ethiopian field data" (slide 10)
  - Removes "Expert validation — scientifically credible" (slide 12)
  - Adds segment-by-segment reality table
  - Adds Stage 2+ clarifier for business model
  - Distinguishes v1 (deployed) from v2 (evaluated)

Run: python create_pitch_deck.py
Output: AgriMind-EAII-Idea-Stage-Deck_v2_HONEST.pptx
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# ============================================================
# Color scheme
# ============================================================
PRIMARY = RGBColor(0x1B, 0x5E, 0x20)     # dark green
ACCENT = RGBColor(0x4C, 0xAF, 0x50)      # mid green
DARK = RGBColor(0x21, 0x21, 0x21)
GRAY = RGBColor(0x75, 0x75, 0x75)
LIGHT_BG = RGBColor(0xF1, 0xF8, 0xE9)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
RED = RGBColor(0xC6, 0x28, 0x28)
AMBER = RGBColor(0xF5, 0x7C, 0x00)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)


# ============================================================
# Helper functions
# ============================================================
def add_title_slide(title, subtitle, footer=""):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg = slide.shapes.add_shape(1, 0, 0, prs.slide_width, prs.slide_height)
    bg.fill.solid()
    bg.fill.fore_color.rgb = PRIMARY
    bg.line.fill.background()

    tb = slide.shapes.add_textbox(Inches(1), Inches(2.3), Inches(11.3), Inches(1.5))
    tf = tb.text_frame
    tf.text = title
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.runs[0].font.size = Pt(48)
    p.runs[0].font.bold = True
    p.runs[0].font.color.rgb = WHITE

    tb2 = slide.shapes.add_textbox(Inches(1), Inches(4.0), Inches(11.3), Inches(1.2))
    tf2 = tb2.text_frame
    tf2.text = subtitle
    p2 = tf2.paragraphs[0]
    p2.alignment = PP_ALIGN.CENTER
    p2.runs[0].font.size = Pt(22)
    p2.runs[0].font.color.rgb = WHITE

    if footer:
        tb3 = slide.shapes.add_textbox(Inches(1), Inches(6.2), Inches(11.3), Inches(1.2))
        tf3 = tb3.text_frame
        tf3.word_wrap = True
        for i, line in enumerate(footer.split("\n")):
            if i == 0:
                p3 = tf3.paragraphs[0]
            else:
                p3 = tf3.add_paragraph()
            p3.text = line
            p3.alignment = PP_ALIGN.CENTER
            p3.runs[0].font.size = Pt(13)
            p3.runs[0].font.color.rgb = WHITE


def add_content_slide(title, subtitle=""):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    header = slide.shapes.add_shape(1, 0, 0, prs.slide_width, Inches(1.2))
    header.fill.solid()
    header.fill.fore_color.rgb = PRIMARY
    header.line.fill.background()

    tb = slide.shapes.add_textbox(Inches(0.5), Inches(0.25), Inches(12.3), Inches(0.8))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.text = title
    p = tf.paragraphs[0]
    p.runs[0].font.size = Pt(30)
    p.runs[0].font.bold = True
    p.runs[0].font.color.rgb = WHITE

    if subtitle:
        tb2 = slide.shapes.add_textbox(Inches(0.5), Inches(1.35), Inches(12.3), Inches(0.5))
        tf2 = tb2.text_frame
        tf2.word_wrap = True
        tf2.text = subtitle
        p2 = tf2.paragraphs[0]
        p2.runs[0].font.size = Pt(16)
        p2.runs[0].font.color.rgb = GRAY
        p2.runs[0].font.italic = True
    return slide


def add_bullets(slide, bullets, left=0.5, top=1.95, width=12.3, height=5.2, size=18):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, bullet in enumerate(bullets):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = bullet
        if p.runs:
            p.runs[0].font.size = Pt(size)
            p.runs[0].font.color.rgb = DARK
        p.space_after = Pt(6)


def add_table(slide, headers, rows, left=0.5, top=1.9, width=12.3, height=4.5,
              col_widths=None, font_size=12):
    n_rows = len(rows) + 1
    n_cols = len(headers)
    table_shape = slide.shapes.add_table(n_rows, n_cols, Inches(left), Inches(top),
                                          Inches(width), Inches(height))
    table = table_shape.table
    if col_widths:
        for i, w in enumerate(col_widths):
            table.columns[i].width = Inches(w)

    for i, h in enumerate(headers):
        cell = table.cell(0, i)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = PRIMARY
        for p in cell.text_frame.paragraphs:
            p.alignment = PP_ALIGN.CENTER
            for r in p.runs:
                r.font.size = Pt(13)
                r.font.bold = True
                r.font.color.rgb = WHITE

    for r_idx, row in enumerate(rows, start=1):
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx, c_idx)
            cell.text = str(val)
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if r_idx % 2 == 1 else LIGHT_BG
            for p in cell.text_frame.paragraphs:
                p.alignment = PP_ALIGN.LEFT
                for r in p.runs:
                    r.font.size = Pt(font_size)
                    r.font.color.rgb = DARK


# ============================================================
# SLIDE 1 — Title
# ============================================================
add_title_slide(
    "AgriMind-Ethiopia",
    "From Disease Diagnosis to African Agricultural Intelligence",
    "Founder & Technical Lead: Fethu Mohammed\n"
    "EAII AI Startup Support Program — 2026 Cohort II\n"
    "Current Stage: Working MVP • PlantVillage-derived training data • Phase 2 field validation planned"
)

# ============================================================
# SLIDE 2 — Honest Status: Have vs Don't Have
# ============================================================
s = add_content_slide(
    "Where We Are Today — Honestly",
    "One product, one user, one well-defined problem"
)
add_table(s,
    ["What we HAVE today", "What we DO NOT have yet"],
    [
        ("Single-leaf disease diagnosis (one photo at a time)", "Cooperative dashboards"),
        ("3 languages: English, Amharic, Afaan Oromo", "Bulk processing / batch diagnosis"),
        ("Mobile (Android) + Web app", "API access for third parties"),
        ("Prediction history per user", "Aggregate analytics & early warning"),
        ("Feedback system (thumbs up/down)", "Expert chat / escalation"),
        ("Trained on 20,669 PlantVillage-derived images", "Ethiopian field photographs (0 verified)"),
        ("95.27% top-1 on 3,106 held-out PlantVillage-derived images", "Field-validated accuracy on Ethiopian farms"),
    ],
    top=1.9, height=4.8, col_widths=[6.15, 6.15]
)

# ============================================================
# SLIDE 3 — The Problem
# ============================================================
s = add_content_slide(
    "The Problem We Solve",
    "Disease diagnosis is slow, expensive, and inaccessible for most Ethiopian farmers"
)
add_bullets(s, [
    "🌾  Smallholder farmers lose crops to preventable diseases because expert diagnosis is far away",
    "📞  Extension workers cover hundreds of farmers and cannot visit every field weekly",
    "📱  Existing crop-diagnosis apps are English-only, urban-designed, or require paid APIs",
    "🌍  No public AI model covers Ethiopian crop varieties at the local disease level",
    "🎯  Result: a farmer photographs a diseased leaf and needs an answer within seconds — in their own language",
], top=2.2, size=19)

# ============================================================
# SLIDE 4 — What the MVP Actually Does
# ============================================================
s = add_content_slide(
    "What the MVP Actually Does",
    "Every claim on this slide is verified in our GitHub evidence pack"
)
add_bullets(s, [
    "✅  Farmer photographs a leaf → gets a disease name + confidence score",
    "✅  Response includes treatment, symptoms, prevention, expert escalation advice",
    "✅  Works in English, Amharic, and Afaan Oromo",
    "✅  Runs on any Android phone and in a browser",
    "✅  Model: MobileNetV2, 15 classes across tomato/pepper/potato (v2)",
    "✅  Backend: FastAPI with JWT auth, prediction history, feedback loop",
    "✅  14/14 backend tests passing",
    "",
    "⚠️  Recommendations currently marked 'REVIEW REQUIRED' — need agronomist validation",
    "⚠️  Coffee, maize, wheat, teff not yet supported (v2 excludes them)",
], top=2.0, size=17)

# ============================================================
# SLIDE 5 — SEGMENT REALITY TABLE (the key slide)
# ============================================================
s = add_content_slide(
    "The Reality: One Product ≠ All Customers",
    "Different segments need substantially different features"
)
add_table(s,
    ["Segment", "What they need", "Do we have it?", "Will they pay?"],
    [
        ("Smallholder farmers", "Free diagnosis in local language", "✅ Yes", "❌ No (free)"),
        ("Extension workers (DAs)", "Fast multi-crop, bulk mode, export", "⚠️ Partially", "⚠️ Paid by co-op"),
        ("Cooperatives", "Dashboard, aggregate analytics, members", "❌ No", "✅ $500–5K/yr"),
        ("NGOs / Research", "API, bulk export, integration", "❌ No", "✅ $1K–5K/yr"),
        ("Commercial farms", "Full farm mgmt, SLA, integration", "❌ No", "✅ Higher"),
        ("Government", "National surveillance, analytics", "❌ No", "✅ $20K–100K"),
    ],
    top=1.9, height=3.5, col_widths=[2.8, 4.2, 2.4, 2.9], font_size=12
)
add_bullets(s, [
    "",
    "Strategy: validate with extension workers first — they use the MVP today, aggregate farmer demand, and are paid by our future paying customers.",
], top=5.6, size=16)

# ============================================================
# SLIDE 6 — Why DAs
# ============================================================
s = add_content_slide(
    "Why We Start with Extension Workers",
    "The wedge that unlocks the other segments"
)
add_bullets(s, [
    "👨‍🌾  Use the MVP today  —  DAs visit farms weekly, exactly the workflow our app fits",
    "📊  Aggregate demand  —  one DA reaches 100+ farmers; scale without 100 outreach visits",
    "💰  Paid for by  —  cooperatives and government (our future paying customers)",
    "⚡  Fast validation  —  DAs give feedback in days, not months",
    "🔁  Data flywheel  —  DAs feed us labeled field images, which improve the model",
    "",
    "Strategy: Validate with DAs → win the co-op contract → build co-op dashboard → scale.",
], top=2.2, size=20)

# ============================================================
# SLIDE 7 — Where to Validate
# ============================================================
s = add_content_slide(
    "Where We Validate First",
    "Four documented partner agricultural research centers in Oromia"
)
add_table(s,
    ["Site", "Partner ARC", "Crop", "Why it matters"],
    [
        ("Jimma", "Jimma ARC", "Coffee", "Ethiopia's largest coffee-producing zone"),
        ("Adama", "Melkassa ARC", "Maize", "Central Rift Valley maize belt"),
        ("Asella", "Kulumsa ARC", "Wheat", "Highland wheat production"),
        ("Bishoftu", "Debre Zeit ARC", "Teff", "Teff production and research hub"),
    ],
    top=1.9, height=2.4, col_widths=[2, 3, 2, 5.3], font_size=12
)
add_bullets(s, [
    "",
    "Phase 1 target (4 weeks, $0–500): deploy MVP to 5–10 extension workers in ONE cooperative",
    "Success metric: 3+ DAs using it 3+ times/week by week 4",
    "Feedback → validation → decide whether to expand, narrow, or pivot",
], top=4.6, size=17)

# ============================================================
# SLIDE 8 — Stage 2 Features Needed
# ============================================================
s = add_content_slide(
    "What We Need to Build for Cooperatives (Stage 2)",
    "Turning a free consumer app into a paying institutional product"
)
add_bullets(s, [
    "📊  Cooperative Dashboard  —  aggregate disease patterns across members",
    "🚨  Early Warning System  —  alerts when a disease spikes in a region",
    "📤  Bulk Processing  —  upload 100s of images, get 100s of diagnoses",
    "🔌  API Access  —  integrate with cooperative's existing software",
    "📈  Analytics Reports  —  exportable PDF/CSV for management and donors",
    "👥  Member Management  —  track which farmer submitted which diagnosis",
    "",
    "None of these exist today. They are 3–6 months of engineering after field validation.",
], top=2.2, size=19)

# ============================================================
# SLIDE 9 — Business Model with Stage 2+ disclaimer
# ============================================================
s = add_content_slide(
    "Business Model — Planned, Not Yet Realized",
    "Revenue streams begin Stage 2 (after field validation)"
)
add_table(s,
    ["Service", "Price Range", "Target Customer", "Status"],
    [
        ("Leaf diagnosis (farmers)", "Free forever", "Smallholder farmers", "✅ Built"),
        ("Cooperative Dashboard", "$500–5,000/yr", "Cooperatives", "⏳ Stage 2"),
        ("Analytics Reports", "$1,000–5,000/yr", "NGOs, Research", "⏳ Stage 2"),
        ("API Access", "$5,000–20,000/yr", "Agribusinesses", "⏳ Stage 2"),
        ("Custom Deployment", "$20,000–100,000", "Government", "⏳ Stage 3"),
        ("Technical Support", "$500–2,000/yr", "All institutions", "⏳ Stage 2"),
    ],
    top=1.9, height=3.4, col_widths=[3.6, 2.7, 3.6, 2.4], font_size=12
)
add_bullets(s, [
    "",
    "⚠️  Current revenue: $0 — no paying customers yet",
    "🎯  First revenue target: 1 cooperative contract by month 6",
], top=5.5, size=17)

# ============================================================
# SLIDE 10 — Technical Evidence
# ============================================================
s = add_content_slide(
    "Technical Evidence — Verified and Reproducible",
    "Every claim traceable to a report in our GitHub evidence pack"
)
add_bullets(s, [
    "🧠  Model: MobileNetV2, 15 classes across tomato/pepper/potato (v2)",
    "📊  Test accuracy: 95.27% top-1 / 99.48% top-3 on 3,106 held-out images",
    "📊  Macro F1: 0.9508  |  Weighted F1: 0.9529",
    "🔁  Byte-for-byte reproducible evaluation (SHA256 verified across rerun)",
    "📂  Training data: 20,669 PlantVillage-derived images",
    "📂  Ethiopian field-verified images: 0 (documented)",
    "🚀  Deployed: v1 (19 classes) — unchanged since Sept 2026",
    "🚀  Evaluated candidate: v2 (15 classes) — deployment requires UI crop selection",
], top=2.0, size=17)

# ============================================================
# SLIDE 11 — Phase 2 Roadmap
# ============================================================
s = add_content_slide(
    "Phase 2 Roadmap — What We'll Do With EAII Support",
    "Next 6 months, one milestone at a time"
)
add_bullets(s, [
    "📅  Month 1–2: Field validation with 5–10 extension workers (Oromia)",
    "📅  Month 2–3: Collect 200+ labeled Ethiopian field images (Jimma, Melkassa, Kulumsa, Debre Zeit)",
    "📅  Month 3–4: Expert-validate recommendations (Tier 2) + lab-confirm subset (Tier 3)",
    "📅  Month 4–5: Build cooperative dashboard (aggregate analytics, member management)",
    "📅  Month 5–6: Run field pilot with ONE cooperative (target: 1 paid contract)",
    "",
    "Success at Month 6: 1 paying cooperative + 500+ verified field images + retrained model",
], top=2.2, size=17)

# ============================================================
# SLIDE 12 — The Ask
# ============================================================
s = add_content_slide(
    "The Ask",
    "What we need from EAII to move from MVP to validated startup"
)
add_bullets(s, [
    "🤖  AI/ML mentorship + HPC resources  —  retrain on Ethiopian field data",
    "🌾  Agronomy expertise  —  validate treatment recommendations (Tier 2)",
    "🤝  Field partnerships  —  access to cooperatives through 5 partner ARCs",
    "💼  Business mentorship  —  pricing validation, pilot design",
    "💰  Funding & connections  —  dataset collection, pilot deployment",
    "",
    "Our next milestones:",
    "  1. Field validation with extension workers  →  2. Collect 500+ Ethiopian images",
    "  →  3. Retrain model  →  4. Run cooperative pilot  →  5. First paid contract",
], top=2.2, size=18)

# ============================================================
# SLIDE 13 — Closing
# ============================================================
add_title_slide(
    "We start with disease diagnosis.",
    "We become Ethiopia's agricultural intelligence infrastructure.",
    "AgriMind-Ethiopia\n"
    "From field images to localized agricultural decisions.\n"
    "Founder: Fethu Mohammed  •  EAII AI Startup Support Program — 2026 Cohort II"
)

# ============================================================
# Save
# ============================================================
output = r"C:\projects\AgriMind-Ethiopia\AgriMind-EAII-Idea-Stage-Deck_v2_HONEST.pptx"
prs.save(output)
print(f"\n✅ Pitch deck saved: {output}")
print(f"   Slides: {len(prs.slides)}")
print(f"   File size will be reported by Windows")
print("\nNext: open in PowerPoint, review, then export to PDF")