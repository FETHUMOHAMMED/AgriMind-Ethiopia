"""Final production training — Holeta Ethiopian field data, 3-class.

Uses all 407 images (no held-out test — the 5-fold CV already measured
generalization). Stratified train/val split for early stopping.
Saves model for deployment.

Model name: wheat_holeta_mobilenetv2_v2.pth
"""
import json
import random
from collections import Counter
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms

HOLETA_ROOT = Path(r"C:\projects\AgriMind-Ethiopia\data\raw\wheat\ethiopia_holeta_kaggle\wheat_leaf")
MODEL_OUT = Path(r"C:\projects\AgriMind-Ethiopia\backend\app\ai\model\wheat_holeta_mobilenetv2_v2.pth")
REPORT_OUT = Path(r"C:\projects\AgriMind-Ethiopia\EAII-Evidence-Pack\B_AI_Evidence\Metrics\WHEAT_HOLETA_V2_REPORT.txt")

CLASSES = ["healthy", "septoria", "stripe_rust"]
FOLDER_MAP = {"Healthy": "healthy", "septoria": "septoria", "stripe_rust": "stripe_rust"}
CLASS_TO_IDX = {c: i for i, c in enumerate(CLASSES)}

IMG_SIZE = 128
BATCH_SIZE = 16
EPOCHS = 20
SEED = 42

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)


class HoletaDataset(Dataset):
    def __init__(self, items, transform):
        self.items = items
        self.transform = transform

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        path, label = self.items[idx]
        with Image.open(path) as im:
            img = im.convert("RGB")
        return self.transform(img), label


def load_items():
    items = []
    for folder_name, canonical in FOLDER_MAP.items():
        for img in (HOLETA_ROOT / folder_name).glob("*"):
            if img.suffix.upper() in {".JPG", ".JPEG", ".PNG"}:
                items.append((str(img), CLASS_TO_IDX[canonical]))
    return items


def main():
    print("=" * 72)
    print("HOLETA FINAL TRAINING — production checkpoint")
    print("=" * 72)

    items = load_items()
    print(f"Total: {len(items)} images")
    print(f"Class distribution: {dict(Counter(label for _, label in items))}")

    # Stratified 85/15 split for early stopping
    labels = [label for _, label in items]
    train_items, val_items = train_test_split(
        items, test_size=0.15, random_state=SEED, stratify=labels
    )
    print(f"Train: {len(train_items)} | Val: {len(val_items)}")

    train_tf = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    eval_tf = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    train_loader = DataLoader(HoletaDataset(train_items, train_tf),
                              batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    val_loader = DataLoader(HoletaDataset(val_items, eval_tf),
                            batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    device = torch.device("cpu")
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)
    model.classifier[1] = nn.Linear(model.last_channel, len(CLASSES))
    for i, block in enumerate(model.features):
        if i < 15:
            for p in block.parameters():
                p.requires_grad = False
    model.to(device)

    optimizer = torch.optim.Adam([
        {"params": model.classifier.parameters(), "lr": 1e-3},
        {"params": [p for i in range(15, len(model.features))
                    for p in model.features[i].parameters()], "lr": 1e-4},
    ])
    criterion = nn.CrossEntropyLoss()

    best_val_acc = 0.0
    best_epoch = 0
    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, EPOCHS + 1):
        model.train()
        for imgs, lbls in train_loader:
            imgs, lbls = imgs.to(device), lbls.to(device)
            optimizer.zero_grad()
            loss = criterion(model(imgs), lbls)
            loss.backward()
            optimizer.step()

        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for imgs, lbls in val_loader:
                out = model(imgs.to(device))
                correct += (out.argmax(1).cpu() == lbls).sum().item()
                total += len(lbls)

        val_acc = 100 * correct / total
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_epoch = epoch
            torch.save({
                "model_state": model.state_dict(),
                "classes": CLASSES,
                "class_to_idx": CLASS_TO_IDX,
                "img_size": IMG_SIZE,
                "val_acc": val_acc,
                "epoch": epoch,
                "num_classes": len(CLASSES),
                "training_data": "Holeta Ethiopian field data (407 images)",
                "training_source": "Kaggle olyadgetch/wheat-leaf-dataset",
                "provenance": "Holeta wheat farm, Ethiopia — real Ethiopian field conditions",
                "limitations": "3-class only (healthy, septoria, stripe_rust), single location, likely single season",
            }, MODEL_OUT)
            print(f"E{epoch:2d} | val_acc={val_acc:.2f}% | ✅ New best")

    print("=" * 72)
    print(f"Training complete. Best val_acc: {best_val_acc:.2f}% @ epoch {best_epoch}")
    print(f"Checkpoint: {MODEL_OUT}")
    print("=" * 72)

    # Write report
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_OUT, "w", encoding="utf-8") as f:
        f.write("AgriMind Wheat Holeta v2 — Production Training Report\n")
        f.write("=" * 60 + "\n\n")
        f.write("Model: MobileNetV2, 3-class (healthy, septoria, stripe_rust)\n")
        f.write("Training data: 407 Ethiopian field images from Holeta wheat farm\n")
        f.write("Provenance: Kaggle olyadgetch/wheat-leaf-dataset (mirrors Mendeley Holeta)\n")
        f.write("Camera: Canon EOS 5D Mark III\n")
        f.write("Labels: Expert-verified with plant pathologists\n\n")
        f.write(f"Train/val split: {len(train_items)} / {len(val_items)}\n")
        f.write(f"Best val_acc: {best_val_acc:.2f}% at epoch {best_epoch}\n\n")
        f.write("5-FOLD CV EVIDENCE (from diagnostic run):\n")
        f.write("  Mean accuracy: 95.08% (±1.75%)\n")
        f.write("  Fold accuracies: 97.56, 95.12, 93.83, 92.59, 96.30\n\n")
        f.write("TRANSFER CONTEXT:\n")
        f.write("  Same 3 classes trained on 1,510 public Kaggle images:\n")
        f.write("    - Kaggle test: 84.90%\n")
        f.write("    - Holeta field: 34.15% (FAIL)\n\n")
        f.write("  Trained on Holeta field images:\n")
        f.write("    - Holeta field (5-fold CV): 95.08% (PASS)\n\n")
        f.write("CONCLUSION:\n")
        f.write("  Ethiopian field data is essential for Ethiopian field performance.\n")
        f.write("  407 images achieve 95% — the barrier is data collection, not ML capability.\n\n")
        f.write("DEPLOYMENT LIMITATIONS:\n")
        f.write("  - Single location (Holeta, Oromia)\n")
        f.write("  - Likely single growing season\n")
        f.write("  - 3 classes only (FHB, leaf_rust not covered)\n")
        f.write("  - Not tested at other Ethiopian sites\n")
        f.write("  - Treatment recommendations require agronomist review\n")

    print(f"Report saved: {REPORT_OUT}")


if __name__ == "__main__":
    main()