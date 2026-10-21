"""Evaluate AgriMind v2 on any leakage-controlled split variant.

Accepts --split argument to point at a specific splits file:
    python app/ai/evaluate_cnn_v3.py --split splits.json
    python app/ai/evaluate_cnn_v3.py --split splits_scenarioA.json
    python app/ai/evaluate_cnn_v3.py --split splits_scenarioB.json

Writes output reports with a suffix matching the split filename so
original reports are never overwritten.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms

ROOT          = Path(r"C:\projects\AgriMind-Ethiopia\backend\app\ai")
DATA_DIR      = ROOT / "datasets" / "flat_crops"
MODEL_PATH    = ROOT / "model" / "agrimind_mobilenetv2_v2.pth"
EVIDENCE_DIR  = Path(r"C:\projects\AgriMind-Ethiopia\EAII-Evidence-Pack\B_AI_Evidence\Metrics")

BATCH_SIZE  = 32
NUM_WORKERS = 0


class EvalDataset(Dataset):
    def __init__(self, root: Path, rel_files: list, class_to_idx: dict, transform):
        self.root = root
        self.files = rel_files
        self.class_to_idx = class_to_idx
        self.transform = transform

    def __len__(self) -> int:
        return len(self.files)

    def __getitem__(self, idx):
        rel = self.files[idx]
        with Image.open(self.root / rel) as im:
            img = im.convert("RGB")
        return self.transform(img), self.class_to_idx[rel.split("/")[0]]


def flatten_split(split_data, split_name):
    out = []
    for splits in split_data["per_class"].values():
        out.extend(splits[split_name])
    return out


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", required=True,
                        help="Split filename (e.g. splits.json, splits_scenarioA.json)")
    args = parser.parse_args()

    split_path = ROOT / "datasets" / args.split
    if not split_path.exists():
        raise SystemExit(f"Split file not found: {split_path}")

    # Derive a unique suffix so we never overwrite an existing report
    stem = split_path.stem  # e.g. "splits" or "splits_scenarioA"
    suffix = stem.replace("splits_", "").upper() or "ORIGINAL"

    report_path   = EVIDENCE_DIR / f"CLASSIFICATION_REPORT_v2_TEST_{suffix}.txt"
    confusion_csv = EVIDENCE_DIR / f"confusion_matrix_v2_test_{suffix.lower()}.csv"

    print("=" * 72)
    print(f"AgriMind v2 evaluation — split: {args.split}")
    print("=" * 72)

    if not MODEL_PATH.exists():
        raise SystemExit(f"Model not found: {MODEL_PATH}")

    split = json.loads(split_path.read_text(encoding="utf-8"))
    class_names = split["class_names"]
    class_to_idx = split["class_to_idx"]

    ckpt = torch.load(MODEL_PATH, map_location="cpu", weights_only=True)
    ckpt_classes = ckpt["classes"]
    img_size = ckpt["img_size"]

    if ckpt_classes != class_names:
        raise SystemExit("Class list MISMATCH between checkpoint and split file")
    expected_mapping = {n: i for i, n in enumerate(class_names)}
    if class_to_idx != expected_mapping:
        raise SystemExit("class_to_idx does not match class_names order")
    if ckpt.get("class_to_idx") != class_to_idx:
        raise SystemExit("Checkpoint class_to_idx mismatch")

    ckpt_sha = sha256_of(MODEL_PATH)

    print(f"Checkpoint:    {MODEL_PATH.name}")
    print(f"  SHA256:      {ckpt_sha}")
    print(f"  saved_epoch: {ckpt.get('epoch')}")
    print(f"  train val_acc: {ckpt.get('val_acc'):.2f}%")
    print(f"  train val_macroF1: {ckpt.get('val_macro_f1'):.4f}")
    print(f"  num_classes: {ckpt['num_classes']}")
    print(f"  img_size:    {img_size}")

    test_files = flatten_split(split, "test")
    excluded_count = len(split.get("excluded_test_images", []))
    print(f"\nSplit file: {args.split}")
    print(f"  Test images: {len(test_files)}")
    if excluded_count:
        print(f"  Excluded (documented in split metadata): {excluded_count}")
    if "scenario" in split:
        print(f"  Scenario: {split['scenario']}")
        print(f"  Description: {split.get('description', 'N/A')}")
    if split.get("does_not_claim_leakage_free"):
        print(f"  does_not_claim_leakage_free: True")
        for item in split.get("not_yet_audited", []):
            print(f"    not_yet_audited: {item}")

    missing = [f for f in test_files if not (DATA_DIR / f).is_file()]
    if missing:
        raise SystemExit(f"{len(missing)} test images missing. Example: {missing[0]}")

    eval_tf = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    test_ds = EvalDataset(DATA_DIR, test_files, class_to_idx, eval_tf)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False,
                             num_workers=NUM_WORKERS)

    model = models.mobilenet_v2(weights=None)
    model.classifier[1] = nn.Linear(model.last_channel, len(class_names))
    model.load_state_dict(ckpt["model_state"])
    model.eval()

    all_preds, all_top3, all_labels = [], [], []
    with torch.no_grad():
        for i, (imgs, labels) in enumerate(test_loader, 1):
            out = model(imgs)
            all_preds.extend(out.argmax(1).tolist())
            all_top3.extend(out.topk(3, dim=1).indices.tolist())
            all_labels.extend(labels.tolist())
            if i % 10 == 0:
                print(f"  evaluated {min(i * BATCH_SIZE, len(test_files))}/{len(test_files)}")

    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)

    overall_acc = 100 * (all_preds == all_labels).mean()
    top3_correct = sum(1 for t, top in zip(all_labels, all_top3) if t in top)
    top3_acc = 100 * top3_correct / len(all_labels)
    macro_f1 = f1_score(all_labels, all_preds, average="macro", zero_division=0)
    weighted_f1 = f1_score(all_labels, all_preds, average="weighted", zero_division=0)

    report = classification_report(
        all_labels, all_preds,
        labels=list(range(len(class_names))),
        target_names=class_names,
        digits=4, zero_division=0,
    )
    cm = confusion_matrix(all_labels, all_preds, labels=list(range(len(class_names))))

    print()
    print("-" * 72)
    print(f"RESULTS — {args.split} ({len(all_labels)} images)")
    print("-" * 72)
    print(f"Top-1 accuracy:  {overall_acc:.2f}%")
    print(f"Top-3 accuracy:  {top3_acc:.2f}%")
    print(f"Macro F1:        {macro_f1:.4f}")
    print(f"Weighted F1:     {weighted_f1:.4f}")
    print()
    print(report)

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"AgriMind v2 evaluation — {args.split}\n")
        f.write("=" * 55 + "\n\n")
        f.write(f"Split file:           {args.split}\n")
        f.write(f"Scenario:             {split.get('scenario', 'original')}\n")
        f.write(f"Description:          {split.get('description', 'N/A')}\n")
        f.write(f"Checkpoint:           {MODEL_PATH.name}\n")
        f.write(f"Checkpoint SHA256:    {ckpt_sha}\n")
        f.write(f"Saved epoch:          {ckpt.get('epoch')}\n")
        f.write(f"Training val_acc:     {ckpt.get('val_acc'):.2f}%\n")
        f.write(f"Training val_macroF1: {ckpt.get('val_macro_f1'):.4f}\n\n")
        f.write(f"Test images:          {len(all_labels)}\n")
        f.write(f"Excluded (per split): {excluded_count}\n")
        if split.get("does_not_claim_leakage_free"):
            f.write(f"Does not claim leakage-free: True\n")
            for item in split.get("not_yet_audited", []):
                f.write(f"  Not yet audited: {item}\n")
        f.write("\n")
        f.write("RESULTS:\n")
        f.write(f"  Top-1 accuracy:  {overall_acc:.2f}%\n")
        f.write(f"  Top-3 accuracy:  {top3_acc:.2f}%\n")
        f.write(f"  Macro F1:        {macro_f1:.4f}\n")
        f.write(f"  Weighted F1:     {weighted_f1:.4f}\n\n")
        f.write("Per-class report:\n")
        f.write(report + "\n\n")
        f.write("Confusion matrix (rows=true, cols=predicted):\n")
        f.write("Class order: " + ", ".join(class_names) + "\n")
        f.write(str(cm) + "\n")

    print(f"\nReport saved:      {report_path}")

    with open(confusion_csv, "w", encoding="utf-8") as f:
        f.write("true\\predicted," + ",".join(class_names) + "\n")
        for i, cname in enumerate(class_names):
            f.write(cname + "," + ",".join(str(v) for v in cm[i]) + "\n")
    print(f"Confusion matrix:  {confusion_csv}")

    print("\n" + "=" * 72)
    print(f"Evaluation complete — {args.split}")
    print("=" * 72)


if __name__ == "__main__":
    main()