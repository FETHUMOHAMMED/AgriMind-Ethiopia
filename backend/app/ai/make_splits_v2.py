"""Create splits_v2.json — leakage-controlled split for AgriMind v2.

Excludes 8 test-side images with confirmed or suspected training overlap:
  - 3 byte-identical (SHA-256 match): pairs 9, 10, 11
  - 5 same-leaf candidates (MAE 9.97-23.05): pairs 4, 5, 6, 7, 8

Training and validation partitions are UNCHANGED (the training-side copies
remain legitimate training data). Only the test partition is reduced:
3,114 -> 3,106 images.

Original splits.json is preserved for reproducibility. This script writes
splits_v2.json alongside it.
"""
import json
from pathlib import Path

SPLITS_V1 = Path(r"C:\projects\AgriMind-Ethiopia\backend\app\ai\datasets\splits.json")
SPLITS_V2 = Path(r"C:\projects\AgriMind-Ethiopia\backend\app\ai\datasets\splits_v2.json")

# Test-side filenames to remove (uniquely identified by embedded PlantVillage name)
EXCLUDE_TEST_KEYS = [
    "JR_B.Spot 3381.JPG",              # pair 1 - actually excluded here as precaution
    "JR_HL 8411.JPG",                  # pair 2
    "RS_Early.B 7972.JPG",             # pair 3
    "GCREC_Bact.Sp 3169.JPG",          # pair 4
    "GCREC_Bact.Sp 5784.JPG",          # pair 5
    "GCREC_Bact.Sp 3302.JPG",          # pair 6
    "GH_HL Leaf 315.2.JPG",            # pair 7
    "GH_HL Leaf 210.2.JPG",            # pair 8
    "GHLB2 Leaf 9011.JPG",             # pair 9  byte-identical
    "GHLB_PS Leaf 23.7 Day 13.jpg",    # pair 10 byte-identical
    "GHLB_PS Leaf 24 Day 16.jpg",      # pair 11 byte-identical
    "Crnl_L.Mold 6700.JPG",            # pair 12
    "Com.G_SpM_FL 1420.JPG",           # pair 13
    "Com.G_SpM_FL 9523.JPG",           # pair 14
    "Com.G_SpM_FL 9559.JPG",           # pair 15
]

# Actually only exclude the 8 same-leaf/byte-identical pairs by default.
# Change to EXCLUDE_TEST_KEYS[:] to also exclude the 7 "coincidentally similar" pairs.
EXCLUDE_8 = EXCLUDE_TEST_KEYS[3:11]  # pairs 4,5,6,7,8,9,10,11

# For strict mode (all 15): EXCLUDE = EXCLUDE_TEST_KEYS
EXCLUDE = EXCLUDE_8


def key_of(rel_path: str) -> str:
    """Extract the PlantVillage embedded name from a relative path."""
    fname = rel_path.split("/")[-1]
    if "___" in fname:
        return fname.split("___", 1)[1]
    return fname


def main() -> None:
    split = json.loads(SPLITS_V1.read_text(encoding="utf-8"))

    excluded = []
    new_per_class = {}

    for cls, entries in split["per_class"].items():
        train = list(entries["train"])  # unchanged
        val = list(entries["val"])      # unchanged
        test = list(entries["test"])    # filter here

        kept_test = []
        for rel in test:
            if key_of(rel) in EXCLUDE:
                excluded.append({"class": cls, "path": rel,
                                 "key": key_of(rel)})
            else:
                kept_test.append(rel)

        new_per_class[cls] = {
            "train": train,
            "val": val,
            "test": kept_test,
            "counts": {
                "train": len(train),
                "val": len(val),
                "test": len(kept_test),
                "total": len(train) + len(val) + len(kept_test),
            },
        }

    split_v2 = dict(split)
    split_v2["per_class"] = new_per_class
    split_v2["leakage_controlled"] = True
    split_v2["parent_split"] = "splits.json"
    split_v2["excluded_test_images"] = excluded
    split_v2["exclusion_reason"] = (
        "Confirmed byte-identical duplicates (pairs 9,10,11 - SHA256 match) "
        "and same-leaf candidates (pairs 4,5,6,7,8 - MAE 9.97-23.05). "
        "Training and validation partitions unchanged."
    )

    SPLITS_V2.write_text(json.dumps(split_v2, indent=2), encoding="utf-8")

    # Summary
    print("=" * 72)
    print(f"splits_v2.json written: {SPLITS_V2}")
    print(f"Excluded test images:   {len(excluded)}")
    tot_train = sum(c["counts"]["train"] for c in new_per_class.values())
    tot_val = sum(c["counts"]["val"] for c in new_per_class.values())
    tot_test = sum(c["counts"]["test"] for c in new_per_class.values())
    print(f"Train: {tot_train} (unchanged from v1)")
    print(f"Val:   {tot_val} (unchanged from v1)")
    print(f"Test:  {tot_test} (was 3114)")
    print()
    print("Excluded (removed from test set only):")
    for e in excluded:
        print(f"  - {e['class']}/{e['key']}")
    print("=" * 72)


if __name__ == "__main__":
    main()