"""Diagnose class distribution in flat_crops dataset + 5000-subset simulation."""
import random
from collections import Counter
from torchvision import datasets

# ✅ Absolute path — works from any working directory
DATA_DIR = r"C:\projects\AgriMind-Ethiopia\backend\app\ai\datasets\flat_crops"
MODEL_PATH = r"C:\projects\AgriMind-Ethiopia\backend\app\ai\model\agrimind_mobilenetv2.pth"
SUBSET_SIZE = 5000

# ---- 1. Dataset class distribution ----
ds = datasets.ImageFolder(DATA_DIR)
classes = ds.classes
targets = ds.targets

print("=" * 70)
print(f"FULL DATASET: {len(ds)} images, {len(classes)} classes")
print("=" * 70)

counts = Counter(targets)
print("\nPer-class image counts (sorted ascending — rarest first):")
for idx in sorted(counts.keys(), key=lambda i: counts[i]):
    print(f"  [{idx:2d}] {classes[idx]:40s} {counts[idx]:6d}")

# ---- 2. Simulate the exact 5000-image training subset ----
random.seed(42)
if SUBSET_SIZE < len(ds):
    idxs = random.sample(range(len(ds)), SUBSET_SIZE)
    subset_targets = [targets[i] for i in idxs]
    subset_counts = Counter(subset_targets)
    print(f"\n{'=' * 70}")
    print(f"TRAINING SUBSET SIMULATION (seed=42, {SUBSET_SIZE} images)")
    print(f"{'=' * 70}")
    print(f"\nApproximate training examples per class (~80% of subset):")
    zero_count = 0
    low_count = 0
    for idx in range(len(classes)):
        total = subset_counts.get(idx, 0)
        approx_train = int(0.8 * total)
        flag = ""
        if approx_train == 0:
            flag = " 🔴 NEVER SEEN"
            zero_count += 1
        elif approx_train < 10:
            flag = " ⚠️ LOW"
            low_count += 1
        print(f"  [{idx:2d}] {classes[idx]:40s} train≈{approx_train:4d}{flag}")

    print(f"\n{'=' * 70}")
    print(f"🔴 Classes with ZERO training samples:  {zero_count}")
    print(f"⚠️ Classes with <10 training samples:   {low_count}")
    print(f"   These will show F1 = 0.00 in evaluation. Guaranteed.")
    print(f"{'=' * 70}")
else:
    print(f"\n⚠️ Dataset ({len(ds)}) is smaller than SUBSET_SIZE ({SUBSET_SIZE}). All images used.")

# ---- 3. What classes does the saved model claim to know? ----
print(f"\n{'=' * 70}")
print("MODEL CHECKPOINT — what classes was it trained on?")
print(f"{'=' * 70}")
import torch
try:
    ckpt = torch.load(MODEL_PATH, map_location="cpu", weights_only=False)
    model_classes = ckpt.get("classes", [])
    print(f"Checkpoint classes: {len(model_classes)}")
    print(f"Checkpoint img_size: {ckpt.get('img_size', 'N/A')}")
    print(f"\nClass list in checkpoint:")
    for i, c in enumerate(model_classes):
        print(f"  [{i:2d}] {c}")
    if model_classes == classes:
        print("\n✅ Checkpoint classes match dataset folder names EXACTLY.")
    else:
        print("\n🔴 MISMATCH between checkpoint classes and dataset folder names!")
        print(f"   In checkpoint only: {set(model_classes) - set(classes)}")
        print(f"   In dataset only:    {set(classes) - set(model_classes)}")
except Exception as e:
    print(f"Could not load checkpoint: {e}")