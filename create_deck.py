from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# ============================================================
# DESIGN SYSTEM
# ============================================================
NAVY = RGBColor(0x12, 0x3B, 0x4A)
GREEN = RGBColor(0x2E, 0x7D, 0x5B)
GOLD = RGBColor(0xD4, 0x9A, 0x3A)
CREAM = RGBColor(0xF7, 0xF5, 0xEE)
DARK = RGBColor(0x17, 0x23, 0x26)
MUTED = RGBColor(0x5D, 0x6A, 0x6E)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
RED = RGBColor(0xB8, 0x4C, 0x4C)

FONT = "Calibri"

# ============================================================
# CREATE PRESENTATION
# ============================================================
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

BLANK = prs.slide_layouts[6]


def add_slide():
    return prs.slides.add_slide(BLANK)


def set_bg(slide, color):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_text(slide, text, left, top, width, height,
             font_size=14, bold=False, italic=False,
             color=DARK, align=PP_ALIGN.LEFT, font=FONT,
             line_spacing=1.15):
    txBox = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = line_spacing
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = font
    return txBox


def add_bullets(slide, items, left, top, width, height,
                font_size=13, color=DARK, bullet_color=GREEN,
                line_spacing=1.3, space_after=6):
    txBox = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    tf = txBox.text_frame
    tf.word_wrap = True

    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = line_spacing
        p.space_after = Pt(space_after)

        # Bullet symbol
        run_bullet = p.add_run()
        run_bullet.text = "▸ "
        run_bullet.font.size = Pt(font_size)
        run_bullet.font.color.rgb = bullet_color
        run_bullet.font.bold = True
        run_bullet.font.name = FONT

        # Text
        run_text = p.add_run()
        run_text.text = item
        run_text.font.size = Pt(font_size)
        run_text.font.color.rgb = color
        run_text.font.name = FONT
    return txBox


def add_rect(slide, left, top, width, height,
             fill_color=WHITE, line_color=None, line_width=0):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if line_color:
        shape.line.color.rgb = line_color
        shape.line.width = Pt(line_width)
    else:
        shape.line.fill.background()
    return shape


def add_table(slide, data, left, top, width, height,
              header_color=GREEN, header_text_color=WHITE,
              font_size=11, header_size=11):
    rows = len(data)
    cols = len(data[0])
    table_shape = slide.shapes.add_table(
        rows, cols, Inches(left), Inches(top), Inches(width), Inches(height)
    )
    table = table_shape.table

    for r, row_data in enumerate(data):
        for c, cell_text in enumerate(row_data):
            cell = table.cell(r, c)
            cell.text = str(cell_text)
            cell.margin_left = Inches(0.05)
            cell.margin_right = Inches(0.05)
            cell.margin_top = Inches(0.03)
            cell.margin_bottom = Inches(0.03)

            for paragraph in cell.text_frame.paragraphs:
                paragraph.alignment = PP_ALIGN.LEFT
                for run in paragraph.runs:
                    run.font.name = FONT
                    if r == 0:
                        run.font.size = Pt(header_size)
                        run.font.bold = True
                        run.font.color.rgb = header_text_color
                    else:
                        run.font.size = Pt(font_size)
                        run.font.color.rgb = DARK

            if r == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = header_color
            else:
                cell.fill.solid()
                cell.fill.fore_color.rgb = WHITE
    return table


def add_notes(slide, text):
    notes_slide = slide.notes_slide
    notes_slide.notes_text_frame.text = text


# ============================================================
# SLIDE 1 — COVER
# ============================================================
s = add_slide()
set_bg(s, NAVY)

# Green accent bar
accent = s.shapes.add_shape(
    MSO_SHAPE.RECTANGLE, Inches(0.7), Inches(1.5), Inches(0.1), Inches(1.2)
)
accent.fill.solid()
accent.fill.fore_color.rgb = GREEN
accent.line.fill.background()

add_text(s, "AgriMind-Ethiopia", 1.0, 1.4, 11, 1.0,
         font_size=48, bold=True, color=WHITE)
add_text(s, "From Disease Diagnosis to African Agricultural Intelligence",
         1.0, 2.5, 11, 0.6,
         font_size=20, color=RGBColor(0xD8, 0xE8, 0xE2))

add_text(s, "Founder & Technical Lead: Fethu Mohammed",
         1.0, 4.3, 11, 0.4,
         font_size=16, bold=True, color=GOLD)
add_text(s, "EAII AI Startup Support Program — 2026 Cohort II",
         1.0, 4.8, 11, 0.4,
         font_size=13, color=RGBColor(0xC4, 0xD6, 0xD2))
add_text(s, "Idea Stage Working Document",
         1.0, 5.2, 11, 0.4,
         font_size=13, color=RGBColor(0xC4, 0xD6, 0xD2))
add_text(s, "Current Stage: Working MVP • Early Ethiopian Dataset • Validation Phase",
         1.0, 5.8, 11, 0.4,
         font_size=12, italic=True, color=RGBColor(0xC4, 0xD6, 0xD2))

add_notes(s, "AgriMind is not just a disease diagnosis app. We are building agricultural intelligence infrastructure for Ethiopia and Africa. Today, we diagnose crop diseases. Tomorrow, we power the entire agricultural ecosystem.")


# ============================================================
# SLIDE 2 — VISION
# ============================================================
s = add_slide()
set_bg(s, CREAM)

add_text(s, "OUR VISION", 0.7, 0.5, 12, 0.4,
         font_size=12, bold=True, color=GREEN)
add_text(s, "What We Are Building", 0.7, 0.9, 12, 0.7,
         font_size=32, bold=True, color=NAVY)

# Vision box
box = add_rect(s, 1.5, 2.2, 10.3, 3.5, fill_color=NAVY)

add_text(s, "\"AgriMind-Ethiopia is building the AI-powered\nagricultural intelligence infrastructure\nthat helps every Ethiopian farmer make\nbetter decisions — from disease diagnosis\nto market access — using localized data,\nexpert knowledge, and accessible technology.\"",
         1.8, 2.6, 9.7, 3.0,
         font_size=20, italic=True, color=WHITE, align=PP_ALIGN.CENTER,
         line_spacing=1.4)

add_notes(s, "This is our north star. Every decision we make — every feature, every partnership, every hire — must move us closer to this vision.")


# ============================================================
# SLIDE 3 — EVOLUTION PATH
# ============================================================
s = add_slide()
set_bg(s, CREAM)

add_text(s, "OUR EVOLUTION PATH", 0.7, 0.5, 12, 0.4,
         font_size=12, bold=True, color=GREEN)
add_text(s, "From MVP to Continental Infrastructure", 0.7, 0.9, 12, 0.7,
         font_size=30, bold=True, color=NAVY)

data = [
    ["Stage", "Timeline", "What We Become", "Key Output"],
    ["Stage 1", "Now", "AI Crop Diagnosis App", "Disease detection"],
    ["Stage 2", "Year 1-2", "Agricultural Intelligence Platform", "Decision support"],
    ["Stage 3", "Year 3-5", "Full Ecosystem Platform", "Farm operating system"],
    ["Stage 4", "Year 5-10", "African Agricultural Infrastructure", "Continental intelligence"],
]
add_table(s, data, 0.7, 2.0, 12, 3.0)

add_text(s, "\"We don't build everything at once. We build one layer, validate it, then expand.\"",
         0.7, 5.5, 12, 0.5,
         font_size=14, italic=True, color=GREEN, align=PP_ALIGN.CENTER)

add_notes(s, "We don't try to build everything at once. We focus on one stage, validate it, then expand.")


# ============================================================
# SLIDE 4 — STAGE 1
# ============================================================
s = add_slide()
set_bg(s, CREAM)

add_text(s, "STAGE 1", 0.7, 0.5, 12, 0.4,
         font_size=12, bold=True, color=GREEN)
add_text(s, "AI Crop Diagnosis — Where We Are Today", 0.7, 0.9, 12, 0.7,
         font_size=28, bold=True, color=NAVY)
add_text(s, "Month 0-6 • 3-person team • Working MVP", 0.7, 1.6, 12, 0.4,
         font_size=13, italic=True, color=MUTED)

# What we are box
add_rect(s, 0.7, 2.2, 5.8, 3.8, fill_color=WHITE)
add_text(s, "What We Are", 0.9, 2.35, 5.4, 0.4,
         font_size=14, bold=True, color=NAVY)
add_text(s, "A focused AI software company building one thing extremely well — image-based crop disease diagnosis for Ethiopian farmers.",
         0.9, 2.8, 5.4, 2.5,
         font_size=12, color=DARK, line_spacing=1.3)

# Services box
add_rect(s, 6.8, 2.2, 5.8, 3.8, fill_color=WHITE)
add_text(s, "What We Provide", 7.0, 2.35, 5.4, 0.4,
         font_size=14, bold=True, color=NAVY)
services = [
    "✅ AI Disease Diagnosis (farmers, free)",
    "✅ Treatment Recommendations",
    "✅ Prediction History",
    "✅ 3 Languages (EN/AM/OM)",
    "✅ Mobile + Web App",
    "🔲 Cooperative Dashboard (Month 3)",
    "🔲 API Access (Month 4)",
]
add_bullets(s, services, 7.0, 2.8, 5.4, 2.5,
            font_size=11, bullet_color=GREEN, space_after=3)

add_text(s, "Success Metric: \"A farmer photographs a diseased crop and gets an accurate diagnosis in their own language within 3 seconds.\"",
         0.7, 6.3, 12, 0.5,
         font_size=12, italic=True, color=GREEN, align=PP_ALIGN.CENTER)

add_notes(s, "Today we have a working MVP. Farmers take photos, get diagnoses, and receive treatment recommendations in their own language. Our next milestone is the cooperative dashboard and API.")


# ============================================================
# SLIDE 5 — STAGE 2
# ============================================================
s = add_slide()
set_bg(s, CREAM)

add_text(s, "STAGE 2", 0.7, 0.5, 12, 0.4,
         font_size=12, bold=True, color=GREEN)
add_text(s, "Agricultural Intelligence Platform", 0.7, 0.9, 12, 0.7,
         font_size=30, bold=True, color=NAVY)
add_text(s, "Year 1-2 • 15-person team • $100K revenue", 0.7, 1.6, 12, 0.4,
         font_size=13, italic=True, color=MUTED)

data = [
    ["Category", "New Services We Add"],
    ["Crop Health", "Pest ID, Nutrient Deficiency, Severity Assessment"],
    ["Weather", "Local Forecast, Disease Risk Alerts, Irrigation Guidance"],
    ["Advisory", "Planting Calendar, Fertilizer Advice, Crop Rotation"],
    ["Institutional", "Dashboard, Heatmaps, Early Warning, Analytics, API"],
    ["Communication", "SMS Diagnosis, Voice Assistant, Offline Mode, Expert Chat"],
]
add_table(s, data, 0.7, 2.2, 12, 3.0, font_size=11)

add_text(s, "Success Metric: \"AgriMind is the go-to agricultural intelligence platform for Ethiopian cooperatives, NGOs, and agribusinesses.\"",
         0.7, 5.7, 12, 0.6,
         font_size=13, italic=True, color=GREEN, align=PP_ALIGN.CENTER)

add_notes(s, "Stage 2 is where we expand beyond diagnosis. We add weather, advisory, and institutional services. Our team grows to 15 people. Revenue reaches $100K.")


# ============================================================
# SLIDE 6 — STAGE 3
# ============================================================
s = add_slide()
set_bg(s, CREAM)

add_text(s, "STAGE 3", 0.7, 0.5, 12, 0.4,
         font_size=12, bold=True, color=GREEN)
add_text(s, "Full Ecosystem Platform", 0.7, 0.9, 12, 0.7,
         font_size=32, bold=True, color=NAVY)
add_text(s, "Year 3-5 • 50-person team • $1.2M revenue • 3 countries", 0.7, 1.6, 12, 0.4,
         font_size=13, italic=True, color=MUTED)

data = [
    ["Category", "New Services We Add"],
    ["Farm Management", "Farm Profile, Crop Tracking, Yield Prediction, Carbon Tracking"],
    ["Market Access", "Market Prices, Price Trends, Buyer Connections, Export"],
    ["Financial", "Loan Eligibility, Insurance, Savings, Payments"],
    ["Supply Chain", "Input Ordering, Mechanization, Logistics, Storage"],
    ["Advanced Tech", "Satellite, Drones, IoT Sensors, AI Automation"],
    ["Knowledge", "Training Platform, Community, Expert Network, Certification"],
]
add_table(s, data, 0.7, 2.2, 12, 3.4, font_size=11)

add_text(s, "Success Metric: \"AgriMind is the operating system for Ethiopian agriculture — connecting 1 million farmers to knowledge, inputs, markets, and finance.\"",
         0.7, 6.0, 12, 0.6,
         font_size=13, italic=True, color=GREEN, align=PP_ALIGN.CENTER)

add_notes(s, "Stage 3 is where we become the operating system for Ethiopian agriculture. We connect farmers to everything they need — knowledge, inputs, markets, and finance.")


# ============================================================
# SLIDE 7 — STAGE 4
# ============================================================
s = add_slide()
set_bg(s, CREAM)

add_text(s, "STAGE 4", 0.7, 0.5, 12, 0.4,
         font_size=12, bold=True, color=GREEN)
add_text(s, "African Agricultural Intelligence Infrastructure", 0.7, 0.9, 12, 0.7,
         font_size=28, bold=True, color=NAVY)
add_text(s, "Year 5-10 • 200+ team • $18.5M revenue • 10+ countries", 0.7, 1.6, 12, 0.4,
         font_size=13, italic=True, color=MUTED)

data = [
    ["Category", "New Services We Add"],
    ["Multi-Country", "Country AI, Regional Analytics, Policy Intelligence"],
    ["Continental Data", "African Crop Dataset, Disease Surveillance, Climate Data"],
    ["Government", "National Dashboards, Food Security Alerts, Policy Recommendations"],
    ["Enterprise", "White-Label, Research API, Insurance Integration"],
    ["Technology", "Open Source Models, African Language AI, Edge AI"],
]
add_table(s, data, 0.7, 2.2, 12, 3.0, font_size=11)

add_text(s, "Success Metric: \"AgriMind is the agricultural intelligence infrastructure for Africa — powering food security for 100 million farmers.\"",
         0.7, 5.7, 12, 0.6,
         font_size=13, italic=True, color=GREEN, align=PP_ALIGN.CENTER)

add_notes(s, "Stage 4 is continental scale. We power agricultural intelligence across Africa. Our data becomes the reference for food security.")


# ============================================================
# SLIDE 8 — EVOLUTION MAP
# ============================================================
s = add_slide()
set_bg(s, CREAM)

add_text(s, "OUR GROWTH AT A GLANCE", 0.7, 0.5, 12, 0.4,
         font_size=12, bold=True, color=GREEN)
add_text(s, "Every Metric, Every Stage", 0.7, 0.9, 12, 0.7,
         font_size=30, bold=True, color=NAVY)

data = [
    ["Dimension", "Stage 1 (Now)", "Stage 2 (Y1-2)", "Stage 3 (Y3-5)", "Stage 4 (Y5-10)"],
    ["Organization", "AI software", "Ag intelligence", "Full-stack agtech", "Continental infra"],
    ["Core Product", "Diagnosis", "Decision support", "Farm OS", "Ag intelligence"],
    ["Services", "1", "15+", "50+", "100+"],
    ["Disease Classes", "19", "50+", "100+", "200+"],
    ["Crops", "6", "15", "30", "50+"],
    ["Languages", "3", "6", "12", "30+"],
    ["Countries", "1", "1", "3", "10+"],
    ["Farmers", "100", "50K", "1M", "10M+"],
    ["Team", "3", "15", "50", "200+"],
    ["Revenue", "$0", "$100K", "$1.2M", "$18M+"],
]
add_table(s, data, 0.4, 1.9, 12.5, 4.8, font_size=10, header_size=10)

add_notes(s, "This is our full evolution map. Every dimension scales — services, crops, languages, countries, farmers, team, and revenue.")


# ============================================================
# SLIDE 9 — WHAT WE ARE BUILDING
# ============================================================
s = add_slide()
set_bg(s, CREAM)

add_text(s, "WHAT WE ARE REALLY BUILDING", 0.7, 0.5, 12, 0.4,
         font_size=12, bold=True, color=GREEN)
add_text(s, "Not What You Think", 0.7, 0.9, 12, 0.7,
         font_size=30, bold=True, color=NAVY)

# NOT box
add_rect(s, 0.7, 2.0, 5.8, 3.8, fill_color=RGBColor(0xF8, 0xE5, 0xE5))
add_text(s, "We are NOT building:", 0.9, 2.15, 5.4, 0.4,
         font_size=15, bold=True, color=RED)
not_items = [
    "Another agricultural app",
    "A marketplace",
    "A chatbot",
    "A weather app",
    "A farm management tool",
]
add_bullets(s, not_items, 0.9, 2.7, 5.4, 2.8,
            font_size=13, bullet_color=RED, space_after=10)

# ARE box
add_rect(s, 6.8, 2.0, 5.8, 3.8, fill_color=RGBColor(0xE5, 0xF2, 0xEA))
add_text(s, "We ARE building:", 7.0, 2.15, 5.4, 0.4,
         font_size=15, bold=True, color=GREEN)
are_items = [
    "An agricultural intelligence layer that powers everything else",
    "A data flywheel — more farmers → more data → better AI",
    "A platform that other platforms plug into",
    "An infrastructure for Ethiopian and African agriculture",
]
add_bullets(s, are_items, 7.0, 2.7, 5.4, 2.8,
            font_size=12, bullet_color=GREEN, space_after=10)

add_text(s, "\"We don't compete with Lersha, FarmerChat, or ATI. We power them.\"",
         0.7, 6.2, 12, 0.5,
         font_size=14, bold=True, italic=True, color=NAVY,
         align=PP_ALIGN.CENTER)

add_notes(s, "We are not another app. We are the intelligence layer. We don't compete with the ecosystem — we power it.")


# ============================================================
# SLIDE 10 — DATA FLYWHEEL
# ============================================================
s = add_slide()
set_bg(s, CREAM)

add_text(s, "OUR COMPETITIVE MOAT", 0.7, 0.5, 12, 0.4,
         font_size=12, bold=True, color=GREEN)
add_text(s, "Why We Win", 0.7, 0.9, 12, 0.7,
         font_size=32, bold=True, color=NAVY)

# Flywheel boxes
steps = [
    ("Ethiopian\nFarmers", 0.9, 2.2, GREEN),
    ("Field Images\n+ Metadata", 3.0, 2.2, NAVY),
    ("Expert\nValidation", 5.1, 2.2, GREEN),
    ("Better\nAI Model", 7.2, 2.2, NAVY),
    ("Better\nDiagnosis", 9.3, 2.2, GREEN),
    ("More Farmers\nTrust", 0.9, 4.3, NAVY),
    ("More\nData", 3.0, 4.3, GREEN),
    ("Locally\nValidated", 5.1, 4.3, NAVY),
    ("Defensible\nMoat", 7.2, 4.3, GOLD),
    ("Continental\nScale", 9.3, 4.3, GREEN),
]

for text, left, top, color in steps:
    box = add_rect(s, left, top, 2.0, 1.3, fill_color=color)
    add_text(s, text, left + 0.1, top + 0.15, 1.8, 1.0,
             font_size=12, bold=True, color=WHITE,
             align=PP_ALIGN.CENTER)

add_text(s, "\"Global platforms have scale. We have Ethiopian field data. That's a moat they cannot easily copy.\"",
         0.7, 6.2, 12, 0.5,
         font_size=14, bold=True, italic=True, color=NAVY,
         align=PP_ALIGN.CENTER)

add_notes(s, "Our moat is the data flywheel. More farmers create more data, which creates better AI, which attracts more farmers. Global platforms don't have Ethiopian field data.")


# ============================================================
# SLIDE 11 — BUSINESS MODEL
# ============================================================
s = add_slide()
set_bg(s, CREAM)

add_text(s, "HOW WE MAKE MONEY", 0.7, 0.5, 12, 0.4,
         font_size=12, bold=True, color=GREEN)
add_text(s, "B2B + B2B2C Business Model", 0.7, 0.9, 12, 0.7,
         font_size=30, bold=True, color=NAVY)

add_text(s, "For Farmers: Free forever. Disease diagnosis, recommendations, history, 3 languages.",
         0.7, 1.8, 12, 0.4,
         font_size=14, bold=True, color=GREEN)

data = [
    ["Service", "Price Range", "Target Customer"],
    ["Cooperative Dashboard", "$500-5,000/year", "Cooperatives"],
    ["Analytics Reports", "$1,000-5,000/year", "NGOs, Research"],
    ["API Access", "$5,000-20,000/year", "Agribusinesses"],
    ["Custom Deployment", "$20,000-100,000", "Government"],
    ["Technical Support", "$500-2,000/year", "All institutions"],
]
add_table(s, data, 0.7, 2.5, 12, 2.8, font_size=11)

add_text(s, "\"Farmers create impact. Institutions create revenue. Everyone wins.\"",
         0.7, 5.9, 12, 0.5,
         font_size=14, bold=True, italic=True, color=NAVY,
         align=PP_ALIGN.CENTER)

add_notes(s, "Our business model is B2B + B2B2C. Farmers never pay. Cooperatives, NGOs, and agribusinesses pay for dashboards, analytics, and API access.")


# ============================================================
# SLIDE 12 — WHY WE WIN
# ============================================================
s = add_slide()
set_bg(s, CREAM)

add_text(s, "WHY WE WIN", 0.7, 0.5, 12, 0.4,
         font_size=12, bold=True, color=GREEN)
add_text(s, "Our Unfair Advantages", 0.7, 0.9, 12, 0.7,
         font_size=32, bold=True, color=NAVY)

data = [
    ["Advantage", "Why It Matters"],
    ["Ethiopian field data", "Global platforms don't have it"],
    ["Expert validation", "Our labels are scientifically credible"],
    ["Local languages", "EN/AM/OM — farmers understand"],
    ["Cooperative distribution", "Trusted channels already exist"],
    ["B2B + B2B2C model", "Sustainable revenue from institutions"],
    ["Government alignment", "DAR flags Agricultural Intelligence as gap"],
    ["Team commitment", "3 people, full-time, EAII office"],
    ["Clear roadmap", "Month-by-month execution plan"],
]
add_table(s, data, 0.7, 1.9, 12, 4.5, font_size=12)

add_text(s, "\"We are not competing with the ecosystem. We are filling the gap the ecosystem identified.\"",
         0.7, 6.6, 12, 0.5,
         font_size=13, bold=True, italic=True, color=NAVY,
         align=PP_ALIGN.CENTER)

add_notes(s, "We have specific unfair advantages. Ethiopian field data, expert validation, local languages, cooperative distribution. These are hard for global competitors to copy.")


# ============================================================
# SLIDE 13 — THE ASK
# ============================================================
s = add_slide()
set_bg(s, NAVY)

add_text(s, "THE ASK", 0.7, 0.5, 12, 0.4,
         font_size=12, bold=True, color=GOLD)
add_text(s, "What We Need from EAII", 0.7, 0.9, 12, 0.7,
         font_size=32, bold=True, color=WHITE)
add_text(s, "Closing the gaps on our 6-month journey to launch", 0.7, 1.6, 12, 0.4,
         font_size=14, italic=True, color=RGBColor(0xD8, 0xE8, 0xE2))

data = [
    ["#", "What", "Why"],
    ["1", "AI/ML Mentorship + HPC Resources", "Model development, dataset training"],
    ["2", "Agronomy Expertise", "Expert validation, local crop knowledge"],
    ["3", "Field Partnerships", "Cooperatives, extension networks"],
    ["4", "Business Mentorship", "Pricing validation, pilot design"],
    ["5", "Funding & Connections", "Dataset collection, pilot deployment"],
]
add_table(s, data, 0.7, 2.2, 12, 3.0, header_color=GOLD, font_size=12)

add_text(s, "Our Next Milestones:", 0.7, 5.5, 12, 0.4,
         font_size=14, bold=True, color=GOLD)
add_text(s, "Expand Ethiopian Data → Validate with Experts → Run Field Pilots → Build Decision Support → LAUNCH",
         0.7, 5.9, 12, 0.5,
         font_size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

add_notes(s, "We need five things from EAII: AI mentorship, agronomy expertise, field partnerships, business mentorship, and funding. With this support, we can launch a validated Ethiopian agricultural intelligence product in 6 months.")


# ============================================================
# SLIDE 14 — CLOSING
# ============================================================
s = add_slide()
set_bg(s, NAVY)

# Big centered statement
add_text(s, "\"We start with disease diagnosis.",
         1.0, 2.0, 11.3, 0.8,
         font_size=26, bold=True, color=WHITE,
         align=PP_ALIGN.CENTER)
add_text(s, "We become Ethiopia's agricultural intelligence infrastructure.",
         1.0, 2.9, 11.3, 0.8,
         font_size=26, bold=True, color=GOLD,
         align=PP_ALIGN.CENTER)
add_text(s, "We scale to power African agriculture.\"",
         1.0, 3.8, 11.3, 0.8,
         font_size=26, bold=True, color=WHITE,
         align=PP_ALIGN.CENTER)

# Divider
line = s.shapes.add_shape(
    MSO_SHAPE.RECTANGLE, Inches(5.5), Inches(5.0), Inches(2.3), Inches(0.03)
)
line.fill.solid()
line.fill.fore_color.rgb = GOLD
line.line.fill.background()

add_text(s, "AgriMind-Ethiopia", 1.0, 5.3, 11.3, 0.5,
         font_size=22, bold=True, color=WHITE,
         align=PP_ALIGN.CENTER)
add_text(s, "From field images to localized agricultural decisions.",
         1.0, 5.9, 11.3, 0.4,
         font_size=13, italic=True, color=RGBColor(0xD8, 0xE8, 0xE2),
         align=PP_ALIGN.CENTER)
add_text(s, "Founder: Fethu Mohammed  •  EAII AI Startup Support Program — 2026 Cohort II",
         1.0, 6.5, 11.3, 0.4,
         font_size=11, color=RGBColor(0xC4, 0xD6, 0xD2),
         align=PP_ALIGN.CENTER)

add_notes(s, "This is our vision. We are at Idea Stage today, but we have a working MVP, a clear roadmap, and a team committed to launch. We are not building an app — we are building infrastructure. Thank you.")


# ============================================================
# SAVE
# ============================================================
output_path = r"C:\projects\AgriMind-Ethiopia\AgriMind-EAII-Idea-Stage-Deck.pptx"
prs.save(output_path)
print(f"PowerPoint created: {output_path}")
print(f"Total slides: {len(prs.slides)}")