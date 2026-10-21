from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR

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
BLUE = RGBColor(0x2A, 0x5F, 0x8F)
PURPLE = RGBColor(0x6A, 0x4C, 0x93)

FONT = "Calibri"

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
             color=DARK, align=PP_ALIGN.LEFT, line_spacing=1.15):
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
    run.font.name = FONT
    return txBox


def add_box(slide, text, left, top, width, height,
            fill_color=WHITE, text_color=DARK, font_size=12,
            bold=True, line_color=None):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if line_color:
        shape.line.color.rgb = line_color
        shape.line.width = Pt(2)
    else:
        shape.line.fill.background()

    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.05)
    tf.margin_right = Inches(0.05)
    tf.margin_top = Inches(0.05)
    tf.margin_bottom = Inches(0.05)

    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.line_spacing = 1.1
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = text_color
    run.font.name = FONT
    return shape


def add_arrow(slide, x1, y1, x2, y2, color=GOLD):
    connector = slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT,
        Inches(x1), Inches(y1), Inches(x2), Inches(y2)
    )
    connector.line.color.rgb = color
    connector.line.width = Pt(3)
    return connector


def add_notes(slide, text):
    notes_slide = slide.notes_slide
    notes_slide.notes_text_frame.text = text


# ============================================================
# SLIDE 1 — MULTI-MODAL ARCHITECTURE
# ============================================================
s = add_slide()
set_bg(s, CREAM)

# Title
add_text(s, "MULTI-MODAL AI ARCHITECTURE", 0.7, 0.3, 12, 0.4,
         font_size=12, bold=True, color=GREEN)
add_text(s, "Image + Environmental Context = Accurate Diagnosis",
         0.7, 0.65, 12, 0.6,
         font_size=26, bold=True, color=NAVY)

# ============ INPUTS SECTION (Left) ============

# Section label
add_text(s, "INPUTS", 0.5, 1.6, 3, 0.35,
         font_size=11, bold=True, color=MUTED)

# Input box 1 — Image
add_box(s, "📷 Leaf Image\n(Visual Symptoms)", 0.5, 2.1, 2.5, 0.9,
        fill_color=WHITE, text_color=DARK, font_size=11, line_color=BLUE)
add_text(s, "CNN / Vision Model\nMobileNetV2 / EfficientNet",
         0.5, 3.05, 2.5, 0.5,
         font_size=9, italic=True, color=BLUE, align=PP_ALIGN.CENTER)

# Input box 2 — Environmental
add_box(s, "🌍 Environmental Data\nGPS • Altitude • Weather\nHumidity • Rainfall • Soil",
        0.5, 3.9, 2.5, 1.2,
        fill_color=WHITE, text_color=DARK, font_size=10, line_color=GREEN)
add_text(s, "Tabular Model\nFeedforward Network",
         0.5, 5.15, 2.5, 0.5,
         font_size=9, italic=True, color=GREEN, align=PP_ALIGN.CENTER)

# Input box 3 — Context
add_box(s, "🌱 Crop Context\nCrop Type • Growth Stage\nFarmer Input",
        0.5, 5.85, 2.5, 1.0,
        fill_color=WHITE, text_color=DARK, font_size=10, line_color=PURPLE)

# ============ FUSION LAYER (Center) ============

add_text(s, "FUSION", 4.0, 1.6, 3, 0.35,
         font_size=11, bold=True, color=MUTED)

# Feature extraction boxes
add_box(s, "Image\nFeatures", 4.0, 2.3, 1.6, 0.8,
        fill_color=BLUE, text_color=WHITE, font_size=11)
add_box(s, "Environmental\nFeatures", 4.0, 4.0, 1.6, 0.8,
        fill_color=GREEN, text_color=WHITE, font_size=11)
add_box(s, "Context\nFeatures", 4.0, 5.5, 1.6, 0.8,
        fill_color=PURPLE, text_color=WHITE, font_size=11)

# Fusion layer box
fusion = add_box(s, "🔗\nFUSION LAYER\n\nAttention-Based\nFeature Combination",
                 6.2, 3.0, 2.2, 2.6,
                 fill_color=NAVY, text_color=WHITE, font_size=13)

# Arrows from inputs to fusion
add_arrow(s, 3.0, 2.55, 4.0, 2.7, BLUE)     # Image to features
add_arrow(s, 3.0, 4.5, 4.0, 4.4, GREEN)      # Env to features
add_arrow(s, 3.0, 6.3, 4.0, 5.9, PURPLE)     # Context to features

add_arrow(s, 5.6, 2.7, 6.2, 3.8, GOLD)       # Image feat to fusion
add_arrow(s, 5.6, 4.4, 6.2, 4.3, GOLD)       # Env feat to fusion
add_arrow(s, 5.6, 5.9, 6.2, 4.9, GOLD)       # Context feat to fusion

# ============ OUTPUT SECTION (Right) ============

add_text(s, "OUTPUT", 9.0, 1.6, 3, 0.35,
         font_size=11, bold=True, color=MUTED)

# Output boxes
add_box(s, "Disease\nDiagnosis", 9.0, 2.3, 3.5, 0.8,
        fill_color=GREEN, text_color=WHITE, font_size=13)
add_box(s, "Confidence\nScore", 9.0, 3.3, 3.5, 0.8,
        fill_color=GOLD, text_color=WHITE, font_size=13)
add_box(s, "Treatment\nRecommendation", 9.0, 4.3, 3.5, 0.8,
        fill_color=NAVY, text_color=WHITE, font_size=13)
add_box(s, "Expert\nEscalation", 9.0, 5.3, 3.5, 0.8,
        fill_color=RED, text_color=WHITE, font_size=13)

# Arrow from fusion to outputs
add_arrow(s, 8.4, 4.3, 9.0, 2.7, GOLD)
add_arrow(s, 8.4, 4.3, 9.0, 3.7, GOLD)
add_arrow(s, 8.4, 4.3, 9.0, 4.7, GOLD)
add_arrow(s, 8.4, 4.3, 9.0, 5.7, GOLD)

# Bottom statement
add_text(s, "\"Research from Jimma University shows multi-modal diagnosis achieves 98% accuracy — vs. 94% for image-only.\"",
         0.5, 7.0, 12.3, 0.4,
         font_size=11, italic=True, color=NAVY, align=PP_ALIGN.CENTER)

add_notes(s, "This is our multi-modal architecture. We combine leaf images with environmental context — GPS, altitude, weather, crop type, and growth stage. A fusion layer combines these signals to produce a diagnosis that is far more accurate than image alone. This is scientifically validated by Ethiopian research.")


# ============================================================
# SAVE
# ============================================================
output_path = r"C:\projects\AgriMind-Ethiopia\AgriMind-MultiModal-Architecture.pptx"
prs.save(output_path)
print(f"PowerPoint created: {output_path}")
print(f"Total slides: {len(prs.slides)}")