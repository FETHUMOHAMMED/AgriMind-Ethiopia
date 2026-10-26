"""Diagnostic: train on Holeta Ethiopian field data ONLY, 5-fold cross-validation.

If this reaches 80%+ accuracy, it confirms:
  - Holeta data is learnable
  - The 34% result is domain shift, not bad data
  - Phase C field collection will work

If this stalls below 60%, investigate data quality before Phase C.
"""
import random
import time
from collections import Counter
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms

HOLETA_ROOT = Path(r"C:\projects\AgriMind-Ethiopia\data\raw\wheat\ethiopia_holeta_kaggle\wheat_leaf")
CLASSES = ["healthy", "septoria", "stripe_rust"]
FOLDER_MAP = {"Healthy": "healthy", "septoria": "septoria", "stripe_rust": "stripe_rust"}
CLASS_TO_IDX = {c: i for i, c in enumerate(CLASSES)}

IMG_SIZE = 128
BATCH_SIZE = 16
EPOCHS = 15
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


def load_all_items():
    items = []
    for folder_name, canonical in FOLDER_MAP.items():
        class_dir = HOLETA_ROOT / folder_name
        for img in class_dir.glob("*"):
            if img.suffix.upper() in {".JPG", ".JPEG", ".PNG"}:
                items.append((str(img), CLASS_TO_IDX[canonical]))
    return items


def train_fold(train_items, val_items, fold_idx):
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
    for epoch in range(1, EPOCHS + 1):
        model.train()
        for imgs, lbls in train_loader:
            imgs, lbls = imgs.to(device), lbls.to(device)
            optimizer.zero_grad()
            loss = criterion(model(imgs), lbls)
            loss.backward()
            optimizer.step()

        model.eval()
        preds, labels = [], []
        with torch.no_grad():
            for imgs, lbls in val_loader:
                out = model(imgs.to(device))
                preds.extend(out.argmax(1).cpu().tolist())
                labels.extend(lbls.tolist())

        acc = 100 * accuracy_score(labels, preds)
        if acc > best_val_acc:
            best_val_acc = acc

        if epoch % 5 == 0 or epoch == EPOCHS:
            print(f"  Fold {fold_idx+1} E{epoch:2d} | val_acc={acc:.2f}%")

    return best_val_acc


def main():
    print("=" * 72)
    print("HOLETA-ONLY DIAGNOSTIC — 5-fold stratified CV on 407 Ethiopian field images")
    print("=" * 72)

    items = load_all_items()
    print(f"\nTotal: {len(items)} images")
    print(f"Class distribution: {Counter(label for _, label in items)}")

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    labels_arr = [label for _, label in items]

    fold_accs = []
    for fold_idx, (train_idx, val_idx) in enumerate(skf.split(items, labels_arr)):
        print(f"\n--- Fold {fold_idx+1}/5 ---")
        train_items = [items[i] for i in train_idx]
        val_items = [items[i] for i in val_idx]
        acc = train_fold(train_items, val_items, fold_idx)
        fold_accs.append(acc)
        print(f"Fold {fold_idx+1} best val_acc: {acc:.2f}%")

    print("\n" + "=" * 72)
    print(f"5-FOLD CV RESULT: mean={np.mean(fold_accs):.2f}%  std={np.std(fold_accs):.2f}%")
    print(f"Fold accuracies: {[f'{a:.2f}' for a in fold_accs]}")
    print("=" * 72)
    print("\nINTERPRETATION:")
    if np.mean(fold_accs) >= 80:
        print("  ✅ Holeta data is LEARNABLE. The 34% result = domain shift.")
        print("  → Phase C field collection is confirmed as the right approach.")
    elif np.mean(fold_accs) >= 65:
        print("  🟡 Holeta data is PARTIALLY learnable with 407 images.")
        print("  → More data needed, but the approach is viable.")
    else:
        print("  🔴 Holeta data struggles even on its own.")
        print("  → Investigate labels before Phase C.")


if __name__ == "__main__":
    main()