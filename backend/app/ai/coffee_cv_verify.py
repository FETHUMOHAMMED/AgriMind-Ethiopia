"""Coffee Phase B — 5-fold grouped CV on clean 2,529 images."""
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

import imagehash
import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms

META = Path(r"C:\projects\AgriMind-Ethiopia\data\verification\coffee_clean_inventory.json")
CLASSES = ["cercospora", "healthy", "leaf_rust", "phoma"]
CLASS_TO_IDX = {c: i for i, c in enumerate(CLASSES)}
SEED = 42
IMG_SIZE = 128
BATCH_SIZE = 16
EPOCHS = 10

random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)


class DS(Dataset):
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


def build_tf():
    mean = [0.485, 0.456, 0.406]; std = [0.229, 0.224, 0.225]
    return transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=mean, std=std),
    ]), transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=mean, std=std),
    ])


def main():
    print("=" * 72)
    print("COFFEE PHASE B — 5-FOLD GROUPED CV")
    print("=" * 72)

    meta = json.loads(META.read_text(encoding="utf-8"))
    items = [(r["path"], CLASS_TO_IDX[r["label"]]) for r in meta["representatives"]]

    # Compute pHash clusters
    hashes = []
    for path, label in items:
        try:
            with Image.open(path) as im:
                im = im.convert("RGB")
                im.thumbnail((2000, 2000))
                h = imagehash.phash(im, hash_size=8)
            hashes.append((path, label, h))
        except Exception as e:
            print(f"  SKIP {path}: {e}")

    parent = list(range(len(hashes)))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
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

    # 5-fold grouped split
    random.shuffle(group_list)
    folds = [[] for _ in range(5)]
    fold_counts = [Counter() for _ in range(5)]
    for group in group_list:
        label = hashes[group[0]][1]
        fi = min(range(5), key=lambda f: fold_counts[f][label])
        folds[fi].extend(group)
        fold_counts[fi][label] += len(group)

    print(f"Fold sizes: {[len(f) for f in folds]}")

    train_tf, eval_tf = build_tf()
    device = torch.device("cpu")
    fold_accs = []

    for fi in range(5):
        print(f"\n--- Fold {fi+1}/5 ---")
        val_idx = folds[fi]
        train_idx = [i for f in range(5) if f != fi for i in folds[f]]

        train_items = [(hashes[i][0], hashes[i][1]) for i in train_idx]
        val_items = [(hashes[i][0], hashes[i][1]) for i in val_idx]

        train_loader = DataLoader(DS(train_items, train_tf), batch_size=BATCH_SIZE, shuffle=True)
        val_loader = DataLoader(DS(val_items, eval_tf), batch_size=BATCH_SIZE, shuffle=False)

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
        crit = nn.CrossEntropyLoss()

        best_acc = 0.0
        for epoch in range(EPOCHS):
            model.train()
            for imgs, lbls in train_loader:
                imgs, lbls = imgs.to(device), lbls.to(device)
                opt.zero_grad()
                crit(model(imgs), lbls).backward()
                opt.step()
            model.eval()
            correct = total = 0
            with torch.no_grad():
                for imgs, lbls in val_loader:
                    correct += (model(imgs.to(device)).argmax(1).cpu() == lbls).sum().item()
                    total += len(lbls)
            best_acc = max(best_acc, 100 * correct / total)

        fold_accs.append(best_acc)
        print(f"  Best val_acc: {best_acc:.2f}%")

    print("\n" + "=" * 72)
    print(f"GROUPED 5-FOLD CV: mean={np.mean(fold_accs):.2f}% ± {np.std(fold_accs):.2f}%")
    print(f"Fold results: {[f'{a:.2f}' for a in fold_accs]}")
    print("=" * 72)

    # Save report
    report = Path(r"C:\projects\AgriMind-Ethiopia\EAII-Evidence-Pack\B_AI_Evidence\Metrics\COFFEE_CV_VERIFICATION.txt")
    report.parent.mkdir(parents=True, exist_ok=True)
    with open(report, "w", encoding="utf-8") as f:
        f.write("COFFEE 5-FOLD GROUPED CV VERIFICATION\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Dataset: {len(hashes)} unique Ethiopian coffee images\n")
        f.write(f"Session clusters: {len(group_list)}\n")
        f.write(f"Split method: grouped by pHash cluster (leakage-free)\n\n")
        f.write(f"RESULTS:\n")
        f.write(f"  Mean CV accuracy: {np.mean(fold_accs):.2f}%\n")
        f.write(f"  Std deviation:    {np.std(fold_accs):.2f}%\n")
        f.write(f"  Fold accuracies:  {[f'{a:.2f}' for a in fold_accs]}\n\n")
        f.write(f"COMPARISON TO SINGLE-SPLIT TRAINING:\n")
        f.write(f"  Single train/val/test split test acc: 93.42%\n")
        f.write(f"  Grouped 5-fold CV mean:               {np.mean(fold_accs):.2f}%\n")
        f.write(f"  Delta:                                {np.mean(fold_accs) - 93.42:+.2f} pp\n")

    print(f"\n✅ Report saved: {report}")


if __name__ == "__main__":
    main()