"""Coffee Phase B training — clean dataset, grouped leakage-free CV.

Uses only NON-AUGMENTED originals, deduplicated by pHash, split by session-cluster.
"""
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

import imagehash
import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from sklearn.metrics import classification_report, f1_score
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms

META = Path(r"C:\projects\AgriMind-Ethiopia\data\verification\coffee_clean_inventory.json")
MODEL_OUT = Path(r"C:\projects\AgriMind-Ethiopia\backend\app\ai\model\coffee_mobilenetv2_v1.pth")
REPORT_OUT = Path(r"C:\projects\AgriMind-Ethiopia\EAII-Evidence-Pack\B_AI_Evidence\Metrics\COFFEE_V1_REPORT.txt")

CLASSES = ["cercospora", "healthy", "leaf_rust", "phoma"]
CLASS_TO_IDX = {c: i for i, c in enumerate(CLASSES)}
SEED = 42

IMG_SIZE = 128
BATCH_SIZE = 16
EPOCHS = 12

random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)


class CoffeeDataset(Dataset):
    def __init__(self, items, tf):
        self.items = items
        self.tf = tf
    def __len__(self): return len(self.items)
    def __getitem__(self, i):
        path, label = self.items[i]
        with Image.open(path) as im:
            im = im.convert("RGB")
            im.thumbnail((2000, 2000))
        return self.tf(im), label


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


def main():
    print("=" * 72)
    print("COFFEE PHASE B — grouped leakage-free CV")
    print("=" * 72)

    meta = json.loads(META.read_text(encoding="utf-8"))
    items_raw = meta["representatives"]
    print(f"Total unique images: {len(items_raw)}")
    print(f"Class distribution: {dict(Counter(r['label'] for r in items_raw))}")

    # Compute pHash again to cluster duplicates we may have missed
    print("\nRe-clustering for group CV...")
    hashes = []
    for r in items_raw:
        try:
            with Image.open(r["path"]) as im:
                im = im.convert("RGB")
                im.thumbnail((2000, 2000))
                h = imagehash.phash(im, hash_size=8)
            hashes.append((r["path"], CLASS_TO_IDX[r["label"]], h))
        except Exception as e:
            print(f"  SKIP {r['path']}: {e}")

    parent = list(range(len(hashes)))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(x, y):
        px, py = find(x), find(y)
        if px != py: parent[py] = px
    for i in range(len(hashes)):
        for j in range(i + 1, len(hashes)):
            if (hashes[i][2] - hashes[j][2]) <= 5:
                union(i, j)
    groups = defaultdict(list)
    for i in range(len(hashes)):
        groups[find(i)].append(i)
    group_list = list(groups.values())
    print(f"Session clusters: {len(group_list)}")

    # Grouped 70/15/15 split
    random.shuffle(group_list)
    total = len(hashes)
    train_target = int(0.70 * total)
    val_target = int(0.15 * total)

    train_idx, val_idx, test_idx = [], [], []
    for group in group_list:
        if len(train_idx) < train_target:
            train_idx.extend(group)
        elif len(val_idx) < val_target:
            val_idx.extend(group)
        else:
            test_idx.extend(group)

    print(f"Train: {len(train_idx)} | Val: {len(val_idx)} | Test: {len(test_idx)}")
    print(f"Train classes: {dict(Counter(hashes[i][1] for i in train_idx))}")
    print(f"Val classes:   {dict(Counter(hashes[i][1] for i in val_idx))}")
    print(f"Test classes:  {dict(Counter(hashes[i][1] for i in test_idx))}")

    # Build loaders
    train_tf, eval_tf = build_transforms()
    train_items = [(hashes[i][0], hashes[i][1]) for i in train_idx]
    val_items = [(hashes[i][0], hashes[i][1]) for i in val_idx]
    test_items = [(hashes[i][0], hashes[i][1]) for i in test_idx]

    train_loader = DataLoader(CoffeeDataset(train_items, train_tf), batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(CoffeeDataset(val_items, eval_tf), batch_size=BATCH_SIZE, shuffle=False)
    test_loader = DataLoader(CoffeeDataset(test_items, eval_tf), batch_size=BATCH_SIZE, shuffle=False)

    device = torch.device("cpu")
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)
    model.classifier[1] = nn.Linear(model.last_channel, len(CLASSES))
    for i, block in enumerate(model.features):
        if i < 15:
            for p in block.parameters():
                p.requires_grad = False
    model.to(device)

    opt = torch.optim.Adam([
        {"params": model.classifier.parameters(), "lr": 1e-3},
        {"params": [p for i in range(15, len(model.features))
                    for p in model.features[i].parameters()], "lr": 1e-4},
    ])
    sched = torch.optim.lr_scheduler.StepLR(opt, step_size=4, gamma=0.5)
    crit = nn.CrossEntropyLoss()

    best_val = 0.0
    best_epoch = 0

    for epoch in range(1, EPOCHS + 1):
        model.train()
        for imgs, lbls in train_loader:
            imgs, lbls = imgs.to(device), lbls.to(device)
            opt.zero_grad()
            crit(model(imgs), lbls).backward()
            opt.step()
        sched.step()

        model.eval()
        correct = total_v = 0
        with torch.no_grad():
            for imgs, lbls in val_loader:
                correct += (model(imgs.to(device)).argmax(1).cpu() == lbls).sum().item()
                total_v += len(lbls)
        val_acc = 100 * correct / total_v if total_v > 0 else 0

        if val_acc > best_val:
            best_val = val_acc
            best_epoch = epoch
            torch.save({
                "model_state": model.state_dict(),
                "classes": CLASSES,
                "class_to_idx": CLASS_TO_IDX,
                "img_size": IMG_SIZE,
                "val_acc": val_acc,
                "epoch": epoch,
            }, MODEL_OUT)
            print(f"E{epoch:2d} | val_acc={val_acc:.2f}% | new best saved")
        else:
            print(f"E{epoch:2d} | val_acc={val_acc:.2f}%")

    # Load best + final test eval
    ckpt = torch.load(MODEL_OUT, map_location="cpu", weights_only=False)
    model.load_state_dict(ckpt["model_state"])
    model.eval()

    print("\n" + "=" * 72)
    print("FINAL EVALUATION ON HELD-OUT TEST SET")
    print("=" * 72)

    preds, labels = [], []
    with torch.no_grad():
        for imgs, lbls in test_loader:
            preds.extend(model(imgs.to(device)).argmax(1).cpu().tolist())
            labels.extend(lbls.tolist())

    acc = 100 * np.mean(np.array(preds) == np.array(labels))
    macro_f1 = f1_score(labels, preds, average="macro", zero_division=0)
    print(f"\nTest accuracy: {acc:.2f}%")
    print(f"Macro F1:      {macro_f1:.4f}")
    print(f"\n{classification_report(labels, preds, target_names=CLASSES, digits=4, zero_division=0)}")

    # Save report
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_OUT, "w", encoding="utf-8") as f:
        f.write("AgriMind Coffee v1 — Phase B Report\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Training: {len(train_idx)} unique images (4 classes)\n")
        f.write(f"Val:      {len(val_idx)} images\n")
        f.write(f"Test:     {len(test_idx)} images\n\n")
        f.write(f"Split method: grouped by pHash session-clusters (leakage-free)\n")
        f.write(f"Best val_acc: {best_val:.2f}% at epoch {best_epoch}\n\n")
        f.write(f"TEST SET RESULTS:\n")
        f.write(f"  Top-1 accuracy: {acc:.2f}%\n")
        f.write(f"  Macro F1:       {macro_f1:.4f}\n\n")
        f.write(classification_report(labels, preds, target_names=CLASSES, digits=4, zero_division=0))
        f.write(f"\n\nData provenance: Kaggle 'metadata-enhanced-coffee-disease-benchmark'\n")
        f.write(f"  Ethiopian subset only (raw_ethiopian)\n")
        f.write(f"  Originals only (no augmented copies)\n")
        f.write(f"  pHash-deduplicated (Hamming <= 5)\n\n")
        f.write("LIMITATIONS:\n")
        f.write("  - Original train/test split from Kaggle had 72.5% leakage (unusable)\n")
        f.write("  - Rebuilt split from originals with grouped CV\n")
        f.write("  - No region/location metadata available\n")
        f.write("  - Not independently validated on other Ethiopian coffee regions\n")
        f.write("  - Treatment recommendations require agronomist review\n")

    print(f"\n✅ Report saved: {REPORT_OUT}")


if __name__ == "__main__":
    main()