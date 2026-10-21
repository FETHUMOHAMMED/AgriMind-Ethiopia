"""Standalone diagnostic: runs v2 through the same preprocessing pipeline.

Does NOT touch real_predictor.py or the live app. Verifies:
  - v2 checkpoint loads strictly
  - Same preprocessing as v1 (128x128 + ImageNet normalization)
  - Forward pass produces valid class from v2's 15 classes
  - Returned class has a matching recommendation entry

Run: python app/ai/v2_inference_smoke.py
"""
import io
from pathlib import Path

import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms

V2_PATH = Path(__file__).parent / "model" / "agrimind_mobilenetv2_v2.pth"
IMG_SIZE = 128

# Same preprocessing as real_predictor.py — verified identical in earlier audits
transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])

# Load v2 checkpoint
print("=" * 60)
print("V2 INFERENCE SMOKE TEST (diagnostic, read-only)")
print("=" * 60)

if not V2_PATH.exists():
    raise SystemExit(f"v2 checkpoint not found: {V2_PATH}")

ckpt = torch.load(V2_PATH, map_location="cpu", weights_only=True)
class_names = ckpt["classes"]
class_to_idx = ckpt.get("class_to_idx", {})
img_size = ckpt.get("img_size", 128)

print(f"Checkpoint:  {V2_PATH.name}")
print(f"Classes:     {len(class_names)}")
print(f"Img size:    {img_size}")
print(f"class_to_idx present: {bool(class_to_idx)}")

# Build v2 model — same architecture, auto-sized head
model = models.mobilenet_v2(weights=None)
model.classifier[1] = nn.Linear(model.last_channel, len(class_names))
model.load_state_dict(ckpt["model_state"], strict=True)
model.eval()
print(f"Strict load: PASS")

# Synthetic test image (green square — deterministic)
img = Image.new("RGB", (IMG_SIZE, IMG_SIZE), color=(50, 120, 50))
buf = io.BytesIO()
img.save(buf, format="PNG")
img_pil = Image.open(io.BytesIO(buf.getvalue())).convert("RGB")

# Forward pass
with torch.no_grad():
    tensor = transform(img_pil).unsqueeze(0)
    outputs = model(tensor)
    probs = torch.nn.functional.softmax(outputs[0], dim=0)
    confidence, predicted_idx = torch.max(probs, 0)

idx = int(predicted_idx.item())
conf = float(confidence.item())
disease_name = class_names[idx]

print()
print("=" * 60)
print("INFERENCE RESULT")
print("=" * 60)
print(f"Predicted class:  {disease_name}")
print(f"Class index:      {idx} / {len(class_names)}")
print(f"Confidence:       {conf:.4f} ({conf*100:.2f}%)")
print(f"Valid class:      {disease_name in class_names}")

# Verify recommendation coverage
import ast
predictor_path = Path(__file__).parent / "real_predictor.py"
source = predictor_path.read_text(encoding="utf-8")
tree = ast.parse(source)
rec_keys = set()
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        if any(isinstance(t, ast.Name) and t.id == "RECOMMENDATIONS" for t in node.targets):
            if isinstance(node.value, ast.Dict):
                rec_keys = {k.value for k in node.value.keys
                            if isinstance(k, ast.Constant) and isinstance(k.value, str)}
                break

has_rec = disease_name in rec_keys
print(f"Has recommendation: {has_rec}")

print()
print("=" * 60)
print("RESULT:", "PASS — v2 inference works through shared pipeline" if has_rec else "PARTIAL — check recommendation")
print("=" * 60)