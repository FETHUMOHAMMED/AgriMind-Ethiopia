"""One-shot patch: fix add_bullets() to handle empty-string level."""
from pathlib import Path

f = Path("generate_presentation.py")
content = f.read_text(encoding="utf-8")

old = '''        if isinstance(item, tuple):
            level, text = item
        else:
            level, text = 0, item
        p = tf.paragraphs[0] if first else tf.add_paragraph()'''

new = '''        if isinstance(item, tuple):
            level, text = item
            if level is None or level == "":
                level = 0
            else:
                level = int(level)
        else:
            level, text = 0, item
        p = tf.paragraphs[0] if first else tf.add_paragraph()'''

if old in content:
    content = content.replace(old, new)
    print("✅ Fix applied: add_bullets now handles empty-string level")
else:
    print("⚠️ Target not found — checking alternate pattern...")
    # Fallback: try without p assignment line
    alt_old = '''        if isinstance(item, tuple):
            level, text = item
        else:
            level, text = 0, item'''
    alt_new = '''        if isinstance(item, tuple):
            level, text = item
            if level is None or level == "":
                level = 0
            else:
                level = int(level)
        else:
            level, text = 0, item'''
    if alt_old in content:
        content = content.replace(alt_old, alt_new)
        print("✅ Fix applied via alternate pattern")
    else:
        print("❌ Neither pattern found — manual edit needed")

f.write_text(content, encoding="utf-8")
print("File saved.")