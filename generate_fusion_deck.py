"""
AgriMind-Ethiopia — CNN + Contextual Fusion Architecture Deck
27 slides covering all 12 sections of the technical guidance.
Output: C:\\Users\\justice\\OneDrive\\Documents\\AgriMind-Ethiopia\\AgriMind_Fusion_Architecture_Guide.pptx

Run: python generate_fusion_deck.py
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pathlib import Path

# ==================== CONFIG ====================
OUTPUT_DIR = Path(r"C:\Users\justice\OneDrive\Documents\AgriMind-Ethiopia")
OUTPUT_FILE = OUTPUT_DIR / "AgriMind_Fusion_Architecture_Guide.pptx"

# Color palette
GREEN_DARK = RGBColor(0x1B, 0x5E, 0x20)
GREEN_PRIMARY = RGBColor(0x2E, 0x7D, 0x32)
GREEN_MID = RGBColor(0x66, 0xBB, 0x6A)
GREEN_LIGHT = RGBColor(0xC8, 0xE6, 0xC9)
GREEN_PALE = RGBColor(0xE8, 0xF5, 0xE9)
ORANGE_ACCENT = RGBColor(0xE6, 0x5C, 0x00)
ORANGE_LIGHT = RGBColor(0xFF, 0xE0, 0xB2)
PURPLE = RGBColor(0x7B, 0x1F, 0xA2)
PURPLE_PALE = RGBColor(0xF3, 0xE5, 0xF5)
BLUE_INFO = RGBColor(0x19, 0x76, 0xD2)
BLUE_PALE = RGBColor(0xE3, 0xF2, 0xFD)
RED_WARN = RGBColor(0xC6, 0x28, 0x28)
RED_PALE = RGBColor(0xFF, 0xEB, 0xEE)
CODE_BG = RGBColor(0x1E, 0x1E, 0x1E)
CODE_TEXT = RGBColor(0xE8, 0xE8, 0xE8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
TEXT_DARK = RGBColor(0x21, 0x21, 0x21)
TEXT_GRAY = RGBColor(0x61, 0x61, 0x61)
BORDER_LIGHT = RGBColor(0xE0, 0xE0, 0xE0)

# ==================== HELPERS ====================

def new_slide(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def add_bg_bar(slide, color=GREEN_PRIMARY, height=0.12):
    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(height))
    bar.fill.solid(); bar.fill.fore_color.rgb = color
    bar.line.fill.background()


def add_title(slide, title, subtitle=None, color=GREEN_DARK):
    accent = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(0.45),
        Inches(0.08), Inches(0.75))
    accent.fill.solid(); accent.fill.fore_color.rgb = GREEN_PRIMARY
    accent.line.fill.background()

    tb = slide.shapes.add_textbox(Inches(0.75), Inches(0.4),
                                    Inches(12.0), Inches(0.85))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.text = title; p.alignment = PP_ALIGN.LEFT
    for run in p.runs:
        run.font.size = Pt(26); run.font.bold = True
        run.font.color.rgb = color; run.font.name = "Calibri"

    if subtitle:
        tb2 = slide.shapes.add_textbox(Inches(0.75), Inches(1.22),
                                          Inches(12.0), Inches(0.42))
        tf2 = tb2.text_frame; tf2.word_wrap = True
        p2 = tf2.paragraphs[0]; p2.text = subtitle
        for run in p2.runs:
            run.font.size = Pt(13); run.font.italic = True
            run.font.color.rgb = TEXT_GRAY; run.font.name = "Calibri"


def add_footer(slide, page_num=None, total=27):
    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, Inches(7.28),
        Inches(13.333), Inches(0.22))
    bar.fill.solid(); bar.fill.fore_color.rgb = GREEN_PALE
    bar.line.fill.background()

    tb = slide.shapes.add_textbox(Inches(0.5), Inches(7.3),
                                    Inches(8.0), Inches(0.2))
    tf = tb.text_frame
    p = tf.paragraphs[0]
    p.text = "AgriMind-Ethiopia  |  CNN + Fusion Architecture  |  2026"
    for run in p.runs:
        run.font.size = Pt(9); run.font.color.rgb = TEXT_GRAY
        run.font.name = "Calibri"

    if page_num:
        tb2 = slide.shapes.add_textbox(Inches(12.0), Inches(7.3),
                                         Inches(1.0), Inches(0.2))
        tf2 = tb2.text_frame
        p2 = tf2.paragraphs[0]
        p2.text = f"{page_num} / {total}"
        p2.alignment = PP_ALIGN.RIGHT
        for run in p2.runs:
            run.font.size = Pt(9); run.font.color.rgb = TEXT_GRAY
            run.font.name = "Calibri"


def add_bullets(slide, items, left=0.75, top=1.8, width=12.0,
                height=5.2, size=14):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top),
                                    Inches(width), Inches(height))
    tf = tb.text_frame; tf.word_wrap = True
    first = True
    for item in items:
        if isinstance(item, tuple):
            lvl, text = item
            try:
                level = int(lvl) if lvl not in (None, "") else 0
            except (ValueError, TypeError):
                level = 0
        else:
            level, text = 0, item

        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.level = level
        bullet = "• " if level == 0 else ("◦ " if level == 1 else "▪ ")
        p.text = bullet + text
        p.space_after = Pt(6); p.space_before = Pt(2)
        for run in p.runs:
            run.font.size = Pt(size if level == 0 else size - 2)
            run.font.color.rgb = TEXT_DARK if level == 0 else TEXT_GRAY
            run.font.name = "Calibri"


def add_code_block(slide, code, left=0.75, top=1.8, width=11.8,
                    height=5.2, size=10):
    box = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top),
        Inches(width), Inches(height))
    box.fill.solid(); box.fill.fore_color.rgb = CODE_BG
    box.line.color.rgb = RGBColor(0x33, 0x33, 0x33)
    box.line.width = Pt(0.75)

    tb = slide.shapes.add_textbox(
        Inches(left + 0.15), Inches(top + 0.12),
        Inches(width - 0.3), Inches(height - 0.24))
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = Emu(0); tf.margin_right = Emu(0)
    tf.margin_top = Emu(0); tf.margin_bottom = Emu(0)
    first = True
    for line in code.split("\n"):
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.text = line if line else " "
        p.space_after = Pt(0); p.space_before = Pt(0)
        p.line_spacing = 1.05
        for run in p.runs:
            run.font.size = Pt(size); run.font.name = "Consolas"
            run.font.color.rgb = CODE_TEXT


def add_box(slide, left, top, width, height, text, fill,
            text_color=WHITE, font_size=12, bold=True,
            shape=MSO_SHAPE.ROUNDED_RECTANGLE, border_color=None):
    shp = slide.shapes.add_shape(shape, Inches(left), Inches(top),
                                    Inches(width), Inches(height))
    shp.fill.solid(); shp.fill.fore_color.rgb = fill
    if border_color:
        shp.line.color.rgb = border_color; shp.line.width = Pt(1.5)
    else:
        shp.line.color.rgb = fill; shp.line.width = Pt(0.5)

    tf = shp.text_frame
    tf.margin_left = Inches(0.05); tf.margin_right = Inches(0.05)
    tf.margin_top = Inches(0.02); tf.margin_bottom = Inches(0.02)
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    p.text = text
    for run in p.runs:
        run.font.size = Pt(font_size); run.font.bold = bold
        run.font.color.rgb = text_color; run.font.name = "Calibri"
    return shp


def add_arrow(slide, left, top, width, height=0.25, color=GREEN_PRIMARY):
    arr = slide.shapes.add_shape(
        MSO_SHAPE.RIGHT_ARROW, Inches(left), Inches(top),
        Inches(width), Inches(height))
    arr.fill.solid(); arr.fill.fore_color.rgb = color
    arr.line.fill.background()


def add_down_arrow(slide, left, top, width=0.3, height=0.4, color=GREEN_PRIMARY):
    arr = slide.shapes.add_shape(
        MSO_SHAPE.DOWN_ARROW, Inches(left), Inches(top),
        Inches(width), Inches(height))
    arr.fill.solid(); arr.fill.fore_color.rgb = color
    arr.line.fill.background()


def add_callout(slide, text, top=6.2, height=0.75,
                  fill=BLUE_PALE, border=BLUE_INFO, text_color=TEXT_DARK):
    box = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.75), Inches(top),
        Inches(11.8), Inches(height))
    box.fill.solid(); box.fill.fore_color.rgb = fill
    box.line.color.rgb = border; box.line.width = Pt(2)
    tf = box.text_frame; tf.word_wrap = True
    tf.margin_left = Inches(0.3); tf.margin_right = Inches(0.3)
    tf.margin_top = Inches(0.1); tf.margin_bottom = Inches(0.1)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.text = text
    for run in p.runs:
        run.font.size = Pt(12); run.font.color.rgb = text_color
        run.font.name = "Calibri"


def add_number_badge(slide, num, left, top, color=GREEN_PRIMARY, size=0.55):
    badge = slide.shapes.add_shape(
        MSO_SHAPE.OVAL, Inches(left), Inches(top),
        Inches(size), Inches(size))
    badge.fill.solid(); badge.fill.fore_color.rgb = color
    badge.line.fill.background()
    tf = badge.text_frame
    tf.margin_left = Emu(0); tf.margin_right = Emu(0)
    tf.margin_top = Emu(0); tf.margin_bottom = Emu(0)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    p.text = str(num)
    for run in p.runs:
        run.font.size = Pt(18); run.font.bold = True
        run.font.color.rgb = WHITE; run.font.name = "Calibri"


# ==================== SLIDE BUILDERS ====================

def slide_01_title(prs):
    s = new_slide(prs)
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0,
                              Inches(13.333), Inches(7.5))
    bg.fill.solid(); bg.fill.fore_color.rgb = GREEN_DARK
    bg.line.fill.background()

    # Decorative circles
    for x, y, d, c in [(10.5, -1.5, 5, GREEN_PRIMARY),
                        (-1.5, 5.5, 4, GREEN_PRIMARY)]:
        circle = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y),
                                       Inches(d), Inches(d))
        circle.fill.solid(); circle.fill.fore_color.rgb = c
        circle.line.fill.background()

    # Top tag
    tb_tag = s.shapes.add_textbox(Inches(0.9), Inches(1.2),
                                     Inches(11.5), Inches(0.4))
    tf = tb_tag.text_frame
    p = tf.paragraphs[0]
    p.text = "TECHNICAL ARCHITECTURE SPECIFICATION"
    for run in p.runs:
        run.font.size = Pt(14); run.font.bold = True
        run.font.color.rgb = GREEN_LIGHT; run.font.name = "Calibri"

    # Main title
    tb = s.shapes.add_textbox(Inches(0.9), Inches(1.9),
                                Inches(11.5), Inches(1.4))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "CNN + Contextual-Data\nFusion Platform"
    for run in p.runs:
        run.font.size = Pt(52); run.font.bold = True
        run.font.color.rgb = WHITE; run.font.name = "Calibri"

    # Subtitle
    tb2 = s.shapes.add_textbox(Inches(0.9), Inches(4.0),
                                  Inches(11.5), Inches(0.7))
    tf2 = tb2.text_frame; tf2.word_wrap = True
    p2 = tf2.paragraphs[0]
    p2.text = "Architecture, Training Plan, and Roadmap"
    for run in p2.runs:
        run.font.size = Pt(24); run.font.color.rgb = GREEN_LIGHT
        run.font.name = "Calibri"

    # Bottom info
    tb3 = s.shapes.add_textbox(Inches(0.9), Inches(5.3),
                                  Inches(11.5), Inches(1.5))
    tf3 = tb3.text_frame; tf3.word_wrap = True
    p3 = tf3.paragraphs[0]
    p3.text = "Prepared for the AgriMind-Ethiopia team and EAII technical verification"
    for run in p3.runs:
        run.font.size = Pt(14); run.font.italic = True
        run.font.color.rgb = GREEN_LIGHT; run.font.name = "Calibri"

    p4 = tf3.add_paragraph()
    p4.text = "\nDate: October 2026"
    for run in p4.runs:
        run.font.size = Pt(12); run.font.color.rgb = GREEN_LIGHT
        run.font.name = "Calibri"


def slide_02_agenda(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "Agenda — 12 Technical Sections",
              "What we will cover in this deck")

    sections = [
        ("1", "Proposed Architecture", "Image + Tabular → Fusion"),
        ("2", "The 512 / 16 Dimensions", "Vector sizes and encoding"),
        ("3", "Fusion Layer Mechanics", "Concatenation and alternatives"),
        ("4", "Paired Data Requirements", "Image + context + verified label"),
        ("5", "Training Strategy", "Image-only → context-only → fusion"),
        ("6", "Uncertainty Handling", "Safety layer and referral"),
        ("7", "Complete Platform", "User → API → Inference → Safety → Results"),
        ("8", "Shared vs Per-Crop", "Modular multi-crop design"),
        ("9", "Risks and Mitigations", "6 identified failure modes"),
        ("10", "Development Roadmap", "10 phased milestones"),
        ("11", "V0 and V1 Scope", "What to build first"),
        ("12", "The Decision", "What to commit to now"),
    ]

    # Two columns
    for i, (num, title, subtitle) in enumerate(sections):
        col = 0 if i < 6 else 1
        row = i if i < 6 else i - 6
        x = 0.75 + col * 6.05
        y = 1.85 + row * 0.8

        add_number_badge(s, num, x, y + 0.05, GREEN_PRIMARY, 0.5)

        tb = s.shapes.add_textbox(Inches(x + 0.65), Inches(y),
                                    Inches(5.2), Inches(0.4))
        tf = tb.text_frame; tf.word_wrap = True
        p = tf.paragraphs[0]; p.text = title
        for run in p.runs:
            run.font.size = Pt(13); run.font.bold = True
            run.font.color.rgb = GREEN_DARK; run.font.name = "Calibri"

        tb2 = s.shapes.add_textbox(Inches(x + 0.65), Inches(y + 0.32),
                                     Inches(5.2), Inches(0.35))
        tf2 = tb2.text_frame; tf2.word_wrap = True
        p2 = tf2.paragraphs[0]; p2.text = subtitle
        for run in p2.runs:
            run.font.size = Pt(11); run.font.color.rgb = TEXT_GRAY
            run.font.name = "Calibri"

    add_footer(s, 2)


def slide_03_proposed_arch(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "1. The Proposed Architecture",
              "Two input paths → fusion → classification")

    # IMAGE PATH (left)
    add_box(s, 0.75, 1.9, 3.5, 0.5, "IMAGE PATH", GREEN_PRIMARY, font_size=14)
    add_box(s, 0.75, 2.5, 3.5, 0.55, "Photograph of a Plant",
            GREEN_PALE, text_color=TEXT_DARK, font_size=12, bold=False)
    add_down_arrow(s, 2.35, 3.1, 0.35, 0.35, GREEN_MID)
    add_box(s, 0.75, 3.5, 3.5, 0.55, "Image Encoder (CNN)",
            GREEN_PRIMARY, font_size=12)
    add_down_arrow(s, 2.35, 4.1, 0.35, 0.35, GREEN_MID)
    add_box(s, 0.75, 4.5, 3.5, 0.65, "Visual Feature Vector\n[512 values]",
            GREEN_LIGHT, text_color=GREEN_DARK, font_size=12)
    add_down_arrow(s, 2.35, 5.2, 0.35, 0.35, GREEN_MID)
    add_arrow(s, 4.3, 5.35, 0.8, 0.25, GREEN_MID)

    # TABULAR PATH (right)
    add_box(s, 9.08, 1.9, 3.5, 0.5, "TABULAR PATH",
            ORANGE_ACCENT, font_size=14)
    add_box(s, 9.08, 2.5, 3.5, 0.55, "Structured Field Data",
            ORANGE_LIGHT, text_color=TEXT_DARK, font_size=12, bold=False)
    add_down_arrow(s, 10.68, 3.1, 0.35, 0.35, ORANGE_ACCENT)
    add_box(s, 9.08, 3.5, 3.5, 0.55, "Context Encoder (MLP)",
            ORANGE_ACCENT, font_size=12)
    add_down_arrow(s, 10.68, 4.1, 0.35, 0.35, ORANGE_ACCENT)
    add_box(s, 9.08, 4.5, 3.5, 0.65, "Context Feature Vector\n[16 values]",
            ORANGE_LIGHT, text_color=ORANGE_ACCENT, font_size=12)
    add_down_arrow(s, 10.68, 5.2, 0.35, 0.35, ORANGE_ACCENT)
    add_arrow(s, 8.28, 5.35, 0.8, 0.25, ORANGE_ACCENT, ) if False else None

    # Left arrow for tabular going left
    arr_left = s.shapes.add_shape(
        MSO_SHAPE.LEFT_ARROW, Inches(8.28), Inches(5.35),
        Inches(0.8), Inches(0.25))
    arr_left.fill.solid(); arr_left.fill.fore_color.rgb = ORANGE_ACCENT
    arr_left.line.fill.background()

    # FUSION LAYER (center bottom)
    add_box(s, 4.9, 5.5, 3.5, 0.65, "FUSION LAYER",
            PURPLE, font_size=15)
    add_down_arrow(s, 6.48, 6.2, 0.35, 0.35, PURPLE)

    # OUTPUT
    add_box(s, 4.9, 6.55, 3.5, 0.55, "Output Classification",
            RED_WARN, font_size=13)

    # Right side caption
    add_callout(s,
        "Two input paths produce learned feature vectors. The fusion layer "
        "combines them into a single prediction. Context does not override "
        "the image automatically — it informs the decision.",
        top=1.9, height=3.3, fill=PURPLE_PALE, border=PURPLE)
    # Actually place it in center-right
    s.shapes[-1].left = Inches(4.6)
    s.shapes[-1].top = Inches(1.9)
    s.shapes[-1].width = Inches(3.9)
    s.shapes[-1].height = Inches(3.3)

    add_footer(s, 3)


def slide_04_why_multimodal(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "1. Why Multimodal Learning",
              "Two kinds of evidence → one decision")

    # Definition box
    box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                              Inches(0.75), Inches(1.85),
                              Inches(11.8), Inches(1.2))
    box.fill.solid(); box.fill.fore_color.rgb = GREEN_PALE
    box.line.color.rgb = GREEN_PRIMARY; box.line.width = Pt(2)
    tf = box.text_frame; tf.word_wrap = True
    tf.margin_left = Inches(0.3); tf.margin_right = Inches(0.3)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.text = ("Multimodal learning = learning from two or more different kinds of input. "
              "Here: images (pixels) + structured context (field observations). "
              "Each modality contributes evidence the other cannot provide alone.")
    for run in p.runs:
        run.font.size = Pt(13); run.font.color.rgb = TEXT_DARK
        run.font.name = "Calibri"

    # Why it helps
    add_box(s, 0.75, 3.2, 5.9, 0.5, "IMAGE ALONE CAN BE AMBIGUOUS",
            ORANGE_ACCENT, font_size=13)
    add_bullets(s, [
        "Yellow streaks on wheat leaf could be: nitrogen deficiency, septoria, or stripe rust",
        "Visual symptoms overlap between diseases",
        "No single photograph captures the full diagnosis context",
        "Confidence drops when visual evidence is weak",
    ], left=0.75, top=3.8, width=5.9, height=2.2, size=12)

    # Why fusion helps
    add_box(s, 6.8, 3.2, 5.9, 0.5, "IMAGE + CONTEXT SHARPENS DECISION",
            PURPLE, font_size=13)
    add_bullets(s, [
        "Add: crop = wheat, altitude = 2,400m, humidity = 90%, variety = Kulumsa",
        "Add: season = Belg, growth stage = flowering",
        "Fusion learns which context combinations support each diagnosis",
        "Result: stripe rust at 92% instead of uncertain",
    ], left=6.8, top=3.8, width=5.9, height=2.2, size=12)

    # Warning
    add_callout(s,
        "⚠ Context must inform, not override. A disease can occur outside its "
        "usual range, and symptoms overlap. The system must be able to report "
        "uncertainty rather than force a diagnosis.",
        top=6.2, height=0.85, fill=RED_PALE, border=RED_WARN)

    add_footer(s, 4)


def slide_05_visual_features(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "2. The 512 Visual Features — Where They Come From",
              "CNN backbone output as a learned representation")

    add_bullets(s, [
        "A pretrained CNN (MobileNetV2, ResNet50, EfficientNet) processes the image",
        "Each layer extracts progressively richer patterns: edges → textures → disease signatures",
        "The final layer outputs a 512- (or 1280-, or 2048-) dimensional vector",
        "This vector is a compressed numerical 'fingerprint' of the image",
        "The vector is learned during training, not hand-engineered",
        "512 is a reasonable default — but other sizes work equally well",
    ], top=1.9, size=13, height=2.5)

    # Code block
    code = '''import torch
from torchvision import models, transforms
from PIL import Image

# Load pretrained MobileNetV2
backbone = models.mobilenet_v2(
    weights=models.MobileNet_V2_Weights.IMAGENET1K_V1
).features

# Preprocessing (ImageNet normalization)
tf = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225]),
])

# Extract the 1280-d feature vector (MobileNetV2 default)
image = tf(Image.open("leaf.jpg").convert("RGB")).unsqueeze(0)
with torch.no_grad():
    features = backbone(image)              # (1, 1280, 7, 7)
    pooled = features.mean(dim=[2, 3])      # (1, 1280)
    # Optional: project to 512
    projection = torch.nn.Linear(1280, 512)
    visual_vector = projection(pooled)      # (1, 512)'''

    add_code_block(s, code, top=4.5, height=2.5, size=10)

    add_footer(s, 5)


def slide_06_contextual_features(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "2. The 16 Contextual Features — Field Observation Schema",
              "What a DA records during a field visit")

    # Two columns of fields
    left_fields = [
        ("Crop", "e.g., wheat"),
        ("Plant part", "leaf / berry / whole plant"),
        ("Growth stage", "vegetative / flowering / fruiting"),
        ("Region", "Oromia"),
        ("Collection date", "seasonal context"),
        ("Variety", "Kulumsa, Kingbird"),
        ("Recent rainfall", "recorded or unavailable"),
        ("Temperature", "recorded or unavailable"),
    ]
    right_fields = [
        ("Relative humidity", "recorded or unavailable"),
        ("Symptom duration", "~1 week"),
        ("Symptom distribution", "scattered / clustered"),
        ("Image quality", "acceptable / poor"),
        ("Expert verification", "pending / verified"),
        ("Source of observation", "DA field visit"),
        ("Data completeness", "partial / full"),
        ("Other verified context", "optional field notes"),
    ]

    add_box(s, 0.75, 1.9, 5.9, 0.4, "COMMON FIELDS",
            GREEN_PRIMARY, font_size=12)

    y = 2.4
    for label, example in left_fields:
        add_box(s, 0.75, y, 2.4, 0.42, label, GREEN_PALE,
                text_color=TEXT_DARK, font_size=10, bold=True,
                shape=MSO_SHAPE.RECTANGLE)
        add_box(s, 3.2, y, 3.4, 0.42, example, WHITE,
                text_color=TEXT_GRAY, font_size=10, bold=False,
                shape=MSO_SHAPE.RECTANGLE)
        y += 0.46

    add_box(s, 6.8, 1.9, 5.9, 0.4, "SUPPLEMENTAL FIELDS",
            ORANGE_ACCENT, font_size=12)

    y = 2.4
    for label, example in right_fields:
        add_box(s, 6.8, y, 2.4, 0.42, label, ORANGE_LIGHT,
                text_color=TEXT_DARK, font_size=10, bold=True,
                shape=MSO_SHAPE.RECTANGLE)
        add_box(s, 9.25, y, 3.4, 0.42, example, WHITE,
                text_color=TEXT_GRAY, font_size=10, bold=False,
                shape=MSO_SHAPE.RECTANGLE)
        y += 0.46

    add_callout(s,
        "⚠ 16 is illustrative, not fixed. The final feature count depends on "
        "the schema: one-hot encoding expands categoricals; embeddings compress "
        "them. Define what each feature MEANS before choosing dimensions.",
        top=6.2, height=0.75, fill=BLUE_PALE, border=BLUE_INFO)

    add_footer(s, 6)


def slide_07_data_categories(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "2. The Critical Data Distinction",
              "Three categories — mixing them causes data leakage")

    # Three columns
    cards = [
        ("DIAGNOSTIC\nINPUTS",
         "Available at prediction time",
         [
             "Crop, plant part, growth stage",
             "GPS, altitude, region",
             "Recent weather",
             "Image quality score",
         ],
         GREEN_PRIMARY, GREEN_PALE),
        ("ADMINISTRATIVE\nMETADATA",
         "Records and audit only",
         [
             "Case ID, date created",
             "Collector name",
             "Submission channel",
             "Permissions / consent",
         ],
         BLUE_INFO, BLUE_PALE),
        ("GROUND-TRUTH\nLABELS",
         "Training targets, never inputs",
         [
             "Expert diagnosis",
             "Lab-confirmed result",
             "Verification method",
             "Verification date",
         ],
         RED_WARN, RED_PALE),
    ]

    for i, (title, subtitle, items, color, pale) in enumerate(cards):
        x = 0.75 + i * 4.05
        add_box(s, x, 1.9, 3.75, 0.85, title, color, font_size=13)

        tb = s.shapes.add_textbox(Inches(x), Inches(2.85),
                                    Inches(3.75), Inches(0.4))
        tf = tb.text_frame; tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = subtitle; p.alignment = PP_ALIGN.CENTER
        for run in p.runs:
            run.font.size = Pt(11); run.font.italic = True
            run.font.color.rgb = TEXT_GRAY; run.font.name = "Calibri"

        y = 3.35
        for item in items:
            box = s.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y),
                Inches(3.75), Inches(0.45))
            box.fill.solid(); box.fill.fore_color.rgb = pale
            box.line.color.rgb = color; box.line.width = Pt(1)
            tf2 = box.text_frame
            tf2.margin_left = Inches(0.15)
            tf2.vertical_anchor = MSO_ANCHOR.MIDDLE
            p2 = tf2.paragraphs[0]
            p2.text = "• " + item
            for run in p2.runs:
                run.font.size = Pt(11); run.font.color.rgb = TEXT_DARK
                run.font.name = "Calibri"
            y += 0.55

    add_callout(s,
        "⚠ Never feed the expert's diagnosis into the model as an input feature. "
        "The model must predict the label, not see it. Mixing these categories "
        "produces misleadingly high accuracy that fails on real data.",
        top=6.15, height=0.9, fill=RED_PALE, border=RED_WARN)

    add_footer(s, 7)


def slide_08_fusion_math(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "3. How the Fusion Layer Works — The Math",
              "Concatenation of two feature vectors")

    # The math
    code = '''Visual vector:    V ∈ ℝ^512
Context vector:   C ∈ ℝ^16

Simple concatenation:
F = [V ; C]     → F ∈ ℝ^528

With a context encoder (recommended for baseline):
Context encoder maps 16 raw inputs → 64 learned features
C_learned ∈ ℝ^64

F = [V ; C_learned]  →  F ∈ ℝ^576

Then:
  F → Linear(576, 256) → ReLU → Dropout(0.3) → Linear(256, N_classes)
  → Softmax → class probabilities'''

    add_code_block(s, code, top=1.9, height=2.9, size=11)

    # Visual: 512 + 16 = 528
    y = 5.05
    add_box(s, 0.75, y, 2.3, 0.85,
            "Visual\nV ∈ ℝ^512", GREEN_PRIMARY, font_size=11)
    add_box(s, 3.15, y, 2.3, 0.85,
            "Context\nC ∈ ℝ^16", ORANGE_ACCENT, font_size=11)

    # Plus and arrow
    add_box(s, 5.55, y + 0.2, 0.5, 0.45, "+",
            WHITE, text_color=TEXT_DARK, font_size=20,
            shape=MSO_SHAPE.RECTANGLE, bold=True)

    add_arrow(s, 6.15, y + 0.3, 0.6, 0.25, PURPLE)

    add_box(s, 6.85, y, 2.7, 0.85,
            "Concatenated\nF ∈ ℝ^528", PURPLE, font_size=11)

    add_arrow(s, 9.65, y + 0.3, 0.6, 0.25, PURPLE)

    add_box(s, 10.35, y, 2.2, 0.85,
            "Classifier\n→ logits", RED_WARN, font_size=11)

    add_footer(s, 8)


def slide_09_fusion_strategies(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "3. Two Fusion Strategies",
              "Start simple — add complexity only if it helps")

    # Late fusion (left)
    add_box(s, 0.75, 1.9, 5.9, 0.55, "LATE FUSION (Concatenation)",
            GREEN_PRIMARY, font_size=14)

    add_bullets(s, [
        "Simplest approach — just concatenate vectors",
        "F = [V ; C]",
        "Then feed into a small MLP classifier",
        "Robust, easy to debug, easy to interpret",
        "Recommended for V1 prototype",
    ], left=0.75, top=2.55, width=5.9, height=2.2, size=12)

    code1 = '''fused = torch.cat([V, C], dim=1)
logits = classifier(fused)'''

    add_code_block(s, code1, left=0.75, top=4.85,
                    width=5.9, height=1.1, size=11)

    # Gated attention (right)
    add_box(s, 6.8, 1.9, 5.9, 0.55, "GATED ATTENTION FUSION (Advanced)",
            PURPLE, font_size=14)

    add_bullets(s, [
        "Context branch produces per-modality weights",
        "Image features are modulated by context attention",
        "E.g., '0% likelihood of X in this region' lowers X's weight",
        "More expressive — but more parameters, more data needed",
        "Only use if late fusion underperforms",
    ], left=6.8, top=2.55, width=5.9, height=2.2, size=12)

    code2 = '''gate = sigmoid(gate_net(C))   # (B, 1)
fused = torch.cat([
    V * gate, C
], dim=1)'''

    add_code_block(s, code2, left=6.8, top=4.85,
                    width=5.9, height=1.1, size=11)

    add_callout(s,
        "⚠ The literature supports multimodal fusion for plant disease. "
        "But our own Ethiopian field evaluation must determine whether "
        "fusion helps — not the publication record.",
        top=6.2, height=0.75, fill=BLUE_PALE, border=BLUE_INFO)

    add_footer(s, 9)


def slide_10_fusion_code(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "3. Fusion Layer in PyTorch",
              "Two branches + fusion + classifier")

    code = '''import torch
import torch.nn as nn
from torchvision import models

class FusionModel(nn.Module):
    def __init__(self, num_classes=4, num_context_features=16):
        super().__init__()

        # ---- Branch 1: Image (CNN) ----
        base = models.mobilenet_v2(
            weights=models.MobileNet_V2_Weights.IMAGENET1K_V1
        )
        self.cnn = base.features
        self.pool = nn.AdaptiveAvgPool2d(1)      # → 1280-d

        # ---- Branch 2: Context (MLP) ----
        self.context_encoder = nn.Sequential(
            nn.Linear(num_context_features, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
        )

        # ---- Fusion classifier ----
        self.classifier = nn.Sequential(
            nn.Linear(1280 + 64, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes),
        )

    def forward(self, image, context):
        # Visual path
        x = self.pool(self.cnn(image)).flatten(1)   # (B, 1280)
        # Context path
        c = self.context_encoder(context)           # (B, 64)
        # Fusion
        fused = torch.cat([x, c], dim=1)            # (B, 1344)
        return self.classifier(fused)               # (B, N_classes)'''

    add_code_block(s, code, top=1.85, height=5.25, size=9)

    add_footer(s, 10)


def slide_11_paired_data(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "4. The Hard Part — Paired Image + Context Data",
              "A training record links image, context, and verified label")

    code = '''{
  "record_id": "FIELD-000001",
  "crop": "wheat",
  "plant_part": "leaf",
  "image_path": "images/FIELD-000001.jpg",
  "collection_date": "2026-10-15",
  "location_precision": "district",
  "region": "Oromia",
  "altitude_m": 2400,
  "variety": "unknown",
  "recent_rainfall": null,
  "temperature": null,
  "humidity_pct": null,
  "symptom_duration_days": 7,
  "image_quality": "acceptable",
  "collector_id": "DA-042",
  "expert_verification_status": "verified",
  "diagnosis_label": "stripe_rust",
  "diagnosis_method": "documented_expert_assessment"
}'''

    add_code_block(s, code, top=1.9, height=3.7, size=9)

    # Principles
    add_bullets(s, [
        "Image and context belong to the same field observation (same day, same plant)",
        "Missing values are null — never fabricated (no synthetic GPS, weather, or soil)",
        "Label has documented verification status and method",
        "Only diagnostic inputs are allowed in the context feature vector",
        "Expert's diagnosis is the target label, not an input feature",
    ], top=5.7, size=12, height=1.4)

    add_footer(s, 11)


def slide_12_data_leakage(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "4. Data Leakage Warnings",
              "Three practices that break multimodal training")

    warnings = [
        ("❌ Synthetic GPS coordinates",
         "Do not generate fake coordinates to fill missing location data. "
         "The model will learn geographic correlations that do not exist."),
        ("❌ Fabricated weather data",
         "Do not invent rainfall or temperature. Missing means missing — "
         "exclude the case or use a documented imputation method."),
        ("❌ Location-as-disease shortcuts",
         "If all disease A comes from region X and all disease B from region Y, "
         "the model learns the region, not the disease. Requires grouped splits."),
    ]

    y = 1.9
    for title, body in warnings:
        # Warning card
        box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                  Inches(0.75), Inches(y),
                                  Inches(11.8), Inches(1.15))
        box.fill.solid(); box.fill.fore_color.rgb = RED_PALE
        box.line.color.rgb = RED_WARN; box.line.width = Pt(1.5)
        tf = box.text_frame; tf.word_wrap = True
        tf.margin_left = Inches(0.25); tf.margin_right = Inches(0.25)
        tf.margin_top = Inches(0.1); tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.text = title
        for run in p.runs:
            run.font.size = Pt(14); run.font.bold = True
            run.font.color.rgb = RED_WARN; run.font.name = "Calibri"

        p2 = tf.add_paragraph()
        p2.text = body
        for run in p2.runs:
            run.font.size = Pt(12); run.font.color.rgb = TEXT_DARK
            run.font.name = "Calibri"
        y += 1.3

    add_callout(s,
        "✓ Preserve every field's provenance: crop source, image date, "
        "GPS precision, expert name, lab reference. The model's trustworthiness "
        "depends on the trustworthiness of each record.",
        top=6.2, height=0.75, fill=GREEN_PALE, border=GREEN_PRIMARY)

    add_footer(s, 12)


def slide_13_training_stages(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "5. Training in Three Stages",
              "Do not train a giant model first — build up evidence")

    stages = [
        ("STAGE 1", "Image-Only Baseline",
         "Train CNN on verified crop classes. Establish the visual performance ceiling.",
         GREEN_PRIMARY),
        ("STAGE 2", "Context-Only Baseline",
         "Train MLP on tabular features alone. Does context carry disease signal? "
         "Suspiciously high accuracy = investigate leakage.",
         ORANGE_ACCENT),
        ("STAGE 3", "Fusion Model",
         "Train both branches jointly. Compare against Stage 1 and Stage 2. "
         "Keep only if it outperforms on held-out data.",
         PURPLE),
    ]

    for i, (label, title, body, color) in enumerate(stages):
        y = 1.9 + i * 1.55
        add_box(s, 0.75, y, 1.9, 1.35, label, color, font_size=13)

        tb = s.shapes.add_textbox(Inches(2.85), Inches(y),
                                    Inches(9.7), Inches(0.45))
        tf = tb.text_frame; tf.word_wrap = True
        p = tf.paragraphs[0]; p.text = title
        for run in p.runs:
            run.font.size = Pt(16); run.font.bold = True
            run.font.color.rgb = color; run.font.name = "Calibri"

        tb2 = s.shapes.add_textbox(Inches(2.85), Inches(y + 0.5),
                                     Inches(9.7), Inches(0.85))
        tf2 = tb2.text_frame; tf2.word_wrap = True
        p2 = tf2.paragraphs[0]; p2.text = body
        for run in p2.runs:
            run.font.size = Pt(12); run.font.color.rgb = TEXT_DARK
            run.font.name = "Calibri"

    add_callout(s,
        "⚠ Each stage is a separately-measured experiment. Do not skip to fusion "
        "without knowing what the image-only and context-only baselines achieve.",
        top=6.65, height=0.55, fill=BLUE_PALE, border=BLUE_INFO)

    add_footer(s, 13)


def slide_14_three_comparison(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "5. The Three-Experiment Comparison",
              "All must use the same dataset and split")

    # Table
    add_box(s, 0.75, 1.9, 2.0, 0.5, "Experiment", GREEN_DARK, font_size=12)
    add_box(s, 2.85, 1.9, 3.0, 0.5, "Inputs", GREEN_DARK, font_size=12)
    add_box(s, 5.95, 1.9, 6.6, 0.5, "What It Tells Us", GREEN_DARK, font_size=12)

    rows = [
        ("A — Image only", "Photograph",
         "Visual baseline: how well can the CNN classify from pixels alone?",
         GREEN_PALE, GREEN_PRIMARY),
        ("B — Context only", "Structured tabular data",
         "Is context informative? If accuracy is suspiciously high, check for "
         "leakage (e.g., location correlated with disease).",
         ORANGE_LIGHT, ORANGE_ACCENT),
        ("C — Fusion", "Photograph + context",
         "Does combining both modalities help? Compare A vs C on the same test set.",
         PURPLE_PALE, PURPLE),
    ]

    y = 2.5
    for label, inputs, tells, pale, color in rows:
        add_box(s, 0.75, y, 2.0, 1.3, label, color, font_size=12)

        tb = s.shapes.add_textbox(Inches(2.85), Inches(y),
                                    Inches(3.0), Inches(1.3))
        tf = tb.text_frame; tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]; p.text = inputs
        for run in p.runs:
            run.font.size = Pt(12); run.font.color.rgb = TEXT_DARK
            run.font.name = "Calibri"

        add_box(s, 5.95, y, 6.6, 1.3, tells, pale,
                text_color=TEXT_DARK, font_size=11, bold=False)
        y += 1.4

    add_callout(s,
        "⚠ Keep the fusion model ONLY if it produces a meaningful, "
        "reproducible improvement over image-only. Do not adopt complexity "
        "without demonstrated benefit.",
        top=6.7, height=0.55, fill=RED_PALE, border=RED_WARN)

    add_footer(s, 14)


def slide_15_generalization(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "5. Testing Generalization",
              "The same-plant / same-farm trap")

    add_bullets(s, [
        "Split by LOCATION, not by image",
        ("Images from the same plant, field, or collection session must not "
         "cross between train and test"),
        ("Use grouped cross-validation: all duplicates of a session in one fold"),
        ("Test on independent fields, seasons, and regions — not just a random split"),
    ], top=1.9, size=13, height=2.0)

    # Metrics table
    add_box(s, 0.75, 3.95, 11.8, 0.5, "REPORT THESE METRICS",
            GREEN_PRIMARY, font_size=13)

    metrics = [
        ("Overall accuracy", "How often is the top prediction correct?"),
        ("Macro-F1 & per-class P/R", "Balanced performance across all classes"),
        ("Confusion matrix", "Which classes get confused with which?"),
        ("Performance on independent fields", "Held-out locations only"),
        ("Calibration", "Do predicted probabilities match observed frequencies?"),
        ("Failure rate on poor images", "What happens with low-quality photos?"),
        ("Referral accuracy", "Are uncertain cases correctly flagged for experts?"),
        ("Subgroup analysis", "Variety, growth stage, location, image quality"),
    ]

    y = 4.55
    for label, desc in metrics:
        tb = s.shapes.add_textbox(Inches(0.75), Inches(y),
                                    Inches(4.0), Inches(0.3))
        tf = tb.text_frame
        p = tf.paragraphs[0]; p.text = label
        for run in p.runs:
            run.font.size = Pt(11); run.font.bold = True
            run.font.color.rgb = GREEN_DARK; run.font.name = "Calibri"

        tb2 = s.shapes.add_textbox(Inches(4.85), Inches(y),
                                     Inches(7.7), Inches(0.3))
        tf2 = tb2.text_frame
        p2 = tf2.paragraphs[0]; p2.text = desc
        for run in p2.runs:
            run.font.size = Pt(11); run.font.color.rgb = TEXT_DARK
            run.font.name = "Calibri"
        y += 0.3

    add_footer(s, 15)


def slide_16_uncertainty(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "6. Uncertainty Handling — The Safety Layer",
              "The highest softmax score is NOT a confirmed diagnosis")

    # Example probabilities
    add_box(s, 0.75, 1.9, 5.9, 0.5, "EXAMPLE MODEL OUTPUT",
            ORANGE_ACCENT, font_size=13)

    probs = [
        ("Stripe rust", "0.64"),
        ("Septoria", "0.23"),
        ("Healthy", "0.13"),
    ]
    y = 2.5
    for cls, prob in probs:
        add_box(s, 0.75, y, 3.0, 0.45, cls, GREEN_PALE,
                text_color=TEXT_DARK, font_size=12, bold=False,
                shape=MSO_SHAPE.RECTANGLE)
        add_box(s, 3.85, y, 2.8, 0.45, prob, ORANGE_LIGHT,
                text_color=ORANGE_ACCENT, font_size=12, bold=True,
                shape=MSO_SHAPE.RECTANGLE)
        y += 0.55

    # Warning
    tb = s.shapes.add_textbox(Inches(0.75), Inches(4.4),
                                Inches(5.9), Inches(0.75))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = ("0.64 is NOT high enough to say 'definitely stripe rust.' "
              "The model may not have encountered the actual condition, "
              "and softmax scores are often poorly calibrated.")
    for run in p.runs:
        run.font.size = Pt(12); run.font.color.rgb = RED_WARN
        run.font.name = "Calibri"

    # Right: 3 outcomes
    add_box(s, 6.8, 1.9, 5.9, 0.5, "THREE REQUIRED OUTCOMES",
            PURPLE, font_size=13)

    outcomes = [
        ("SUPPORTED", "Plausible result within validated scope",
         GREEN_PRIMARY, GREEN_PALE),
        ("UNCERTAIN", "Model cannot make reliable distinction — refer to expert",
         ORANGE_ACCENT, ORANGE_LIGHT),
        ("UNSUPPORTED", "Crop / disease / plant part outside validated scope",
         RED_WARN, RED_PALE),
    ]

    y = 2.5
    for name, desc, color, pale in outcomes:
        add_box(s, 6.8, y, 2.0, 0.75, name, color, font_size=12)
        add_box(s, 8.9, y, 3.8, 0.75, desc, pale,
                text_color=TEXT_DARK, font_size=11, bold=False)
        y += 0.9

    # Safety checks
    add_callout(s,
        "7 checks before showing a diagnosis: (1) crop supported? "
        "(2) plant part valid? (3) image quality OK? (4) class covered? "
        "(5) uncertainty acceptable? (6) context valid? (7) referral needed?",
        top=5.7, height=1.4, fill=BLUE_PALE, border=BLUE_INFO)

    add_footer(s, 16)


def slide_17_ood(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "6. Out-of-Scope Detection",
              "Softmax alone is not enough")

    add_bullets(s, [
        "A classifier trained on known diseases will confidently assign an "
        "unfamiliar disease to its closest known class",
        "The winning softmax score can be high even when the input is "
        "completely outside the training distribution",
        "This is a fundamental property of closed-set classification — not a bug",
    ], top=1.9, size=13, height=1.8)

    # What to test
    add_box(s, 0.75, 3.85, 11.8, 0.5, "WHAT TO TEST",
            RED_WARN, font_size=13)

    add_bullets(s, [
        "Feed unsupported crops (e.g., enset to a wheat model) — should return UNSUPPORTED",
        "Feed corrupted / blank images — should return UNSUPPORTED",
        "Feed other plant species (weeds, other crops) — should return UNSUPPORTED",
        "Feed healthy leaves from a different variety — should return healthy, not "
        "a confident disease",
    ], top=4.45, size=12, height=1.6)

    # Approaches
    add_box(s, 0.75, 6.1, 5.9, 0.4, "APPROACHES TO OOD DETECTION",
            PURPLE, font_size=12)
    add_box(s, 6.8, 6.1, 5.9, 0.4, "MINIMUM REQUIREMENT",
            BLUE_INFO, font_size=12)

    tb = s.shapes.add_textbox(Inches(0.75), Inches(6.55),
                                Inches(5.9), Inches(0.55))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "• Energy-based OOD score\n• Mahalanobis distance\n• Ensemble disagreement"
    for run in p.runs:
        run.font.size = Pt(10); run.font.color.rgb = TEXT_DARK
        run.font.name = "Calibri"

    tb2 = s.shapes.add_textbox(Inches(6.8), Inches(6.55),
                                 Inches(5.9), Inches(0.55))
    tf2 = tb2.text_frame; tf2.word_wrap = True
    p2 = tf2.paragraphs[0]
    p2.text = "Explicit test suite of unsupported inputs.\nNo production deployment "
    for run in p2.runs:
        run.font.size = Pt(10); run.font.color.rgb = TEXT_DARK
        run.font.name = "Calibri"

    add_footer(s, 17)


def slide_18_complete_platform(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "7. Complete Platform Architecture",
              "Six layers from DA input to case management")

    layers = [
        ("USER APPLICATION",
         "DA selects crop, records symptoms, uploads photo, submits field info",
         GREEN_PRIMARY),
        ("BACKEND API",
         "Auth, validation, case ID, consent, image storage, audit trail",
         GREEN_MID),
        ("INFERENCE SERVICE",
         "Image preprocess + context preprocess → CNN + Context encoder → Fusion → Predictions",
         PURPLE),
        ("DIAGNOSTIC SAFETY LAYER",
         "Scope checks, calibration, uncertainty thresholds, referral rules",
         ORANGE_ACCENT),
        ("RESULTS INTERFACE",
         "Diagnosis + supporting info + limitations + referral status",
         GREEN_MID),
        ("CASE MANAGEMENT",
         "Expert review, verified outcomes, history, model evaluation data",
         GREEN_DARK),
    ]

    y = 1.85
    for name, desc, color in layers:
        add_box(s, 0.75, y, 3.0, 0.75, name, color, font_size=11)
        add_box(s, 3.85, y, 8.7, 0.75, desc, WHITE,
                text_color=TEXT_DARK, font_size=11, bold=False,
                shape=MSO_SHAPE.RECTANGLE, border_color=color)
        add_down_arrow(s, 2.1, y + 0.78, 0.25, 0.15, color)
        y += 0.95

    add_footer(s, 18)


def slide_19_tech_stack(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "7. Recommended Technology Stack",
              "Use what works — do not introduce tech for appearance")

    # Table
    add_box(s, 0.75, 1.9, 2.7, 0.5, "Component", GREEN_DARK, font_size=12)
    add_box(s, 3.55, 1.9, 3.5, 0.5, "Proposed Technology", GREEN_DARK, font_size=12)
    add_box(s, 7.15, 1.9, 5.4, 0.5, "Purpose", GREEN_DARK, font_size=12)

    rows = [
        ("Frontend", "Existing React frontend", "DA interface and case workflow"),
        ("Main API", "Existing backend with clear API contract",
         "Auth, cases, records, permissions"),
        ("AI Service", "Python + FastAPI", "Model inference and preprocessing"),
        ("Deep Learning", "PyTorch", "CNN, context encoder, fusion model"),
        ("Structured Data", "PostgreSQL (or existing)", "Field records, labels, audit"),
        ("Image Storage", "Controlled local or object storage", "Photos + metadata"),
        ("Model Artifacts", "Versioned checkpoints", "Reproducible inference"),
        ("Evaluation", "Python scripts + manifests", "Model comparison + validation"),
    ]

    y = 2.5
    for comp, tech, purpose in rows:
        add_box(s, 0.75, y, 2.7, 0.42, comp, GREEN_PALE,
                text_color=TEXT_DARK, font_size=11, bold=True,
                shape=MSO_SHAPE.RECTANGLE)
        add_box(s, 3.55, y, 3.5, 0.42, tech, WHITE,
                text_color=TEXT_DARK, font_size=10, bold=False,
                shape=MSO_SHAPE.RECTANGLE, border_color=BORDER_LIGHT)
        add_box(s, 7.15, y, 5.4, 0.42, purpose, WHITE,
                text_color=TEXT_DARK, font_size=10, bold=False,
                shape=MSO_SHAPE.RECTANGLE, border_color=BORDER_LIGHT)
        y += 0.48

    add_callout(s,
        "⚠ Do not introduce new technology just to look sophisticated. "
        "Adapt the existing application if its interfaces support these "
        "responsibilities.",
        top=6.55, height=0.55, fill=RED_PALE, border=RED_WARN)

    add_footer(s, 19)


def slide_20_shared_vs_crop(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "8. Shared Platform vs Per-Crop Models",
              "Modular architecture — one app, many capabilities")

    add_callout(s,
        "AgriMind = ONE shared field-data workflow + MULTIPLE crop-specific "
        "model capabilities, each activated when its data and evidence justify it.",
        top=1.85, height=0.65, fill=GREEN_PALE, border=GREEN_PRIMARY)

    # Table
    add_box(s, 0.75, 2.7, 2.5, 0.5, "Crop", GREEN_DARK, font_size=12)
    add_box(s, 3.35, 2.7, 4.5, 0.5, "Current AI Status", GREEN_DARK, font_size=12)
    add_box(s, 7.95, 2.7, 4.6, 0.5, "Longer-Term Direction", GREEN_DARK, font_size=12)

    rows = [
        ("Wheat", "3-class experimental model (93.42% test)",
         "Image-context fusion after field data collection", GREEN_LIGHT),
        ("Coffee", "4-class experimental model (93.42% test)",
         "Fusion if context demonstrably improves accuracy", ORANGE_LIGHT),
        ("Maize", "No AI yet — Phase A taxonomy needed",
         "Train & validate image model, then fusion", RED_PALE),
        ("Teff", "No AI yet — specialist taxonomy needed",
         "Add AI after suitable labelled data exists", RED_PALE),
        ("Enset", "No AI yet — Phase C field collection",
         "Add AI after dataset & evaluation protocol", RED_PALE),
    ]

    y = 3.3
    for crop, status, direction, color in rows:
        add_box(s, 0.75, y, 2.5, 1.0, crop, color,
                text_color=TEXT_DARK, font_size=13, bold=True)
        add_box(s, 3.35, y, 4.5, 1.0, status, WHITE,
                text_color=TEXT_DARK, font_size=11, bold=False,
                shape=MSO_SHAPE.RECTANGLE, border_color=BORDER_LIGHT)
        add_box(s, 7.95, y, 4.6, 1.0, direction, WHITE,
                text_color=TEXT_DARK, font_size=11, bold=False,
                shape=MSO_SHAPE.RECTANGLE, border_color=BORDER_LIGHT)
        y += 1.08

    add_footer(s, 20)


def slide_21_risks(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "9. Risks and Mitigations",
              "Six identified failure modes")

    risks = [
        ("Model learns location, not disease",
         "Preserve field IDs; use grouped splits; compare image-only vs context-only baselines."),
        ("Context hides unusual disease",
         "Never hardcode 'disease X impossible in region Y'. Use context as support, not absolute exclusion."),
        ("Unreliable labels poison both branches",
         "Track label provenance, expert review status, confirmation method. Exclude uncertain labels."),
        ("Public data ≠ Ethiopian fields",
         "Maintain frozen external test set. Never tune against the external test set."),
        ("Model depends on missing context",
         "Design for incomplete data. Evaluate under missingness. Fall back gracefully."),
        ("Fusion adds complexity without accuracy",
         "Require fusion to beat image-only by a meaningful margin before adopting."),
    ]

    y = 1.9
    for i, (risk, mitigation) in enumerate(risks):
        add_number_badge(s, str(i+1), 0.75, y + 0.05, RED_WARN, 0.5)

        tb = s.shapes.add_textbox(Inches(1.4), Inches(y),
                                    Inches(11.2), Inches(0.35))
        tf = tb.text_frame; tf.word_wrap = True
        p = tf.paragraphs[0]; p.text = risk
        for run in p.runs:
            run.font.size = Pt(13); run.font.bold = True
            run.font.color.rgb = RED_WARN; run.font.name = "Calibri"

        tb2 = s.shapes.add_textbox(Inches(1.4), Inches(y + 0.35),
                                     Inches(11.2), Inches(0.5))
        tf2 = tb2.text_frame; tf2.word_wrap = True
        p2 = tf2.paragraphs[0]
        p2.text = "→ " + mitigation
        for run in p2.runs:
            run.font.size = Pt(11); run.font.color.rgb = TEXT_DARK
            run.font.name = "Calibri"
        y += 0.85

    add_footer(s, 21)


def slide_22_roadmap(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "10. Development Roadmap",
              "10 phased milestones with completion criteria")

    phases = [
        ("1", "Architecture", "System boundaries & data flow agreed"),
        ("2", "Data Contract", "Case/image/context/label schema versioned"),
        ("3", "Image Baseline", "Working image inference endpoint"),
        ("4", "Context Baseline", "Validated tabular preprocessing pipeline"),
        ("5", "Paired Dataset", "Curated multimodal records with provenance"),
        ("6", "Fusion Prototype", "Fusion model with identical preprocessing"),
        ("7", "Comparative Eval", "Image vs context vs fusion report"),
        ("8", "Safety & Workflow", "Uncertainty, referral, DA-facing UX"),
        ("9", "External Validation", "Performance on independent fields"),
        ("10", "Controlled Pilot", "5-10 DAs, expert oversight, evaluation"),
    ]

    # 2 columns of 5
    for i, (num, title, desc) in enumerate(phases):
        col = 0 if i < 5 else 1
        row = i if i < 5 else i - 5
        x = 0.75 + col * 6.1
        y = 1.9 + row * 1.05

        add_number_badge(s, num, x, y + 0.1, GREEN_PRIMARY, 0.45)

        tb = s.shapes.add_textbox(Inches(x + 0.6), Inches(y),
                                    Inches(5.3), Inches(0.4))
        tf = tb.text_frame; tf.word_wrap = True
        p = tf.paragraphs[0]; p.text = title
        for run in p.runs:
            run.font.size = Pt(13); run.font.bold = True
            run.font.color.rgb = GREEN_DARK; run.font.name = "Calibri"

        tb2 = s.shapes.add_textbox(Inches(x + 0.6), Inches(y + 0.35),
                                     Inches(5.3), Inches(0.55))
        tf2 = tb2.text_frame; tf2.word_wrap = True
        p2 = tf2.paragraphs[0]; p2.text = desc
        for run in p2.runs:
            run.font.size = Pt(10); run.font.color.rgb = TEXT_DARK
            run.font.name = "Calibri"

    add_footer(s, 22)


def slide_23_v0_scope(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "11. V0 — Platform Foundation",
              "What to build first, before any fusion work")

    # Two columns
    add_box(s, 0.75, 1.9, 5.9, 0.5, "✓ V0 INCLUDES",
            GREEN_PRIMARY, font_size=14)

    add_bullets(s, [
        "DA creates a field case (crop, plant part, symptoms, photos)",
        "Backend validates and stores the record",
        "AI service checks whether the crop is supported",
        "Existing experimental model runs ONLY within documented scope",
        "Platform records model version, prediction, and case ID",
        "Uncertain or unsupported cases → expert referral",
        "Expert-verified outcomes stored for future training",
    ], left=0.75, top=2.55, width=5.9, height=4.0, size=11)

    add_box(s, 6.8, 1.9, 5.9, 0.5, "✗ V0 EXCLUDES",
            RED_WARN, font_size=14)

    add_bullets(s, [
        "No context encoder",
        "No fusion model",
        "No tabular features in inference",
        "No geographic masking rules",
        "No OOD detection (deferred to V0.5)",
        "No per-crop UI differences",
        "No multi-crop simultaneous support",
    ], left=6.8, top=2.55, width=5.9, height=4.0, size=11)

    add_callout(s,
        "✓ V0 succeeds when a DA can complete a full field case end-to-end "
        "and get either a supported diagnosis or a clear expert-referral path. "
        "AI is one feature; workflow is the product.",
        top=6.65, height=0.55, fill=GREEN_PALE, border=GREEN_PRIMARY)

    add_footer(s, 23)


def slide_24_v1_scope(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "11. V1 — Fusion Prototype (after V0 + data)",
              "Only build when paired data exists")

    add_bullets(s, [
        "Add context encoder (tabular → learned embedding)",
        "Build dataset of paired image + context + verified labels",
        "Train context-only baseline (Experiment B)",
        "Train fusion model (Experiment C)",
        "Compare all three (A: image-only, B: context-only, C: fusion)",
        "Retain fusion ONLY if it beats image-only by a documented margin",
    ], top=1.9, size=14, height=3.0)

    # When to start
    add_box(s, 0.75, 5.2, 11.8, 0.55,
            "GATE TO START V1", ORANGE_ACCENT, font_size=14)

    add_box(s, 0.75, 5.85, 3.75, 1.1,
            "500+\npaired records",
            GREEN_PALE, text_color=GREEN_DARK, font_size=12)
    add_box(s, 4.6, 5.85, 3.95, 1.1,
            "Expert-verified\nlabels",
            GREEN_PALE, text_color=GREEN_DARK, font_size=12)
    add_box(s, 8.65, 5.85, 3.9, 1.1,
            "Independent\ntest set held out",
            GREEN_PALE, text_color=GREEN_DARK, font_size=12)

    add_footer(s, 24)


def slide_25_do_not(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "11. What NOT to Do",
              "Six anti-patterns that break the project")

    dont_do = [
        "Train one giant classifier for all Ethiopian crops and diseases",
        "Commit to 512 visual + 16 context dimensions as fixed requirements",
        "Generate synthetic GPS, weather, or soil data to fill gaps",
        "Hardcode geographic rules that declare diseases impossible in regions",
        "Claim fusion is more accurate before a controlled comparison",
        "Present experimental wheat/coffee metrics as production readiness",
    ]

    y = 1.9
    for item in dont_do:
        # Red X
        badge = s.shapes.add_shape(MSO_SHAPE.OVAL,
                                     Inches(0.75), Inches(y + 0.05),
                                     Inches(0.5), Inches(0.5))
        badge.fill.solid(); badge.fill.fore_color.rgb = RED_WARN
        badge.line.fill.background()
        tf = badge.text_frame
        tf.margin_left = Emu(0); tf.margin_right = Emu(0)
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
        p.text = "✗"
        for run in p.runs:
            run.font.size = Pt(18); run.font.bold = True
            run.font.color.rgb = WHITE; run.font.name = "Calibri"

        # Text
        tb = s.shapes.add_textbox(Inches(1.4), Inches(y + 0.05),
                                    Inches(11.2), Inches(0.7))
        tf2 = tb.text_frame; tf2.word_wrap = True
        tf2.vertical_anchor = MSO_ANCHOR.MIDDLE
        p2 = tf2.paragraphs[0]; p2.text = item
        for run in p2.runs:
            run.font.size = Pt(13); run.font.color.rgb = TEXT_DARK
            run.font.name = "Calibri"
        y += 0.85

    add_footer(s, 25)


def slide_26_decision(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "12. The Decision",
              "What we are committing to")

    # Decision statement
    box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                              Inches(0.75), Inches(1.85),
                              Inches(11.8), Inches(1.7))
    box.fill.solid(); box.fill.fore_color.rgb = GREEN_PALE
    box.line.color.rgb = GREEN_PRIMARY; box.line.width = Pt(2)
    tf = box.text_frame; tf.word_wrap = True
    tf.margin_left = Inches(0.35); tf.margin_right = Inches(0.35)
    tf.margin_top = Inches(0.2); tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.text = "DECISION STATEMENT"
    for run in p.runs:
        run.font.size = Pt(12); run.font.bold = True
        run.font.color.rgb = GREEN_DARK; run.font.name = "Calibri"

    p2 = tf.add_paragraph()
    p2.text = ("AgriMind-Ethiopia will use a modular multimodal diagnosis architecture "
               "that combines plant-image features with validated field context when "
               "paired training data and evaluation evidence justify doing so. The "
               "platform will support crop-specific capabilities, preserve "
               "expert-verification provenance, and provide uncertainty-aware results "
               "and referral workflows. Fusion will be retained only when it "
               "demonstrates a measurable benefit over an image-only baseline on "
               "appropriately independent data.")
    for run in p2.runs:
        run.font.size = Pt(12); run.font.color.rgb = TEXT_DARK
        run.font.name = "Calibri"

    # Next deliverable
    add_box(s, 0.75, 3.85, 11.8, 0.55,
            "NEXT DELIVERABLE: Architecture & Data Contract Specification",
            PURPLE, font_size=14)

    specs = [
        "1. Image input contract + CNN feature extraction interface",
        "2. Contextual field schema + encoding rules",
        "3. Fusion interface + output class definitions",
        "4. Case record + expert label schema",
        "5. Model inference API contract",
        "6. Evaluation + safety requirements",
    ]

    for i, spec in enumerate(specs):
        col = i % 2
        row = i // 2
        x = 0.75 + col * 6.05
        y = 4.55 + row * 0.6
        tb = s.shapes.add_textbox(Inches(x), Inches(y),
                                    Inches(5.8), Inches(0.5))
        tf = tb.text_frame; tf.word_wrap = True
        p = tf.paragraphs[0]; p.text = spec
        for run in p.runs:
            run.font.size = Pt(12); run.font.color.rgb = TEXT_DARK
            run.font.name = "Calibri"

    add_footer(s, 26)


def slide_27_summary(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "EAII Verification Summary",
              "What this deck establishes")

    # Left: what we prove
    add_box(s, 0.75, 1.9, 5.9, 0.5, "✓ WHAT THIS DECK ESTABLISHES",
            GREEN_PRIMARY, font_size=13)

    add_bullets(s, [
        "The CNN + Tabular → Fusion architecture is technically sound",
        "We understand the 512 + 16 → 528 (or 576) math",
        "We know how to encode context (embeddings, one-hot, normalization)",
        "We know the training sequence (image → context → fusion)",
        "We know the safety layer requirements (3 outcomes, 7 checks)",
        "We know the risks and mitigations (6 failure modes)",
        "We have a 10-phase roadmap with completion criteria",
        "We have V0 and V1 scope defined",
    ], left=0.75, top=2.55, width=5.9, height=3.6, size=11)

    # Right: what we do NOT claim
    add_box(s, 6.8, 1.9, 5.9, 0.5, "✗ WHAT WE DO NOT CLAIM YET",
            RED_WARN, font_size=13)

    add_bullets(s, [
        "That fusion improves accuracy on Ethiopian crops",
        "That the existing wheat/coffee models are production-ready",
        "That 512 and 16 are final dimensions",
        "That fusion will definitely be deployed",
        "That contextual data alone will diagnose diseases",
        "That per-crop models exist for maize/teff/enset",
        "That the platform is pilot-ready",
        "That the model outperforms a human agronomist",
    ], left=6.8, top=2.55, width=5.9, height=3.6, size=11)

    # Bottom
    add_callout(s,
        "The next deliverable is the Architecture + Data Contract Specification "
        "— the engineering document that turns this vision into buildable code. "
        "Fusion is a 2027 deliverable, gated on 500+ paired records from the "
        "2026 pilot.",
        top=6.35, height=0.85, fill=BLUE_PALE, border=BLUE_INFO)

    add_footer(s, 27)


# ==================== MAIN ====================

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Build 27 slides
    slide_01_title(prs)
    slide_02_agenda(prs)
    slide_03_proposed_arch(prs)
    slide_04_why_multimodal(prs)
    slide_05_visual_features(prs)
    slide_06_contextual_features(prs)
    slide_07_data_categories(prs)
    slide_08_fusion_math(prs)
    slide_09_fusion_strategies(prs)
    slide_10_fusion_code(prs)
    slide_11_paired_data(prs)
    slide_12_data_leakage(prs)
    slide_13_training_stages(prs)
    slide_14_three_comparison(prs)
    slide_15_generalization(prs)
    slide_16_uncertainty(prs)
    slide_17_ood(prs)
    slide_18_complete_platform(prs)
    slide_19_tech_stack(prs)
    slide_20_shared_vs_crop(prs)
    slide_21_risks(prs)
    slide_22_roadmap(prs)
    slide_23_v0_scope(prs)
    slide_24_v1_scope(prs)
    slide_25_do_not(prs)
    slide_26_decision(prs)
    slide_27_summary(prs)

    prs.save(str(OUTPUT_FILE))
    print(f"\n✅ Presentation saved!")
    print(f"   File: {OUTPUT_FILE}")
    print(f"   Slides: {len(prs.slides)}")
    print(f"   Size: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()