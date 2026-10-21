"""Generate a reproducible stratified train/val/test split for AgriMind CNN.

Creates splits.json with fixed train/val/test assignments for all classes with
>= MIN_IMAGES_PER_CLASS images. Excludes rare classes (coffee/maize/wheat) that
cannot be reliably learned with the available data.

Run once. Then train_cnn.py and evaluate_cnn.py both load this file for
deterministic, leakage-free evaluation.

Usage:
    cd C:/projects/AgriMind-Ethiopia/backend
    python app/ai/make_splits.py
"""
import json
import random
from collections import defaultdict
from pathlib import Path

from torchvision import datasets

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATA_DIR = Path(r"C:\projects\AgriMind-Ethiopia\backend\app\ai\datasets\flat_crops")
OUTPUT_PATH = Path(r"C:\projects\AgriMind-Ethiopia\backend\app\ai\datasets\splits.json")
SEED = 42
MIN_IMAGES_PER_CLASS = 100   # excludes coffee(4), maize(3+4), wheat(3)
SPLIT_RATIOS = {"train": 0.70, "val": 0.15, "test": 0.15}
IMG_SIZE = 128


def main() -> None:
    random.seed(SEED)

    if not DATA_DIR.is_dir():
        raise SystemExit(f"Dataset not found: {DATA_DIR}")

    ds = datasets.ImageFolder(str(DATA_DIR))
    class_names = ds.classes
    samples = ds.samples  # list of (absolute_path, class_idx)

    # Group relative paths per class
    by_class: dict[str, list[str]] = defaultdict(list)
    for path, idx in samples:
        rel = Path(path).relative_to(DATA_DIR).as_posix()
        by_class[class_names[idx]].append(rel)

    # Decide included vs excluded classes
    included: list[str] = []
    excluded: list[dict] = []
    for cname in class_names:
        count = len(by_class[cname])
        if count >= MIN_IMAGES_PER_CLASS:
            included.append(cname)
        else:
            excluded.append({
                "name": cname,
                "count": count,
                "reason": f"insufficient_samples (need >= {MIN_IMAGES_PER_CLASS})",
            })

    # Stratified split
    per_class: dict[str, dict] = {}
    for cname in included:
        files = sorted(by_class[cname])
        random.shuffle(files)
        n = len(files)
        n_train = int(n * SPLIT_RATIOS["train"])
        n_val = int(n * SPLIT_RATIOS["val"])
        train_files = files[:n_train]
        val_files = files[n_train:n_train + n_val]
        test_files = files[n_train + n_val:]
        per_class[cname] = {
            "train": train_files,
            "val": val_files,
            "test": test_files,
            "counts": {
                "train": len(train_files),
                "val": len(val_files),
                "test": len(test_files),
                "total": n,
            },
        }

    # Build final JSON
    split = {
        "seed": SEED,
        "img_size": IMG_SIZE,
        "split_ratios": SPLIT_RATIOS,
        "data_dir": str(DATA_DIR),
        "min_images_per_class": MIN_IMAGES_PER_CLASS,
        "class_names": included,                       # index order = list order
        "class_to_idx": {c: i for i, c in enumerate(included)},
        "excluded_classes": excluded,
        "per_class": per_class,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(split, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------
    # Human-readable summary
    # ------------------------------------------------------------------
    print("=" * 72)
    print(f"SPLITS SAVED: {OUTPUT_PATH}")
    print(f"Seed: {SEED}  |  img_size: {IMG_SIZE}")
    print(f"Included classes: {len(included)}")
    print(f"Excluded classes: {len(excluded)}")
    print("=" * 72)

    print(f"\n{'Class':<42}{'Train':>6}{'Val':>5}{'Test':>5}{'Total':>6}")
    print("-" * 72)
    for cname in included:
        c = per_class[cname]["counts"]
        print(f"{cname:<42}{c['train']:>6}{c['val']:>5}{c['test']:>5}{c['total']:>6}")

    print("\n--- Excluded (insufficient data) ---")
    for exc in excluded:
        print(f"  {exc['name']:<42}{exc['count']:>4} images — {exc['reason']}")

    tot_train = sum(c["counts"]["train"] for c in per_class.values())
    tot_val = sum(c["counts"]["val"] for c in per_class.values())
    tot_test = sum(c["counts"]["test"] for c in per_class.values())
    tot_exc = sum(e["count"] for e in excluded)

    print()
    print("-" * 72)
    print(f"Totals: {tot_train} train + {tot_val} val + {tot_test} test "
          f"= {tot_train + tot_val + tot_test} images used for 15-class model")
    print(f"Excluded from training: {tot_exc} images across {len(excluded)} classes")
    print("=" * 72)

    # Sanity assertions
    assert tot_train + tot_val + tot_test + tot_exc == len(samples), \
        "Split does not cover all images — check for missing files."
    assert all(c["counts"]["total"] > 0 for c in per_class.values()), \
        "Empty class in split — check dataset."
    print("\n✅ All sanity checks passed.")


if __name__ == "__main__":
    main()