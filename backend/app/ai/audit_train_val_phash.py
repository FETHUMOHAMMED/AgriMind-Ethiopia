"""Train/validation boundary duplicate audit for AgriMind v2.

Runs the same pHash + SHA-256 methodology used on the test boundary,
but targeting train<->val pairs only. Read-only: does not modify any split.

Outputs:
  TRAIN_VAL_PHASH_AUDIT.csv    -- all candidate pairs with full paths + hashes
  TRAIN_VAL_PHASH_AUDIT_SUMMARY.txt  -- categorized summary
"""
import hashlib
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import imagehash
from PIL import Image

SPLITS = Path(r"C:\projects\AgriMind-Ethiopia\backend\app\ai\datasets\splits.json")
DATA = Path(r"C:\projects\AgriMind-Ethiopia\backend\app\ai\datasets\flat_crops")
OUTPUT_DIR = Path(r"C:\projects\AgriMind-Ethiopia\EAII-Evidence-Pack\B_AI_Evidence\Metrics")
CSV_OUT = OUTPUT_DIR / "TRAIN_VAL_PHASH_AUDIT.csv"
SUMMARY_OUT = OUTPUT_DIR / "TRAIN_VAL_PHASH_AUDIT_SUMMARY.txt"

PHASH_SIZE = 8
THRESHOLD = 5


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def key_of(rel: str) -> str:
    fname = rel.split("/")[-1]
    return fname.split("___", 1)[1] if "___" in fname else fname


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    split = json.loads(SPLITS.read_text(encoding="utf-8"))

    train = []
    val = []
    for cls, entries in split["per_class"].items():
        for rel in entries["train"]:
            train.append((cls, rel))
        for rel in entries["val"]:
            val.append((cls, rel))

    print(f"Train: {len(train)}  Val: {len(val)}")

    # Hash val set by class
    print("Hashing val set...")
    val_hashes = defaultdict(list)
    for cls, rel in val:
        with Image.open(DATA / rel) as im:
            val_hashes[cls].append((rel, imagehash.phash(im.convert("RGB"), hash_size=PHASH_SIZE)))

    # Hash train set and compare to val
    print("Hashing train set (this takes ~2-3 minutes)...")
    candidates = []
    for i, (cls, rel_a) in enumerate(train, 1):
        if i % 2000 == 0:
            print(f"  {i}/{len(train)}")
        with Image.open(DATA / rel_a) as im:
            ha = imagehash.phash(im.convert("RGB"), hash_size=PHASH_SIZE)
        for rel_b, hb in val_hashes.get(cls, []):
            dist = ha - hb
            if dist <= THRESHOLD:
                candidates.append((cls, rel_a, rel_b, dist))

    # Classify with SHA-256
    print(f"\nFound {len(candidates)} candidates. Computing SHA-256...")
    results = []
    for cls, rel_a, rel_b, dist in candidates:
        sha_a = sha256_of(DATA / rel_a)
        sha_b = sha256_of(DATA / rel_b)
        if sha_a == sha_b:
            status = "BYTE_IDENTICAL"
        elif key_of(rel_a) == key_of(rel_b):
            status = "SAME_ORIGINAL_NAME"
        elif dist == 0:
            status = "SAME_PHASH_DIFFERENT_FILES"
        else:
            status = "VISUALLY_SIMILAR_DISTINCT_FILES"
        results.append({
            "class": cls,
            "train_rel": rel_a,
            "val_rel": rel_b,
            "phash_distance": dist,
            "train_key": key_of(rel_a),
            "val_key": key_of(rel_b),
            "train_sha256": sha_a,
            "val_sha256": sha_b,
            "status": status,
        })

    # Write CSV
    import csv
    with open(CSV_OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys() if results else [
            "class", "train_rel", "val_rel", "phash_distance",
            "train_key", "val_key", "train_sha256", "val_sha256", "status"
        ])
        writer.writeheader()
        writer.writerows(results)

    # Summary by status
    by_status = defaultdict(int)
    for r in results:
        by_status[r["status"]] += 1

    with open(SUMMARY_OUT, "w", encoding="utf-8") as f:
        f.write("=" * 78 + "\n")
        f.write("TRAIN/VALIDATION BOUNDARY pHASH AUDIT\n")
        f.write("=" * 78 + "\n")
        f.write(f"Audit date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"Split file: {SPLITS.name}\n")
        f.write(f"Train: {len(train)} images   Val: {len(val)} images\n")
        f.write(f"pHash size: {PHASH_SIZE}x{PHASH_SIZE}  Threshold: Hamming <= {THRESHOLD}/64\n\n")

        f.write("RESULTS:\n")
        f.write("-" * 78 + "\n")
        for status, count in sorted(by_status.items()):
            f.write(f"  {status:<40} {count}\n")
        f.write(f"\n  TOTAL candidate pairs: {len(results)}\n\n")

        if by_status.get("BYTE_IDENTICAL"):
            f.write("⚠️  BYTE-IDENTICAL PAIRS FOUND — val leakage confirmed\n")
            f.write("-" * 78 + "\n")
            for r in results:
                if r["status"] == "BYTE_IDENTICAL":
                    f.write(f"  {r['class']}: {r['train_key']}\n")
            f.write("\n")
        else:
            f.write("✅ No byte-identical pairs across train/val boundary.\n\n")

        f.write("INTERPRETATION:\n")
        f.write("-" * 78 + "\n")
        f.write("Val leakage affects model-selection evidence (best-epoch choice),\n")
        f.write("not the reported test metric. Even if some candidates were confirmed\n")
        f.write("duplicates, they would only inflate val_acc by at most\n")
        f.write(f"{len(results)}/{len(val)} = {100*len(results)/len(val):.2f}pp, affecting\n")
        f.write("which epoch is saved — not the 95.27% test result.\n\n")
        f.write("Splits are NOT modified by this audit. This is documentation only.\n")

    print()
    print("=" * 78)
    print("TRAIN/VAL PHASH AUDIT COMPLETE")
    print("=" * 78)
    print(f"Candidates: {len(results)}")
    for status, count in sorted(by_status.items()):
        print(f"  {status:<40} {count}")
    print()
    print(f"CSV:     {CSV_OUT}")
    print(f"Summary: {SUMMARY_OUT}")


if __name__ == "__main__":
    main()