"""
AgriMind-Ethiopia — CNN & Fusion Layer Presentation Generator
Generates a 24-slide professional deck on plant disease diagnosis.

Run: python generate_presentation.py
Output: C:\\Users\\justice\\OneDrive\\Documents\\AgriMind-Ethiopia\\AgriMind_CNN_and_Fusion_Guide.pptx
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pathlib import Path
import os

# ==================== CONFIG ====================
OUTPUT_DIR = Path(r"C:\Users\justice\OneDrive\Documents\AgriMind-Ethiopia")
OUTPUT_FILE = OUTPUT_DIR / "AgriMind_CNN_and_Fusion_Guide.pptx"

# Color palette
GREEN_DARK = RGBColor(0x1B, 0x5E, 0x20)
GREEN_PRIMARY = RGBColor(0x2E, 0x7D, 0x32)
GREEN_MID = RGBColor(0x66, 0xBB, 0x6A)
GREEN_LIGHT = RGBColor(0xC8, 0xE6, 0xC9)
GREEN_PALE = RGBColor(0xE8, 0xF5, 0xE9)
ORANGE_ACCENT = RGBColor(0xE6, 0x5C, 0x00)
ORANGE_LIGHT = RGBColor(0xFF, 0xE0, 0xB2)
CODE_BG = RGBColor(0x1E, 0x1E, 0x1E)
CODE_TEXT = RGBColor(0xE8, 0xE8, 0xE8)
CODE_KEYWORD = RGBColor(0x56, 0x9C, 0xD6)
CODE_STRING = RGBColor(0xCE, 0x91, 0x78)
CODE_COMMENT = RGBColor(0x6A, 0x99, 0x55)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
TEXT_DARK = RGBColor(0x21, 0x21, 0x21)
TEXT_GRAY = RGBColor(0x61, 0x61, 0x61)
TEXT_LIGHT_GRAY = RGBColor(0x9E, 0x9E, 0x9E)
BORDER_LIGHT = RGBColor(0xE0, 0xE0, 0xE0)
RED_WARN = RGBColor(0xC6, 0x28, 0x28)
RED_PALE = RGBColor(0xFF, 0xEB, 0xEE)
BLUE_INFO = RGBColor(0x19, 0x76, 0xD2)
BLUE_PALE = RGBColor(0xE3, 0xF2, 0xFD)
PURPLE = RGBColor(0x7B, 0x1F, 0xA2)
PURPLE_PALE = RGBColor(0xF3, 0xE5, 0xF5)

# ==================== HELPERS ====================

def new_slide(prs):
    """Add a blank slide."""
    return prs.slides.add_slide(prs.slide_layouts[6])


def add_bg_bar(slide, color=GREEN_PRIMARY, height=0.12):
    """Top accent bar."""
    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(height)
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = color
    bar.line.fill.background()


def add_title(slide, title, subtitle=None, color=GREEN_DARK):
    """Add a title with optional subtitle."""
    # Left accent
    accent = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(0.45), Inches(0.08), Inches(0.75)
    )
    accent.fill.solid()
    accent.fill.fore_color.rgb = GREEN_PRIMARY
    accent.line.fill.background()

    tb = slide.shapes.add_textbox(
        Inches(0.75), Inches(0.4), Inches(12.0), Inches(0.85)
    )
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.alignment = PP_ALIGN.LEFT
    for run in p.runs:
        run.font.size = Pt(28)
        run.font.bold = True
        run.font.color.rgb = color
        run.font.name = "Calibri"

    if subtitle:
        tb2 = slide.shapes.add_textbox(
            Inches(0.75), Inches(1.25), Inches(12.0), Inches(0.4)
        )
        tf2 = tb2.text_frame
        p2 = tf2.paragraphs[0]
        p2.text = subtitle
        for run in p2.runs:
            run.font.size = Pt(14)
            run.font.color.rgb = TEXT_GRAY
            run.font.italic = True
            run.font.name = "Calibri"


def add_footer(slide, text="AgriMind-Ethiopia  |  CNN & Fusion Guide  |  2026"):
    """Footer with page info."""
    # Bottom bar
    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, Inches(7.28), Inches(13.333), Inches(0.22)
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = GREEN_PALE
    bar.line.fill.background()

    tb = slide.shapes.add_textbox(
        Inches(0.5), Inches(7.3), Inches(12.3), Inches(0.2)
    )
    tf = tb.text_frame
    p = tf.paragraphs[0]
    p.text = text
    p.alignment = PP_ALIGN.CENTER
    for run in p.runs:
        run.font.size = Pt(9)
        run.font.color.rgb = TEXT_GRAY
        run.font.name = "Calibri"


def add_bullets(slide, items, left=0.75, top=1.8, width=12.0, height=5.2, size=16):
    """Bulleted list with optional sub-bullets."""
    tb = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    tf = tb.text_frame
    tf.word_wrap = True
    first = True
    for item in items:
        if isinstance(item, tuple):
            level, text = item
            if level is None or level == "":
                level = 0
            else:
                level = int(level)
        else:
            level, text = 0, item
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.level = level
        p.text = ("• " if level == 0 else "◦ ") + text
        p.space_after = Pt(6)
        p.space_before = Pt(2)
        for run in p.runs:
            run.font.size = Pt(size if level == 0 else size - 2)
            run.font.color.rgb = TEXT_DARK if level == 0 else TEXT_GRAY
            run.font.name = "Calibri"
            if level == 0:
                run.font.bold = False


def add_code_block(slide, code, left=0.75, top=1.8, width=11.8, height=5.2, size=11):
    """Dark code block."""
    box = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    box.fill.solid()
    box.fill.fore_color.rgb = CODE_BG
    box.line.color.rgb = RGBColor(0x33, 0x33, 0x33)
    box.line.width = Pt(0.75)

    tb = slide.shapes.add_textbox(
        Inches(left + 0.15), Inches(top + 0.12),
        Inches(width - 0.3), Inches(height - 0.24)
    )
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Emu(0)
    tf.margin_right = Emu(0)
    tf.margin_top = Emu(0)
    tf.margin_bottom = Emu(0)
    first = True
    for line in code.split("\n"):
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.text = line if line else " "
        p.space_after = Pt(0)
        p.space_before = Pt(0)
        p.line_spacing = 1.05
        for run in p.runs:
            run.font.size = Pt(size)
            run.font.name = "Consolas"
            run.font.color.rgb = CODE_TEXT


def add_box(slide, left, top, width, height, text, fill, text_color=WHITE,
            font_size=13, bold=True, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    """Colored box with centered text."""
    shp = slide.shapes.add_shape(shape, Inches(left), Inches(top),
                                   Inches(width), Inches(height))
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    shp.line.color.rgb = fill
    shp.line.width = Pt(0.5)
    tf = shp.text_frame
    tf.margin_left = Inches(0.05)
    tf.margin_right = Inches(0.05)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = text
    for run in p.runs:
        run.font.size = Pt(font_size)
        run.font.bold = bold
        run.font.color.rgb = text_color
        run.font.name = "Calibri"
    return shp


def add_arrow(slide, left, top, width, height=0.3, color=GREEN_PRIMARY):
    """Rightward arrow."""
    arr = slide.shapes.add_shape(
        MSO_SHAPE.RIGHT_ARROW, Inches(left), Inches(top),
        Inches(width), Inches(height)
    )
    arr.fill.solid()
    arr.fill.fore_color.rgb = color
    arr.line.fill.background()


def add_table_row(slide, left, top, cells, widths, height=0.45,
                   fill=WHITE, text_color=TEXT_DARK, bold=False, size=11):
    """One row of cells."""
    x = left
    for text, w in zip(cells, widths):
        box = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(x), Inches(top), Inches(w), Inches(height)
        )
        box.fill.solid()
        box.fill.fore_color.rgb = fill
        box.line.color.rgb = BORDER_LIGHT
        box.line.width = Pt(0.75)
        tf = box.text_frame
        tf.margin_left = Inches(0.05)
        tf.margin_right = Inches(0.05)
        tf.margin_top = Inches(0.02)
        tf.margin_bottom = Inches(0.02)
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        p.text = text
        for run in p.runs:
            run.font.size = Pt(size)
            run.font.color.rgb = text_color
            run.font.name = "Calibri"
            run.font.bold = bold
        x += w


# ==================== SLIDE BUILDERS ====================

def slide_title(prs):
    s = new_slide(prs)
    # Full green gradient background
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0,
                             Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = GREEN_DARK
    bg.line.fill.background()

    # Decorative circle
    circle = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(10.5), Inches(-1),
                                 Inches(5), Inches(5))
    circle.fill.solid()
    circle.fill.fore_color.rgb = GREEN_PRIMARY
    circle.line.fill.background()

    # Title
    tb = s.shapes.add_textbox(Inches(0.8), Inches(2.3), Inches(11.7), Inches(1.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "AgriMind-Ethiopia"
    for run in p.runs:
        run.font.size = Pt(56)
        run.font.bold = True
        run.font.color.rgb = WHITE
        run.font.name = "Calibri"

    tb2 = s.shapes.add_textbox(Inches(0.8), Inches(3.7), Inches(11.7), Inches(0.8))
    tf2 = tb2.text_frame
    p2 = tf2.paragraphs[0]
    p2.text = "Understanding CNN & Fusion Layer"
    for run in p2.runs:
        run.font.size = Pt(30)
        run.font.color.rgb = GREEN_LIGHT
        run.font.name = "Calibri"

    tb3 = s.shapes.add_textbox(Inches(0.8), Inches(4.6), Inches(11.7), Inches(0.6))
    tf3 = tb3.text_frame
    p3 = tf3.paragraphs[0]
    p3.text = "How We Diagnose Plant Diseases with Deep Learning"
    for run in p3.runs:
        run.font.size = Pt(20)
        run.font.italic = True
        run.font.color.rgb = GREEN_LIGHT
        run.font.name = "Calibri"

    # Info line
    tb4 = s.shapes.add_textbox(Inches(0.8), Inches(6.3), Inches(11.7), Inches(0.5))
    tf4 = tb4.text_frame
    p4 = tf4.paragraphs[0]
    p4.text = "Technical Guide  •  Coffee & Wheat Models  •  Ethiopian Agriculture AI"
    for run in p4.runs:
        run.font.size = Pt(14)
        run.font.color.rgb = GREEN_LIGHT
        run.font.name = "Calibri"


def slide_agenda(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "Agenda", "What we'll cover in this guide")

    sections = [
        ("PART 1 — Convolutional Neural Networks", GREEN_PRIMARY, [
            "What is a CNN and how does it work?",
            "Architecture: convolutions, pooling, fully connected layers",
            "How to train a CNN for plant disease diagnosis",
            "Code example: MobileNetV2 training loop",
            "Real results from our coffee & wheat models",
        ]),
        ("PART 2 — Fusion Layer (Multimodal AI)", ORANGE_ACCENT, [
            "What is fusion and why does it matter?",
            "Combining image + environmental data",
            "Architecture: late fusion vs. gated attention",
            "Code example: dual-path network",
            "Expected output and confidence calibration",
        ]),
    ]

    y = 1.85
    for title, color, items in sections:
        # Section header
        hdr = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                  Inches(0.75), Inches(y),
                                  Inches(11.8), Inches(0.5))
        hdr.fill.solid()
        hdr.fill.fore_color.rgb = color
        hdr.line.fill.background()
        tf = hdr.text_frame
        tf.margin_left = Inches(0.2)
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.text = title
        p.alignment = PP_ALIGN.LEFT
        for run in p.runs:
            run.font.size = Pt(16)
            run.font.bold = True
            run.font.color.rgb = WHITE
            run.font.name = "Calibri"
        y += 0.65

        for item in items:
            tb = s.shapes.add_textbox(
                Inches(1.0), Inches(y), Inches(11.5), Inches(0.35)
            )
            tf = tb.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = "▸  " + item
            for run in p.runs:
                run.font.size = Pt(13)
                run.font.color.rgb = TEXT_DARK
                run.font.name = "Calibri"
            y += 0.35
        y += 0.15

    add_footer(s)


def slide_what_is_cnn(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "What is a CNN?",
              "Convolutional Neural Network — the brain of image classification")

    # Definition box
    box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                              Inches(0.75), Inches(1.8),
                              Inches(11.8), Inches(1.3))
    box.fill.solid()
    box.fill.fore_color.rgb = GREEN_PALE
    box.line.color.rgb = GREEN_PRIMARY
    box.line.width = Pt(2)
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.3)
    tf.margin_right = Inches(0.3)
    tf.margin_top = Inches(0.15)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.text = ("A CNN is a deep learning model designed to process images by learning "
              "spatial patterns (edges, shapes, textures) through learned filters. "
              "It is the standard architecture for image classification.")
    for run in p.runs:
        run.font.size = Pt(15)
        run.font.color.rgb = TEXT_DARK
        run.font.name = "Calibri"

    # Key properties
    add_bullets(s, [
        "Learns directly from raw pixels — no hand-crafted features required",
        "Preserves spatial structure — a 2D image stays 2D throughout the network",
        "Uses shared weights — the same filter slides across the entire image",
        "Translation-invariant — a disease spot is detected wherever it appears",
        "End-to-end trainable — input image → output disease class in one model",
    ], top=3.35, size=15)

    # Bottom callout
    box2 = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                               Inches(0.75), Inches(6.3),
                               Inches(11.8), Inches(0.8))
    box2.fill.solid()
    box2.fill.fore_color.rgb = ORANGE_LIGHT
    box2.line.color.rgb = ORANGE_ACCENT
    box2.line.width = Pt(1.5)
    tf = box2.text_frame
    tf.margin_left = Inches(0.3)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.text = "In AgriMind: coffee leaf photo → CNN → 'leaf_rust' with 93% confidence"
    for run in p.runs:
        run.font.size = Pt(14)
        run.font.bold = True
        run.font.color.rgb = ORANGE_ACCENT
        run.font.name = "Calibri"

    add_footer(s)


def slide_cnn_architecture(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "CNN Architecture — Four Core Stages",
              "From raw pixels to disease classification")

    # Pipeline
    y = 2.0
    stages = [
        ("INPUT", "224×224×3\nRGB Image", GREEN_DARK),
        ("CONVOLUTION", "Filter 3×3\n→ Feature Maps", GREEN_PRIMARY),
        ("POOLING", "Downsample\n→ Smaller Maps", GREEN_MID),
        ("FLATTEN", "2D → 1D\nVector", ORANGE_ACCENT),
        ("DENSE", "Fully\nConnected", ORANGE_ACCENT),
        ("OUTPUT", "Softmax\nClasses", RED_WARN),
    ]
    box_w = 1.85
    gap = 0.15
    total_w = len(stages) * box_w + (len(stages) - 1) * gap
    start_x = (13.333 - total_w) / 2

    for i, (name, desc, color) in enumerate(stages):
        x = start_x + i * (box_w + gap)
        add_box(s, x, y, box_w, 0.55, name, color, font_size=11)
        add_box(s, x, y + 0.6, box_w, 0.85, desc, GREEN_PALE,
                text_color=TEXT_DARK, font_size=10, bold=False)
        if i < len(stages) - 1:
            add_arrow(s, x + box_w + 0.02, y + 0.55, gap - 0.04, 0.2, GREEN_MID)

    # Details below
    details = [
        ("Convolution",
         "A small filter (e.g., 3×3) slides across the image, computing dot products. "
         "Each filter learns to detect one pattern (an edge, a spot, a pustule). "
         "The network has dozens to hundreds of filters per layer."),
        ("Pooling",
         "Takes the maximum (or average) of a small region, halving the spatial size. "
         "Reduces computation and forces the network to focus on broader patterns. "
         "Typical size: 2×2 with stride 2."),
        ("Fully Connected",
         "After flattening to 1D, dense layers combine the learned features into a "
         "final decision. The last layer has one node per disease class."),
        ("Softmax",
         "Converts raw scores to probabilities that sum to 1.0. Lets us compute "
         "'confidence' as the probability of the winning class."),
    ]

    y2 = 4.1
    for name, desc in details:
        tb = s.shapes.add_textbox(Inches(0.75), Inches(y2), Inches(3.0), Inches(0.4))
        tf = tb.text_frame
        p = tf.paragraphs[0]
        p.text = name
        for run in p.runs:
            run.font.size = Pt(13)
            run.font.bold = True
            run.font.color.rgb = GREEN_DARK
            run.font.name = "Calibri"

        tb2 = s.shapes.add_textbox(Inches(3.6), Inches(y2), Inches(9.0), Inches(0.55))
        tf2 = tb2.text_frame
        tf2.word_wrap = True
        p2 = tf2.paragraphs[0]
        p2.text = desc
        for run in p2.runs:
            run.font.size = Pt(11)
            run.font.color.rgb = TEXT_DARK
            run.font.name = "Calibri"
        y2 += 0.65

    add_footer(s)


def slide_convolution(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "The Convolution Operation",
              "How a CNN 'sees' features in an image")

    # Visual: filter over image
    # Image grid
    img_left, img_top = 0.9, 2.0
    cell = 0.28
    for i in range(8):
        for j in range(8):
            shade = 0x80 + (i * 8 + j * 5) % 100
            cell_color = RGBColor(shade, shade + 20, shade - 20)
            c = s.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                Inches(img_left + i * cell), Inches(img_top + j * cell),
                Inches(cell), Inches(cell)
            )
            c.fill.solid()
            c.fill.fore_color.rgb = cell_color
            c.line.color.rgb = WHITE
            c.line.width = Pt(0.5)

    # Highlight 3x3 filter region
    hl = s.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(img_left + 2 * cell), Inches(img_top + 2 * cell),
        Inches(3 * cell), Inches(3 * cell)
    )
    hl.fill.background()
    hl.line.color.rgb = ORANGE_ACCENT
    hl.line.width = Pt(3)

    # Labels
    lbl = s.shapes.add_textbox(Inches(0.9), Inches(4.7), Inches(3.5), Inches(0.4))
    tf = lbl.text_frame
    p = tf.paragraphs[0]
    p.text = "Input Image (8×8 grid shown)"
    p.alignment = PP_ALIGN.CENTER
    for run in p.runs:
        run.font.size = Pt(11)
        run.font.bold = True
        run.font.color.rgb = TEXT_DARK
        run.font.name = "Calibri"

    # Filter box
    add_box(s, 5.0, 2.6, 1.0, 0.75, "3×3\nFilter", ORANGE_ACCENT, font_size=12)

    # Arrow
    add_arrow(s, 4.35, 2.85, 0.55, 0.25, ORANGE_ACCENT)

    # Output map
    out_left = 6.4
    for i in range(3):
        for j in range(3):
            c = s.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                Inches(out_left + i * cell), Inches(2.4 + j * cell),
                Inches(cell), Inches(cell)
            )
            c.fill.solid()
            c.fill.fore_color.rgb = GREEN_MID
            c.line.color.rgb = WHITE
            c.line.width = Pt(0.5)

    lbl2 = s.shapes.add_textbox(Inches(6.4), Inches(3.4), Inches(1.2), Inches(0.4))
    tf = lbl2.text_frame
    p = tf.paragraphs[0]
    p.text = "Feature\nMap"
    p.alignment = PP_ALIGN.CENTER
    for run in p.runs:
        run.font.size = Pt(11)
        run.font.bold = True
        run.font.color.rgb = GREEN_DARK
        run.font.name = "Calibri"

    # Explanation on right
    explain_left = 8.3
    explanations = [
        ("What happens",
         "The 3×3 filter is a small matrix of learned weights. It slides across the "
         "image, and at each position computes: sum(filter × image patch)."),
        ("What it means",
         "One filter detects one feature: a vertical edge, a brown spot, a yellow "
         "pustule. Different filters in the same layer detect different features."),
        ("Why it works",
         "The filter shares weights across the whole image — the same feature "
         "detector works wherever the disease appears."),
    ]
    y = 2.0
    for title, body in explanations:
        tb = s.shapes.add_textbox(
            Inches(explain_left), Inches(y), Inches(4.5), Inches(0.35)
        )
        tf = tb.text_frame
        p = tf.paragraphs[0]
        p.text = title
        for run in p.runs:
            run.font.size = Pt(13)
            run.font.bold = True
            run.font.color.rgb = GREEN_DARK
            run.font.name = "Calibri"

        tb2 = s.shapes.add_textbox(
            Inches(explain_left), Inches(y + 0.35), Inches(4.5), Inches(1.0)
        )
        tf2 = tb2.text_frame
        tf2.word_wrap = True
        p2 = tf2.paragraphs[0]
        p2.text = body
        for run in p2.runs:
            run.font.size = Pt(11)
            run.font.color.rgb = TEXT_DARK
            run.font.name = "Calibri"
        y += 1.4

    add_footer(s)


def slide_pooling(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "Pooling & Feature Maps",
              "Compressing information while keeping the important signal")

    # Left: pooling visual
    add_bullets(s, [
        "Pooling reduces the spatial size of feature maps",
        "Max pooling takes the highest value in each 2×2 region",
        "Average pooling takes the mean instead",
        "Result: 224×224 → 112×112 → 56×56 → …",
        "Benefits: fewer parameters, less overfitting, faster training",
    ], left=0.75, top=1.9, width=6.0, height=4.5, size=13)

    # Right: pooling visual
    y = 2.0
    add_box(s, 7.2, y, 1.8, 0.45, "4×4 Map", GREEN_PRIMARY, font_size=13)
    add_arrow(s, 9.1, y + 0.1, 0.5, 0.25, GREEN_MID)
    add_box(s, 9.7, y, 1.8, 0.45, "2×2 Pooled", GREEN_MID, font_size=13)
    add_arrow(s, 11.6, y + 0.1, 0.5, 0.25, GREEN_MID)
    add_box(s, 12.2, y, 1.0, 0.45, "1×1", ORANGE_ACCENT, font_size=11)

    # Show max-pooling example
    ex_left, ex_top, cell = 7.2, 3.0, 0.5
    labels = [["1", "3", "5", "6"], ["2", "8", "7", "4"], ["9", "2", "3", "1"], ["4", "6", "2", "5"]]
    for i, row in enumerate(labels):
        for j, val in enumerate(row):
            c = s.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                Inches(ex_left + i * cell), Inches(ex_top + j * cell),
                Inches(cell), Inches(cell)
            )
            c.fill.solid()
            c.fill.fore_color.rgb = GREEN_PALE
            c.line.color.rgb = GREEN_PRIMARY
            c.line.width = Pt(0.5)
            tf = c.text_frame
            tf.margin_left = Emu(0)
            tf.margin_right = Emu(0)
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            p.text = val
            for run in p.runs:
                run.font.size = Pt(12)
                run.font.bold = True
                run.font.color.rgb = TEXT_DARK
                run.font.name = "Calibri"

    # Arrow to pooled
    add_arrow(s, ex_left + 4 * cell + 0.15, ex_top + 0.9, 0.5, 0.25, ORANGE_ACCENT)

    # Pooled 2x2
    pooled = [["8", "7"], ["9", "5"]]
    pool_left = ex_left + 4 * cell + 0.7
    for i, row in enumerate(pooled):
        for j, val in enumerate(row):
            c = s.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                Inches(pool_left + i * cell), Inches(ex_top + 0.35 + j * cell),
                Inches(cell), Inches(cell)
            )
            c.fill.solid()
            c.fill.fore_color.rgb = ORANGE_LIGHT
            c.line.color.rgb = ORANGE_ACCENT
            c.line.width = Pt(1.5)
            tf = c.text_frame
            tf.margin_left = Emu(0)
            tf.margin_right = Emu(0)
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            p.text = val
            for run in p.runs:
                run.font.size = Pt(12)
                run.font.bold = True
                run.font.color.rgb = ORANGE_ACCENT
                run.font.name = "Calibri"

    # Explanation box
    box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                              Inches(7.2), Inches(5.5),
                              Inches(5.8), Inches(1.4))
    box.fill.solid()
    box.fill.fore_color.rgb = ORANGE_LIGHT
    box.line.color.rgb = ORANGE_ACCENT
    box.line.width = Pt(1.5)
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.2)
    tf.margin_top = Inches(0.1)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.text = ("Each 2×2 region collapses to its maximum. The pooling layer learns "
              "nothing — it just reduces data. But it forces the network to "
              "generalize: it can't memorize exact pixel positions.")
    for run in p.runs:
        run.font.size = Pt(11)
        run.font.color.rgb = TEXT_DARK
        run.font.name = "Calibri"

    add_footer(s)


def slide_full_pipeline(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "The Complete CNN Pipeline",
              "From field photo to actionable diagnosis")

    # Layer stack
    y = 1.9
    layers = [
        ("INPUT", "Field photo 224×224×3", GREEN_DARK, "Raw camera image"),
        ("BLOCK 1", "Conv(64) + ReLU + Pool", GREEN_PRIMARY, "Edges, colors, textures"),
        ("BLOCK 2", "Conv(128) + ReLU + Pool", GREEN_PRIMARY, "Spots, lesions, patterns"),
        ("BLOCK 3", "Conv(256) + ReLU + Pool", GREEN_MID, "Disease-specific features"),
        ("BLOCK 4", "Conv(512) + ReLU + Pool", GREEN_MID, "High-level structures"),
        ("GAP", "Global Average Pooling", ORANGE_ACCENT, "Final feature vector (1280-d)"),
        ("DENSE", "Fully Connected → N classes", ORANGE_ACCENT, "Class scores"),
        ("SOFTMAX", "Probability distribution", RED_WARN, "Confidence per class"),
    ]

    for i, (name, op, color, desc) in enumerate(layers):
        add_box(s, 0.75, y, 1.7, 0.45, name, color, font_size=11)
        add_box(s, 2.55, y, 4.4, 0.45, op, GREEN_PALE,
                text_color=TEXT_DARK, font_size=11, bold=False)
        add_box(s, 7.05, y, 5.5, 0.45, desc, WHITE,
                text_color=TEXT_GRAY, font_size=11, bold=False,
                shape=MSO_SHAPE.RECTANGLE)
        y += 0.55

    # Note at bottom
    tb = s.shapes.add_textbox(Inches(0.75), Inches(6.5), Inches(11.8), Inches(0.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = ("Each block reduces spatial size (224 → 112 → 56 → 28 → 14 → 7) while "
              "increasing channel depth (3 → 64 → 128 → 256 → 512). The network trades "
              "spatial detail for semantic understanding.")
    for run in p.runs:
        run.font.size = Pt(11)
        run.font.italic = True
        run.font.color.rgb = TEXT_GRAY
        run.font.name = "Calibri"

    add_footer(s)


def slide_why_cnn_plants(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "Why CNN Works for Plant Disease Diagnosis",
              "Visual symptoms are exactly what convolutions detect")

    # Four cards
    cards = [
        ("Symptom Detection",
         "Disease symptoms (spots, pustules, lesions, yellowing) are visual "
         "patterns. A convolution filter can learn to detect each.",
         GREEN_PRIMARY),
        ("Location Independence",
         "A rust pustule on the top-left of a leaf is the same disease as one on "
         "the bottom-right. Weight sharing handles this automatically.",
         GREEN_MID),
        ("Scale Invariance",
         "Early pooling layers let the network recognize features at multiple "
         "scales — small spots and large lesions both get caught.",
         ORANGE_ACCENT),
        ("Transfer Learning",
         "ImageNet-trained backbones already know edges, textures, colors. "
         "Fine-tuning for plant diseases requires far fewer labeled images.",
         RED_WARN),
    ]

    x = 0.75
    for title, desc, color in cards:
        add_box(s, x, 1.9, 2.85, 0.55, title, color, font_size=14)

        box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                  Inches(x), Inches(2.55),
                                  Inches(2.85), Inches(2.5))
        box.fill.solid()
        box.fill.fore_color.rgb = GREEN_PALE
        box.line.color.rgb = color
        box.line.width = Pt(1.5)
        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.15)
        tf.margin_right = Inches(0.15)
        tf.margin_top = Inches(0.15)
        tf.vertical_anchor = MSO_ANCHOR.TOP
        p = tf.paragraphs[0]
        p.text = desc
        for run in p.runs:
            run.font.size = Pt(11)
            run.font.color.rgb = TEXT_DARK
            run.font.name = "Calibri"

        x += 3.05

    # Bottom callout
    box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                              Inches(0.75), Inches(5.4),
                              Inches(11.8), Inches(1.5))
    box.fill.solid()
    box.fill.fore_color.rgb = BLUE_PALE
    box.line.color.rgb = BLUE_INFO
    box.line.width = Pt(2)
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.3)
    tf.margin_right = Inches(0.3)
    tf.margin_top = Inches(0.15)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.text = ("Real-world proof: Our MobileNetV2-trained coffee model achieves 93.42% "
              "test accuracy on 380 held-out images across 4 classes "
              "(healthy, leaf_rust, cercospora, phoma). Coffee Leaf Rust — a leading "
              "economic threat to Ethiopian smallholders — is detected at 0.91 F1.")
    for run in p.runs:
        run.font.size = Pt(13)
        run.font.color.rgb = TEXT_DARK
        run.font.name = "Calibri"

    add_footer(s)


def slide_cnn_code_data(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "CNN in Code — Data Loading",
              "From folder of images to PyTorch Dataset")

    code = '''from torchvision import datasets, transforms
from torch.utils.data import DataLoader

# Preprocessing (same for train & eval)
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# ImageFolder auto-labels from subfolder names
train_ds = datasets.ImageFolder(
    "data/train",   # data/train/healthy/, data/train/leaf_rust/, ...
    transform=transform
)
val_ds = datasets.ImageFolder("data/val", transform=transform)

train_loader = DataLoader(train_ds, batch_size=16, shuffle=True)
val_loader = DataLoader(val_ds, batch_size=16, shuffle=False)

print(f"Classes: {train_ds.classes}")'''

    add_code_block(s, code, top=1.9, height=4.6, size=12)

    # Note
    tb = s.shapes.add_textbox(Inches(0.75), Inches(6.6), Inches(11.8), Inches(0.5))
    tf = tb.text_frame
    p = tf.paragraphs[0]
    p.text = "ImageFolder maps each subfolder to a class index automatically — folder name = class name."
    for run in p.runs:
        run.font.size = Pt(11)
        run.font.italic = True
        run.font.color.rgb = TEXT_GRAY
        run.font.name = "Calibri"

    add_footer(s)


def slide_cnn_code_model(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "CNN in Code — Building the Model",
              "Transfer learning with MobileNetV2")

    code = '''import torch.nn as nn
from torchvision import models

# Start from ImageNet-pretrained MobileNetV2
model = models.mobilenet_v2(
    weights=models.MobileNet_V2_Weights.IMAGENET1K_V1
)

# Freeze all base features
for p in model.features.parameters():
    p.requires_grad = False

# Replace classifier for our number of classes
num_classes = 4  # healthy, leaf_rust, cercospora, phoma
model.classifier[1] = nn.Linear(
    model.last_channel,
    num_classes
)

# Move to device
device = torch.device("cpu")
model.to(device)

print(f"Ready: {num_classes} classes")'''

    add_code_block(s, code, top=1.9, height=4.6, size=12)

    tb = s.shapes.add_textbox(Inches(0.75), Inches(6.6), Inches(11.8), Inches(0.5))
    tf = tb.text_frame
    p = tf.paragraphs[0]
    p.text = "Transfer learning: reuse ImageNet features, train only the new classifier (10x faster, needs far less data)."
    for run in p.runs:
        run.font.size = Pt(11)
        run.font.italic = True
        run.font.color.rgb = TEXT_GRAY
        run.font.name = "Calibri"

    add_footer(s)


def slide_cnn_code_training(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "CNN in Code — Training Loop",
              "What happens each epoch")

    code = '''import torch
import torch.nn as nn
from sklearn.metrics import f1_score

criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

best_val_acc = 0.0
EPOCHS = 12

for epoch in range(EPOCHS):
    # ---- TRAINING ----
    model.train()
    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        logits = model(images)
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()

    # ---- VALIDATION ----
    model.eval()
    preds, targets = [], []
    with torch.no_grad():
        for images, labels in val_loader:
            logits = model(images.to(device))
            preds.extend(logits.argmax(1).cpu().tolist())
            targets.extend(labels.tolist())

    val_acc = 100 * sum(p == t for p, t in zip(preds, targets)) / len(targets)
    print(f"Epoch {epoch+1}: val_acc = {val_acc:.2f}%")

    # ---- SAVE BEST ----
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        torch.save(model.state_dict(), "coffee_model.pth")'''

    add_code_block(s, code, top=1.9, height=4.7, size=10)

    add_footer(s)


def slide_cnn_results(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "Real Training Results — AgriMind Models",
              "Numbers from actual runs on Ethiopian data")

    # Wheat card
    add_box(s, 0.75, 1.9, 5.9, 0.55, "WHEAT (Holeta dataset)", GREEN_PRIMARY, font_size=15)

    wheat_rows = [
        ("Images", "407 unique Ethiopian field"),
        ("Classes", "healthy, septoria, stripe_rust"),
        ("Best val_acc", "94.46% (epoch 10)"),
        ("Test accuracy", "93.42%"),
        ("Macro F1", "0.9328"),
        ("Per-class F1", "0.89 – 0.96 (all classes ≥ 0.89)"),
    ]
    y = 2.55
    for label, val in wheat_rows:
        add_box(s, 0.75, y, 2.6, 0.5, label, GREEN_PALE,
                text_color=TEXT_DARK, font_size=11, bold=False)
        add_box(s, 3.45, y, 3.2, 0.5, val, WHITE,
                text_color=TEXT_DARK, font_size=11, bold=False,
                shape=MSO_SHAPE.RECTANGLE)
        y += 0.55

    # Coffee card
    add_box(s, 6.8, 1.9, 5.9, 0.55, "COFFEE (2,529 images)", ORANGE_ACCENT, font_size=15)

    coffee_rows = [
        ("Images", "2,529 unique (after pHash dedup)"),
        ("Classes", "healthy, leaf_rust, cercospora, phoma"),
        ("Train split", "1,770 images (grouped CV)"),
        ("Test accuracy", "93.42%"),
        ("Macro F1", "0.9328"),
        ("Leaf Rust F1", "0.9091 (Ethiopia's key disease)"),
    ]
    y = 2.55
    for label, val in coffee_rows:
        add_box(s, 6.8, y, 2.6, 0.5, label, ORANGE_LIGHT,
                text_color=TEXT_DARK, font_size=11, bold=False)
        add_box(s, 9.5, y, 3.2, 0.5, val, WHITE,
                text_color=TEXT_DARK, font_size=11, bold=False,
                shape=MSO_SHAPE.RECTANGLE)
        y += 0.55

    # Warning at bottom
    box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                              Inches(0.75), Inches(6.0),
                              Inches(11.8), Inches(0.95))
    box.fill.solid()
    box.fill.fore_color.rgb = RED_PALE
    box.line.color.rgb = RED_WARN
    box.line.width = Pt(2)
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.25)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.text = ("⚠ Honest limitation: Both models are EXPERIMENTAL CANDIDATES. "
              "No independent field validation on other farms/regions. "
              "Do NOT deploy until external field data confirms these results.")
    for run in p.runs:
        run.font.size = Pt(12)
        run.font.color.rgb = RED_WARN
        run.font.name = "Calibri"

    add_footer(s)


def slide_cnn_output(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "What Output to Expect — CNN",
              "Interpreting the model's response")

    # Example output
    add_box(s, 0.75, 1.9, 11.8, 0.55, "Sample CNN Output (JSON)",
            GREEN_DARK, font_size=15)

    code = '''{
  "prediction_id": 4523,
  "disease": "leaf_rust",
  "confidence": 0.9091,
  "recommendation": "Remove affected leaves. Apply copper-based fungicide.",
  "symptoms": "Orange-yellow powdery spots on underside of leaves.",
  "prevention": "Improve air circulation. Maintain shade.",
  "expert_help": "Consult if rust covers >30% of tree.",
  "diagnosed_by": "farmer@example.com"
}'''

    add_code_block(s, code, top=2.55, height=2.5, size=11)

    # Field meanings
    add_bullets(s, [
        "disease — the predicted class name (must be in the trained class list)",
        "confidence — softmax probability of the winning class (0.0 to 1.0)",
        "recommendation / symptoms / prevention — expert-reviewed text keyed by class",
        "expert_help — escalation advice when the situation is urgent",
        "prediction_id — database row ID for feedback tracking",
    ], top=5.2, size=13, height=2.0)

    add_footer(s)


def slide_cnn_limitations(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "CNN Limitations — What CNNs Cannot Do",
              "Understanding the boundaries")

    limitations = [
        ("Closed-set classification",
         "A CNN predicts one of its trained classes. Feed it a coffee leaf to a "
         "tomato-trained model and it will confidently output 'tomato___late_blight'. "
         "It has no built-in way to say 'this is not in my training set.'"),
        ("Domain shift",
         "Trained on public data (PlantVillage, Kaggle) → tested on Ethiopian farms "
         "→ accuracy drops from 85% to 34% (we measured this on wheat)."),
        ("Requires labeled data",
         "Every disease class needs hundreds of expert-labeled examples. Rare "
         "diseases remain impossible to model."),
        ("No environmental context",
         "A leaf photo alone cannot use altitude, humidity, growth stage, or variety "
         "— yet a human agronomist uses all of these."),
    ]

    y = 1.9
    for i, (title, desc) in enumerate(limitations):
        # Warning icon
        add_box(s, 0.75, y, 0.5, 0.5, "!", RED_WARN, font_size=18)

        tb = s.shapes.add_textbox(
            Inches(1.4), Inches(y), Inches(11.1), Inches(0.35)
        )
        tf = tb.text_frame
        p = tf.paragraphs[0]
        p.text = title
        for run in p.runs:
            run.font.size = Pt(14)
            run.font.bold = True
            run.font.color.rgb = RED_WARN
            run.font.name = "Calibri"

        tb2 = s.shapes.add_textbox(
            Inches(1.4), Inches(y + 0.35), Inches(11.1), Inches(0.8)
        )
        tf2 = tb2.text_frame
        tf2.word_wrap = True
        p2 = tf2.paragraphs[0]
        p2.text = desc
        for run in p2.runs:
            run.font.size = Pt(12)
            run.font.color.rgb = TEXT_DARK
            run.font.name = "Calibri"

        y += 1.25

    add_footer(s)


# ---- FUSION SLIDES ----

def slide_what_is_fusion(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "What is a Fusion Layer?",
              "Combining image + environmental data for smarter diagnosis")

    # Definition
    box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                              Inches(0.75), Inches(1.8),
                              Inches(11.8), Inches(1.3))
    box.fill.solid()
    box.fill.fore_color.rgb = ORANGE_LIGHT
    box.line.color.rgb = ORANGE_ACCENT
    box.line.width = Pt(2)
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.3)
    tf.margin_right = Inches(0.3)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.text = ("A Fusion Layer is a neural network component that combines outputs "
              "from two different models — here, an image CNN and a tabular "
              "(numeric) model — into a single prediction. It mimics how a human "
              "expert looks at a leaf AND considers the climate, season, and variety.")
    for run in p.runs:
        run.font.size = Pt(15)
        run.font.color.rgb = TEXT_DARK
        run.font.name = "Calibri"

    # Key ideas
    add_bullets(s, [
        "Also called: multimodal fusion, feature fusion, late fusion, early fusion",
        "Two input streams: image features + tabular features",
        "One merged feature vector → one classification decision",
        "Grounded in how agronomists actually diagnose: image + context",
    ], top=3.3, size=15)

    # Visual concept
    y = 5.3
    add_box(s, 0.75, y, 2.5, 0.6, "Leaf Image", GREEN_PRIMARY, font_size=13)
    add_box(s, 0.75, y + 0.8, 2.5, 0.6, "GPS + Altitude + Variety", ORANGE_ACCENT, font_size=12)

    add_arrow(s, 3.35, y + 0.2, 0.6, 0.2, GREEN_PRIMARY)
    add_arrow(s, 3.35, y + 1.0, 0.6, 0.2, ORANGE_ACCENT)

    add_box(s, 4.05, y + 0.35, 2.5, 0.7, "FUSION\nLAYER", PURPLE, font_size=14)

    add_arrow(s, 6.65, y + 0.55, 0.6, 0.2, PURPLE)

    add_box(s, 7.35, y + 0.35, 3.5, 0.7, "Diagnosis + Confidence", RED_WARN, font_size=13)

    add_footer(s)


def slide_why_fusion(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "Why We Need Fusion — The Problem",
              "CNNs alone can be dangerously wrong without context")

    # Scenario
    add_box(s, 0.75, 1.9, 5.9, 0.55, "SCENARIO: Wheat Leaf, Yellow Streaks",
            GREEN_DARK, font_size=14)

    scenarios = [
        ("Altitude: 2,400m", "Highland (Dega)", GREEN_PALE),
        ("Humidity: 90%", "High-risk zone", GREEN_PALE),
        ("Variety: Kulumsa", "Stripe-rust susceptible", GREEN_PALE),
        ("Season: Belg (Mar-Apr)", "Peak rust season", GREEN_PALE),
        ("Visual: Yellow streaks", "Ambiguous symptom", GREEN_PALE),
    ]
    y = 2.55
    for label, val, _ in scenarios:
        add_box(s, 0.75, y, 2.6, 0.5, label, WHITE,
                text_color=TEXT_DARK, font_size=11, bold=False,
                shape=MSO_SHAPE.RECTANGLE)
        add_box(s, 3.45, y, 3.2, 0.5, val, GREEN_PALE,
                text_color=TEXT_DARK, font_size=11, bold=False)
        y += 0.55

    # vs
    add_box(s, 6.8, 1.9, 5.9, 0.55, "WITHOUT FUSION", RED_WARN, font_size=14)

    tb = s.shapes.add_textbox(Inches(6.8), Inches(2.55), Inches(5.9), Inches(3.0))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = (
        "The CNN sees the leaf. Yellow streaks. Could be:\n\n"
        "  • Nitrogen deficiency (30%)\n"
        "  • Septoria (40%)\n"
        "  • Stripe rust (30%)\n\n"
        "Result: LOW CONFIDENCE. Wrong treatment may follow."
    )
    for run in p.runs:
        run.font.size = Pt(13)
        run.font.color.rgb = TEXT_DARK
        run.font.name = "Calibri"

    add_box(s, 6.8, 5.5, 5.9, 0.55, "WITH FUSION", PURPLE, font_size=14)

    tb2 = s.shapes.add_textbox(Inches(6.8), Inches(6.1), Inches(5.9), Inches(0.9))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    p2 = tf2.paragraphs[0]
    p2.text = (
        "Fusion layer sees: image + altitude 2,400m + 90% humidity + Kulumsa "
        "variety + Belg season.\n\n"
        "Result: STRIKE RUST at 92% confidence."
    )
    for run in p2.runs:
        run.font.size = Pt(12)
        run.font.color.rgb = TEXT_DARK
        run.font.name = "Calibri"

    add_footer(s)


def slide_fusion_architecture(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "Fusion Architecture — Two Branches",
              "Visual path + Tabular path → merged prediction")

    # Top branch (visual)
    add_box(s, 0.75, 1.9, 2.5, 0.5, "IMAGE", GREEN_PRIMARY, font_size=13)
    add_arrow(s, 3.35, 2.05, 0.5, 0.2, GREEN_PRIMARY)
    add_box(s, 3.95, 1.9, 3.0, 0.5, "CNN Backbone (MobileNetV2)", GREEN_MID, font_size=12)
    add_arrow(s, 7.05, 2.05, 0.5, 0.2, GREEN_PRIMARY)
    add_box(s, 7.65, 1.9, 2.5, 0.5, "512-d Vector", GREEN_LIGHT,
            text_color=TEXT_DARK, font_size=12)

    # Bottom branch (tabular)
    add_box(s, 0.75, 3.0, 2.5, 0.5, "METADATA", ORANGE_ACCENT, font_size=13)
    add_arrow(s, 3.35, 3.15, 0.5, 0.2, ORANGE_ACCENT)
    add_box(s, 3.95, 3.0, 3.0, 0.5, "Dense Network (MLP)", ORANGE_LIGHT,
            text_color=TEXT_DARK, font_size=12)
    add_arrow(s, 7.05, 3.15, 0.5, 0.2, ORANGE_ACCENT)
    add_box(s, 7.65, 3.0, 2.5, 0.5, "32-d Vector", ORANGE_LIGHT,
            text_color=TEXT_DARK, font_size=12)

    # Fusion
    add_arrow(s, 10.2, 2.2, 0.4, 0.2, GREEN_PRIMARY)
    add_arrow(s, 10.2, 3.2, 0.4, 0.2, ORANGE_ACCENT)
    add_box(s, 10.7, 2.35, 2.0, 0.7, "FUSION\nLAYER", PURPLE, font_size=13)

    # Output
    add_arrow(s, 10.8, 3.25, 0.2, 0.3, PURPLE)
    add_box(s, 9.5, 4.0, 3.2, 0.55, "SOFTMAX → Classes", RED_WARN, font_size=12)

    # Two fusion strategies
    add_box(s, 0.75, 4.9, 5.9, 0.55, "LATE FUSION (Simple)", PURPLE, font_size=14)

    tb = s.shapes.add_textbox(Inches(0.75), Inches(5.5), Inches(5.9), Inches(1.7))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = (
        "1. Get 512-d image vector from CNN\n"
        "2. Get 32-d metadata vector from MLP\n"
        "3. Concatenate: [512 + 32] = 544-d vector\n"
        "4. Feed into final dense layers → softmax"
    )
    for run in p.runs:
        run.font.size = Pt(11)
        run.font.color.rgb = TEXT_DARK
        run.font.name = "Calibri"

    add_box(s, 6.8, 4.9, 5.9, 0.55, "GATED ATTENTION (Advanced)", PURPLE, font_size=14)

    tb2 = s.shapes.add_textbox(Inches(6.8), Inches(5.5), Inches(5.9), Inches(1.7))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    p2 = tf2.paragraphs[0]
    p2.text = (
        "1. Metadata branch produces attention weights\n"
        "2. Weights mask out impossible image features\n"
        "3. E.g., '0% enset in Wurch zone' → lower enset probability"
    )
    for run in p2.runs:
        run.font.size = Pt(11)
        run.font.color.rgb = TEXT_DARK
        run.font.name = "Calibri"

    add_footer(s)


def slide_fusion_code(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "Fusion in Code — Two-Branch Model",
              "PyTorch implementation of a fusion network")

    code = '''import torch
import torch.nn as nn
from torchvision import models

class FusionModel(nn.Module):
    def __init__(self, num_classes=4, num_tabular_features=16):
        super().__init__()

        # ---- Branch 1: image ----
        base = models.mobilenet_v2(
            weights=models.MobileNet_V2_Weights.IMAGENET1K_V1
        )
        self.cnn = base.features
        self.pool = nn.AdaptiveAvgPool2d(1)  # -> 1280-d

        # ---- Branch 2: tabular ----
        self.tabular = nn.Sequential(
            nn.Linear(num_tabular_features, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
        )

        # ---- Fusion + classifier ----
        self.fusion = nn.Sequential(
            nn.Linear(1280 + 32, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes),
        )

    def forward(self, image, tabular):
        # Image path
        x = self.cnn(image)
        x = self.pool(x).flatten(1)   # (B, 1280)

        # Tabular path
        t = self.tabular(tabular)     # (B, 32)

        # Fusion
        fused = torch.cat([x, t], dim=1)  # (B, 1312)
        return self.fusion(fused)'''

    add_code_block(s, code, top=1.9, height=5.0, size=10)

    add_footer(s)


def slide_fusion_training(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "Fusion Training — Setup & Requirements",
              "What you need before fusion is trainable")

    # Requirements
    add_bullets(s, [
        "Every image must have associated metadata (GPS, altitude, variety, weather)",
        "Labels must be expert-verified (not crowd-sourced)",
        "Metadata schema must be fixed at training time (feature vector length)",
        "Missing metadata must be handled (fill with regional averages, or exclude)",
        "Minimum dataset: 500+ labeled cases with full metadata per crop",
    ], top=1.9, size=13, height=2.3)

    # Code
    code = '''# Training loop for fusion model
model = FusionModel(num_classes=4, num_tabular_features=16).to(device)

for epoch in range(EPOCHS):
    model.train()
    for images, tabular, labels in train_loader:
        images = images.to(device)
        tabular = tabular.to(device).float()
        labels = labels.to(device)

        optimizer.zero_grad()
        logits = model(images, tabular)
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()'''

    add_code_block(s, code, top=4.5, height=2.0, size=11)

    add_footer(s)


def slide_fusion_output(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "Fusion Output — Context-Aware Diagnosis",
              "What a fused prediction looks like")

    # Example output
    code = '''{
  "prediction_id": 8842,
  "disease": "stripe_rust",
  "confidence": 0.9240,
  "confidence_level": "high",
  "contributing_factors": {
    "image_features": {"weight": 0.62, "signal": "yellow_streaks"},
    "context": {
      "altitude": "2400m",
      "humidity_7d": "90%",
      "variety": "Kulumsa (susceptible)",
      "season": "Belg"
    }
  },
  "recommendation": "Apply propiconazole. Scout other fields within 5km.",
  "explanation": "Yellow streaks + high humidity + susceptible variety during Belg = stripe rust consistent.",
  "alternative_diagnoses": [
    {"disease": "septoria", "probability": 0.041},
    {"disease": "nitrogen_deficiency", "probability": 0.035}
  ]
}'''

    add_code_block(s, code, top=1.9, height=4.2, size=10)

    # Benefits
    add_box(s, 0.75, 6.2, 11.8, 0.7, "Why this is better than pure CNN output:",
            PURPLE, font_size=13)

    tb = s.shapes.add_textbox(Inches(0.75), Inches(6.55), Inches(11.8), Inches(0.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = ("Explainable (contributing_factors), higher confidence when context "
              "agrees with image, low confidence when context disagrees.")
    for run in p.runs:
        run.font.size = Pt(11)
        run.font.color.rgb = TEXT_DARK
        run.font.name = "Calibri"

    add_footer(s)


def slide_cnn_vs_fusion(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "CNN vs Fusion — Side-by-Side",
              "When to use each")

    # Headers
    add_box(s, 0.75, 1.9, 3.5, 0.5, "", GREEN_PALE, font_size=11)
    add_box(s, 4.35, 1.9, 3.9, 0.5, "CNN Only", GREEN_PRIMARY, font_size=14)
    add_box(s, 8.35, 1.9, 4.2, 0.5, "CNN + Fusion", PURPLE, font_size=14)

    rows = [
        ("Inputs", "Image only", "Image + metadata"),
        ("Data needed", "Labeled photos", "Photos + GPS, altitude, variety"),
        ("Training effort", "Low (weeks)", "High (months)"),
        ("Accuracy gain", "Strong baseline", "+3–8% when context is informative"),
        ("Explainability", "Class + confidence", "Class + confidence + factors"),
        ("Deployment effort", "Straightforward", "Needs metadata pipeline"),
        ("Best for", "MVP, quick pilot", "Production, high-stakes diagnosis"),
    ]

    y = 2.5
    for label, cnn, fusion in rows:
        add_box(s, 0.75, y, 3.5, 0.5, label, GREEN_PALE,
                text_color=TEXT_DARK, font_size=11, bold=True,
                shape=MSO_SHAPE.RECTANGLE)
        add_box(s, 4.35, y, 3.9, 0.5, cnn, WHITE,
                text_color=TEXT_DARK, font_size=11, bold=False,
                shape=MSO_SHAPE.RECTANGLE)
        add_box(s, 8.35, y, 4.2, 0.5, fusion, WHITE,
                text_color=TEXT_DARK, font_size=11, bold=False,
                shape=MSO_SHAPE.RECTANGLE)
        y += 0.55

    # Bottom recommendation
    box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                              Inches(0.75), Inches(6.5),
                              Inches(11.8), Inches(0.55))
    box.fill.solid()
    box.fill.fore_color.rgb = ORANGE_LIGHT
    box.line.color.rgb = ORANGE_ACCENT
    box.line.width = Pt(2)
    tf = box.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.text = "AgriMind Path: CNN first (2026 pilot) → Fusion after 500+ labeled cases (2027)"
    p.alignment = PP_ALIGN.CENTER
    for run in p.runs:
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.color.rgb = ORANGE_ACCENT
        run.font.name = "Calibri"

    add_footer(s)


def slide_roadmap(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "AgriMind Technical Roadmap",
              "What to build, in what order")

    phases = [
        ("NOW", "Customer Discovery", "5–8 DA interviews, 2–3 buyer interviews", GREEN_PRIMARY),
        ("WEEKS 2-3", "Collector Mode", "Build metadata-enforced case capture", GREEN_MID),
        ("WEEKS 3-4", "ARC Outreach", "Contact Jimma ARC + Kulumsa ARC", ORANGE_ACCENT),
        ("MONTH 2-3", "Pilot", "5–10 DAs, 4-week trial, collect labeled cases", ORANGE_ACCENT),
        ("MONTH 4-6", "Evidence Synthesis", "Re-score matrices from pilot data", RED_WARN),
        ("MONTH 6-9", "CNN Expansion", "Retrain coffee/wheat with new field data", PURPLE),
        ("MONTH 9-12", "Fusion MVP", "Train first multimodal model (needs 500+ cases)", PURPLE),
        ("2027", "Scale", "Deploy fusion, expand to maize/teff/enset", GREEN_DARK),
    ]

    y = 1.9
    for label, title, desc, color in phases:
        add_box(s, 0.75, y, 1.9, 0.55, label, color, font_size=11)
        add_box(s, 2.75, y, 3.2, 0.55, title, WHITE,
                text_color=TEXT_DARK, font_size=12, bold=True,
                shape=MSO_SHAPE.RECTANGLE)
        add_box(s, 6.05, y, 6.5, 0.55, desc, GREEN_PALE,
                text_color=TEXT_DARK, font_size=11, bold=False,
                shape=MSO_SHAPE.RECTANGLE)
        y += 0.65

    add_footer(s)


def slide_summary(prs):
    s = new_slide(prs)
    add_bg_bar(s)
    add_title(s, "Summary & Key Takeaways",
              "What to remember")

    # Left column
    add_box(s, 0.75, 1.9, 5.9, 0.55, "CNN — What It Is", GREEN_PRIMARY, font_size=15)

    add_bullets(s, [
        "Learns spatial patterns directly from pixels",
        "4 stages: convolution → pooling → dense → softmax",
        "Transfer learning (MobileNetV2) makes training fast",
        "AgriMind coffee model: 93.42% accuracy, 0.93 macro F1",
        "AgriMind wheat model: 93.42% test accuracy",
    ], left=0.75, top=2.55, width=5.9, height=2.5, size=12)

    # Right column
    add_box(s, 6.8, 1.9, 5.9, 0.55, "Fusion — What It Will Do", PURPLE, font_size=15)

    add_bullets(s, [
        "Combines image + environmental context",
        "Two branches: CNN + tabular MLP",
        "Fusion layer concatenates or attends",
        "Requires 500+ labeled cases with metadata",
        "Deployment target: 2027 (not 2026)",
    ], left=6.8, top=2.55, width=5.9, height=2.5, size=12)

    # Bottom callout
    box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                              Inches(0.75), Inches(5.4),
                              Inches(11.8), Inches(1.5))
    box.fill.solid()
    box.fill.fore_color.rgb = BLUE_PALE
    box.line.color.rgb = BLUE_INFO
    box.line.width = Pt(2)
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.3)
    tf.margin_right = Inches(0.3)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.text = ("Next step: Customer discovery. Before we build fusion, we need to "
              "know what DAs actually need. Book 5–8 DA interviews this week. "
              "Collector Mode in weeks 2–3 produces the metadata that makes fusion "
              "possible in 2027.")
    for run in p.runs:
        run.font.size = Pt(13)
        run.font.color.rgb = TEXT_DARK
        run.font.name = "Calibri"

    add_footer(s)


# ==================== MAIN ====================

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Build 24 slides
    slide_title(prs)
    slide_agenda(prs)
    slide_what_is_cnn(prs)
    slide_cnn_architecture(prs)
    slide_convolution(prs)
    slide_pooling(prs)
    slide_full_pipeline(prs)
    slide_why_cnn_plants(prs)
    slide_cnn_code_data(prs)
    slide_cnn_code_model(prs)
    slide_cnn_code_training(prs)
    slide_cnn_results(prs)
    slide_cnn_output(prs)
    slide_cnn_limitations(prs)
    slide_what_is_fusion(prs)
    slide_why_fusion(prs)
    slide_fusion_architecture(prs)
    slide_fusion_code(prs)
    slide_fusion_training(prs)
    slide_fusion_output(prs)
    slide_cnn_vs_fusion(prs)
    slide_roadmap(prs)
    slide_summary(prs)

    prs.save(str(OUTPUT_FILE))
    print(f"\n✅ Presentation saved!")
    print(f"   File: {OUTPUT_FILE}")
    print(f"   Slides: {len(prs.slides)}")
    print(f"   Size: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()