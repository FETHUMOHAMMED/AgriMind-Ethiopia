"""Train MobileNetV2 on AgriMind dataset using the preserved splits.json.

Fixes the previous training bugs identified in the EAII safety audit:
  - Deterministic train/val split loaded from splits.json (no random_split)
  - No 5,000-image subset cap (uses all train images)
  - Augmentation applied to TRAIN ONLY (val/test use resize + normalize)
  - Seeded everywhere (random, numpy, torch)
  - Unfreezes last 2 MobileNet blocks + classifier (vs. fully frozen base)
  - Saves BEST checkpoint by val accuracy to a NEW file (does not overwrite
    the existing agrimind_mobilenetv2.pth baseline)
  - Per-epoch val accuracy + per-class F1 printout

Usage:
    cd C:/projects/AgriMind-Ethiopia/backend
    python app/ai/train_cnn.py              # full 10-epoch run
    $env:AGRI_QUICK="1"; python app/ai/train_cnn.py   # 1-epoch smoke test
"""
import json
import os
import random
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from sklearn.metrics import f1_score
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SPLITS_PATH = Path(r"C:\projects\AgriMind-Ethiopia\backend\app\ai\datasets\splits.json")
DATA_DIR    = Path(r"C:\projects\AgriMind-Ethiopia\backend\app\ai\datasets\flat_crops")
OUTPUT_MODEL = Path(r"C:\projects\AgriMind-Ethiopia\backend\app\ai\model\agrimind_mobilenetv2_v2.pth")

SEED        = 42
IMG_SIZE    = 128
BATCH_SIZE  = 32
NUM_WORKERS = 0

QUICK_MODE  = os.getenv("AGRI_QUICK") == "1"
EPOCHS      = 1 if QUICK_MODE else 10
LR_HEAD     = 1e-3
LR_BACKBONE = 1e-4
FREEZE_MODE = "last2"  # "head_only" | "last2" | "all"

# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
torch.cuda.manual_seed_all(SEED)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False

# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------
class SplitDataset(Dataset):
    """Reads images by relative path from splits.json, labels via folder name."""

    def __init__(self, root: Path, rel_files: list[str], class_to_idx: dict, transform):
        self.root = root
        self.files = rel_files
        self.class_to_idx = class_to_idx
        self.transform = transform

    def __len__(self) -> int:
        return len(self.files)

    def __getitem__(self, idx):
        rel = self.files[idx]
        path = self.root / rel
        with Image.open(path) as im:
            img = im.convert("RGB")
        img = self.transform(img)
        class_name = rel.split("/")[0]
        return img, self.class_to_idx[class_name]


def flatten_split(split_data: dict, split_name: str) -> list[str]:
    out: list[str] = []
    for cname, splits in split_data["per_class"].items():
        out.extend(splits[split_name])
    return out


# ---------------------------------------------------------------------------
# Transforms — CRITICAL: aug on train only, resize+norm on val/test
# ---------------------------------------------------------------------------
def build_transforms():
    mean = [0.485, 0.456, 0.406]
    std  = [0.229, 0.224, 0.225]

    train_tf = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=mean, std=std),
    ])
    eval_tf = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=mean, std=std),
    ])
    return train_tf, eval_tf


# ---------------------------------------------------------------------------
# Model + freeze strategy
# ---------------------------------------------------------------------------
def build_model(num_classes: int):
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)
    model.classifier[1] = nn.Linear(model.last_channel, num_classes)

    if FREEZE_MODE == "head_only":
        for p in model.features.parameters():
            p.requires_grad = False
        head_params = list(model.classifier.parameters())
        backbone_params: list = []
    elif FREEZE_MODE == "last2":
        # Freeze features[0..16], train features[17..18] + classifier
        for i, block in enumerate(model.features):
            if i < 17:
                for p in block.parameters():
                    p.requires_grad = False
        head_params = list(model.classifier.parameters())
        backbone_params = [
            p for i in range(17, len(model.features))
            for p in model.features[i].parameters()
        ]
    else:  # "all"
        head_params = list(model.classifier.parameters())
        backbone_params = [
            p for i in range(len(model.features))
            for p in model.features[i].parameters()
        ]

    return model, head_params, backbone_params


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("=" * 72)
    print("AgriMind CNN Training (pipeline-fixed)")
    print("=" * 72)

    if not SPLITS_PATH.exists():
        raise SystemExit(f"splits.json missing. Run make_splits.py first: {SPLITS_PATH}")
    if not DATA_DIR.is_dir():
        raise SystemExit(f"Dataset not found: {DATA_DIR}")

    split = json.loads(SPLITS_PATH.read_text(encoding="utf-8"))
    class_names = split["class_names"]
    class_to_idx = split["class_to_idx"]
    num_classes = len(class_names)

    print(f"Split seed:         {split['seed']}")
    print(f"Class count:        {num_classes}")
    print(f"Excluded classes:   {len(split['excluded_classes'])}")
    print(f"Quick mode:         {QUICK_MODE}")
    print(f"Epochs:             {EPOCHS}")
    print(f"Freeze mode:        {FREEZE_MODE}")
    print(f"Output checkpoint:  {OUTPUT_MODEL}")
    print("=" * 72)

    train_tf, eval_tf = build_transforms()

    train_files = flatten_split(split, "train")
    val_files   = flatten_split(split, "val")

    if QUICK_MODE:
        random.shuffle(train_files); train_files = train_files[:500]
        random.shuffle(val_files);   val_files   = val_files[:200]
        print(f"[QUICK] Truncated to {len(train_files)} train / {len(val_files)} val")

    train_ds = SplitDataset(DATA_DIR, train_files, class_to_idx, train_tf)
    val_ds   = SplitDataset(DATA_DIR, val_files,   class_to_idx, eval_tf)

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,
                              num_workers=NUM_WORKERS, pin_memory=False)
    val_loader   = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False,
                              num_workers=NUM_WORKERS, pin_memory=False)

    print(f"Train: {len(train_ds)} | Val: {len(val_ds)} | "
          f"Batches/epoch: {len(train_loader)}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}\n")

    model, head_params, backbone_params = build_model(num_classes)
    model.to(device)

    param_groups = [{"params": head_params, "lr": LR_HEAD}]
    if backbone_params:
        param_groups.append({"params": backbone_params, "lr": LR_BACKBONE})
    optimizer = torch.optim.Adam(param_groups)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.5)
    criterion = nn.CrossEntropyLoss()

    best_val_acc = 0.0
    best_epoch = 0
    OUTPUT_MODEL.parent.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, EPOCHS + 1):
        epoch_start = time.time()

        # ---- Train ----
        model.train()
        run_loss = 0.0
        correct = 0
        total = 0
        for i, (imgs, labels) in enumerate(train_loader, 1):
            imgs, labels = imgs.to(device), labels.to(device)
            optimizer.zero_grad()
            out = model(imgs)
            loss = criterion(out, labels)
            loss.backward()
            optimizer.step()

            run_loss += loss.item() * imgs.size(0)
            correct += (out.argmax(1) == labels).sum().item()
            total += labels.size(0)

            if i % 50 == 0 or i == len(train_loader):
                elapsed = time.time() - epoch_start
                eta = elapsed / i * (len(train_loader) - i)
                print(f"  E{epoch:2d} [{i:4d}/{len(train_loader)}] "
                      f"loss={run_loss/total:.4f} "
                      f"acc={100*correct/total:5.2f}% "
                      f"elapsed={elapsed:5.0f}s eta={eta:5.0f}s")

        train_acc = 100 * correct / total
        train_loss = run_loss / total

        # ---- Validate ----
        model.eval()
        val_correct = 0
        val_total = 0
        val_preds: list[int] = []
        val_labels: list[int] = []
        with torch.no_grad():
            for imgs, labels in val_loader:
                imgs, labels = imgs.to(device), labels.to(device)
                out = model(imgs)
                preds = out.argmax(1)
                val_correct += (preds == labels).sum().item()
                val_total += labels.size(0)
                val_preds.extend(preds.cpu().tolist())
                val_labels.extend(labels.cpu().tolist())

        val_acc = 100 * val_correct / val_total
        macro_f1 = f1_score(val_labels, val_preds, average="macro", zero_division=0)
        epoch_time = time.time() - epoch_start

        print(f"\nE{epoch:2d} DONE | train_loss={train_loss:.4f} | "
              f"train_acc={train_acc:.2f}% | val_acc={val_acc:.2f}% | "
              f"val_macroF1={macro_f1:.4f} | time={epoch_time:.0f}s\n")

        scheduler.step()

        # Save best
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_epoch = epoch
            torch.save({
                "model_state": model.state_dict(),
                "classes": class_names,
                "class_to_idx": class_to_idx,
                "img_size": IMG_SIZE,
                "freeze_mode": FREEZE_MODE,
                "split_seed": split["seed"],
                "val_acc": val_acc,
                "val_macro_f1": macro_f1,
                "epoch": epoch,
                "num_classes": num_classes,
            }, OUTPUT_MODEL)
            print(f"  ✅ New best saved → {OUTPUT_MODEL.name} "
                  f"(val_acc={val_acc:.2f}%)\n")

    print("=" * 72)
    print(f"Training complete. Best val_acc = {best_val_acc:.2f}% at epoch {best_epoch}")
    print(f"Checkpoint: {OUTPUT_MODEL}")
    print("Next step: python app/ai/evaluate_cnn.py")
    print("=" * 72)


if __name__ == "__main__":
    main()