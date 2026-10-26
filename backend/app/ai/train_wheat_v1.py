"""Phase B wheat training — MobileNetV2, 3-class (healthy, septoria, stripe_rust).

Training: Kaggle `yilikalfikru` wheat dataset — 3-class subset
Validation: Kaggle's own val split
Test 1: Kaggle's own test split
Test 2: Holeta Ethiopian field data (Kaggle `olyadgetch`)

Outputs:
  model/wheat_mobilenetv2_v1.pth
  Metrics report with all three test results
"""
import json
import random
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms

# ============ CONFIG ============
KAGGLE_ROOT = Path(r"C:\projects\AgriMind-Ethiopia\data\raw\wheat\kaggle\Datasets")
HOLETA_ROOT = Path(r"C:\projects\AgriMind-Ethiopia\data\raw\wheat\ethiopia_holeta_kaggle\wheat_leaf")
MODEL_OUT = Path(r"C:\projects\AgriMind-Ethiopia\backend\app\ai\model\wheat_mobilenetv2_v1.pth")
REPORT_OUT = Path(r"C:\projects\AgriMind-Ethiopia\EAII-Evidence-Pack\B_AI_Evidence\Metrics\WHEAT_V1_CLASSIFICATION_REPORT.txt")

# 3-class subset (Holeta has these 3 only)
CLASSES = ["healthy", "septoria", "stripe_rust"]
CLASS_TO_IDX = {c: i for i, c in enumerate(CLASSES)}

# Class name mapping (Kaggle uses these folder names)
KAGGLE_FOLDER_MAP = {
    "healthy": "healthy",
    "septoria": "septoria",
    "stripe_rust": "stripe_rust",
}
HOLETA_FOLDER_MAP = {
    "Healthy": "healthy",
    "septoria": "septoria",
    "stripe_rust": "stripe_rust",
}

IMG_SIZE = 128
BATCH_SIZE = 16
EPOCHS = 10
LR_HEAD = 1e-3
LR_BACKBONE = 1e-4
FREEZE_MODE = "last2"
SEED = 42

# ============ SEEDING ============
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)


class WheatDataset(Dataset):
    def __init__(self, root: Path, split: str, folder_map: dict, transform):
        self.items = []
        self.transform = transform
        self.split = split

        # For Kaggle: root/split/class/*.jpg
        # For Holeta: root/class/*.JPG (single "split" folder)
        for folder_name, canonical in folder_map.items():
            class_dir = root / split / folder_name if (root / split).exists() else root / folder_name
            if not class_dir.exists():
                continue
            for img in class_dir.glob("*"):
                if img.suffix.upper() in {".JPG", ".JPEG", ".PNG"}:
                    self.items.append((str(img), CLASS_TO_IDX[canonical]))

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        path, label = self.items[idx]
        with Image.open(path) as im:
            img = im.convert("RGB")
        return self.transform(img), label


def build_transforms():
    mean = [0.485, 0.456, 0.406]
    std = [0.229, 0.224, 0.225]
    train_tf = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.RandomHorizontalFlip(),
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


def build_model(num_classes: int):
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)
    model.classifier[1] = nn.Linear(model.last_channel, num_classes)

    for i, block in enumerate(model.features):
        if i < 17:
            for p in block.parameters():
                p.requires_grad = False

    head_params = list(model.classifier.parameters())
    backbone_params = [p for i in range(17, len(model.features))
                       for p in model.features[i].parameters()]
    return model, head_params, backbone_params


def evaluate(model, loader, device, class_names):
    model.eval()
    preds, labels = [], []
    with torch.no_grad():
        for imgs, lbls in loader:
            imgs = imgs.to(device)
            out = model(imgs)
            preds.extend(out.argmax(1).cpu().tolist())
            labels.extend(lbls.tolist())
    acc = 100 * np.mean(np.array(preds) == np.array(labels))
    macro_f1 = f1_score(labels, preds, average="macro", zero_division=0)
    return acc, macro_f1, preds, labels


def main():
    print("=" * 72)
    print("PHASE B WHEAT TRAINING — 3-class, MobileNetV2")
    print("=" * 72)

    train_tf, eval_tf = build_transforms()

    # Build datasets
    train_ds = WheatDataset(KAGGLE_ROOT, "train", KAGGLE_FOLDER_MAP, train_tf)
    val_ds = WheatDataset(KAGGLE_ROOT, "val", KAGGLE_FOLDER_MAP, eval_tf)
    kaggle_test_ds = WheatDataset(KAGGLE_ROOT, "test", KAGGLE_FOLDER_MAP, eval_tf)

    # Holeta: no split dir, just class dirs
    holeta_ds = WheatDataset(HOLETA_ROOT, "", HOLETA_FOLDER_MAP, eval_tf)

    print(f"\nDataset sizes:")
    print(f"  Train (Kaggle):        {len(train_ds)}")
    print(f"  Val (Kaggle):          {len(val_ds)}")
    print(f"  Test (Kaggle):         {len(kaggle_test_ds)}")
    print(f"  Test (Holeta 🇪🇹):      {len(holeta_ds)}")

    if len(train_ds) == 0 or len(val_ds) == 0:
        raise SystemExit("No training data found — check folder paths")

    # DataLoaders
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    kaggle_test_loader = DataLoader(kaggle_test_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    holeta_loader = DataLoader(holeta_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\nDevice: {device}")

    model, head_params, backbone_params = build_model(len(CLASSES))
    model.to(device)

    optimizer = torch.optim.Adam([
        {"params": head_params, "lr": LR_HEAD},
        {"params": backbone_params, "lr": LR_BACKBONE},
    ])
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.5)
    criterion = nn.CrossEntropyLoss()

    best_val_acc = 0.0
    best_epoch = 0
    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, EPOCHS + 1):
        start = time.time()
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

            if i % 20 == 0 or i == len(train_loader):
                print(f"  E{epoch:2d} [{i:3d}/{len(train_loader)}] "
                      f"loss={run_loss/total:.4f} acc={100*correct/total:.2f}% "
                      f"elapsed={time.time()-start:.0f}s")

        train_acc = 100 * correct / total
        val_acc, val_f1, _, _ = evaluate(model, val_loader, device, CLASSES)
        scheduler.step()

        print(f"\nE{epoch:2d} DONE | train_acc={train_acc:.2f}% | "
              f"val_acc={val_acc:.2f}% | val_macroF1={val_f1:.4f} | "
              f"time={time.time()-start:.0f}s")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_epoch = epoch
            torch.save({
                "model_state": model.state_dict(),
                "classes": CLASSES,
                "class_to_idx": CLASS_TO_IDX,
                "img_size": IMG_SIZE,
                "val_acc": val_acc,
                "val_macro_f1": val_f1,
                "epoch": epoch,
                "num_classes": len(CLASSES),
            }, MODEL_OUT)
            print(f"  ✅ New best saved (val_acc={val_acc:.2f}%)\n")

    print("=" * 72)
    print(f"Training complete. Best val_acc={best_val_acc:.2f}% @ epoch {best_epoch}")
    print("=" * 72)

    # ===== Final evaluation =====
    # Load best checkpoint
    ckpt = torch.load(MODEL_OUT, map_location="cpu", weights_only=False)
    model.load_state_dict(ckpt["model_state"])
    model.to(device)

    print("\n" + "=" * 72)
    print("FINAL EVALUATION — 3 test sets")
    print("=" * 72)

    kaggle_acc, kaggle_f1, kaggle_preds, kaggle_labels = evaluate(model, kaggle_test_loader, device, CLASSES)
    holeta_acc, holeta_f1, holeta_preds, holeta_labels = evaluate(model, holeta_loader, device, CLASSES)

    print(f"\n[1] Kaggle test set (public, {len(kaggle_test_ds)} images):")
    print(f"    Top-1 accuracy: {kaggle_acc:.2f}%")
    print(f"    Macro F1:       {kaggle_f1:.4f}")
    print(f"\n{classification_report(kaggle_labels, kaggle_preds, target_names=CLASSES, digits=4, zero_division=0)}")

    print(f"\n[2] Holeta Ethiopian field set ({len(holeta_ds)} images):")
    print(f"    Top-1 accuracy: {holeta_acc:.2f}%")
    print(f"    Macro F1:       {holeta_f1:.4f}")
    print(f"\n{classification_report(holeta_labels, holeta_preds, target_names=CLASSES, digits=4, zero_division=0)}")

    print(f"\nTRANSFER GAP:")
    print(f"  Public test:   {kaggle_acc:.2f}%")
    print(f"  Ethiopian field: {holeta_acc:.2f}%")
    print(f"  Gap:            {kaggle_acc - holeta_acc:+.2f} pp")

    # Write report
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_OUT, "w", encoding="utf-8") as f:
        f.write("AgriMind Wheat v1 — Phase B Training Report\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Model: MobileNetV2, 3-class subset (healthy, septoria, stripe_rust)\n")
        f.write(f"Training: {len(train_ds)} Kaggle images\n")
        f.write(f"Validation: {len(val_ds)} Kaggle images\n")
        f.write(f"Best epoch: {best_epoch}, best val_acc: {best_val_acc:.2f}%\n\n")
        f.write(f"[1] KAGGLE TEST SET ({len(kaggle_test_ds)} images, PUBLIC):\n")
        f.write(f"  Accuracy: {kaggle_acc:.2f}%\n")
        f.write(f"  Macro F1: {kaggle_f1:.4f}\n\n")
        f.write(classification_report(kaggle_labels, kaggle_preds, target_names=CLASSES, digits=4, zero_division=0))
        f.write(f"\n\n[2] HOLETA ETHIOPIAN FIELD SET ({len(holeta_ds)} images, REAL FARM DATA):\n")
        f.write(f"  Accuracy: {holeta_acc:.2f}%\n")
        f.write(f"  Macro F1: {holeta_f1:.4f}\n\n")
        f.write(classification_report(holeta_labels, holeta_preds, target_names=CLASSES, digits=4, zero_division=0))
        f.write(f"\n\nTRANSFER GAP: {kaggle_acc - holeta_acc:+.2f} pp (public → Ethiopian field)\n\n")
        f.write("HONEST LIMITATIONS:\n")
        f.write("- Kaggle dataset origin unclear (unverified for Ethiopian conditions)\n")
        f.write("- Holeta: 407 images from single location, single season\n")
        f.write("- 3-class subset only — FHB, leaf_rust not evaluated on Ethiopian field\n")
        f.write("- Model not tested beyond these two datasets\n")
        f.write("- Treatment recommendations require agronomist review (no clinical validation)\n")

    print(f"\n✅ Report saved: {REPORT_OUT}")


if __name__ == "__main__":
    main()