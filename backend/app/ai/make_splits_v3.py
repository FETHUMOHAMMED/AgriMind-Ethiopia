"""Create two leakage-audited split variants for AgriMind v2 evaluation.

  Scenario A (splits_scenarioA.json):
    Excludes only the 3 confirmed byte-identical test/train duplicates
    (pairs 9, 10, 11). SHA-256 re-verified at runtime for each pair.
    Test partition: 3,114 -> 3,111 images.

  Scenario B (splits_scenarioB.json):
    Also excludes 5 suspected same-leaf test images (pairs 4-8).
    These have DIFFERENT SHA-256 hashes and are visually similar (pixel
    MAE 9.97-23.05). LABELED AS SUSPECTED, NOT CONFIRMED.
    Test partition: 3,114 -> 3,106 images.

Both scenarios leave training and validation partitions UNCHANGED.

Caveats recorded in both output files:
  - Confirmed byte-level leakage: 3 test images (Scenario A resolves this)
  - Suspected same-leaf overlap: 5 test images (Scenario B resolves this)
  - NOT YET AUDITED: train/validation boundary (10 pHash candidates found)
  - Splits are NOT labeled "leakage-free"; only "leakage-partially-audited"

Original splits.json is preserved unchanged.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(r"C:\projects\AgriMind-Ethiopia\backend\app\ai\datasets")
SPLITS_V1 = ROOT / "splits.json"
SPLITS_A  = ROOT / "splits_scenarioA.json"
SPLITS_B  = ROOT / "splits_scenarioB.json"
DATA_DIR  = ROOT / "flat_crops"

# Confirmed byte-identical duplicates (SHA-256 re-verified at runtime)
# Format: (test_rel, train_rel, expected_sha256)  -- SINGLE class prefix
CONFIRMED_DUPLICATES = [
    (
        "tomato___late_blight/Tomato_Late_blight_1a69b38b-c4eb-42c4-9584-bcb14fb8db0c___GHLB2 Leaf 9011.JPG",
        "tomato___late_blight/Tomato_Late_blight_2c47b891-3c97-48f1-a2cc-5aa53d3a1148___GHLB2 Leaf 9011.JPG",
        "7ff8410db407008bb9aecf0cc5505f2b47ffd89e508413a30ea983b4bc169714",
    ),
    (
        "tomato___late_blight/Tomato_Late_blight_bd4f09bd-ee85-4ab1-bce0-8cde3fdd7f1b___GHLB_PS Leaf 23.7 Day 13.jpg",
        "tomato___late_blight/Tomato_Late_blight_48c55974-9fe9-4f4b-94f7-c8cd127d1e05___GHLB_PS Leaf 23.7 Day 13.jpg",
        "375eee7b5da77c7afdd73d089574bee3148d04cbe266ee070ee4774d26aca750",
    ),
    (
        "tomato___late_blight/Tomato_Late_blight_3fae9c64-18f0-4a67-9f97-554248bb1bed___GHLB_PS Leaf 24 Day 16.jpg",
        "tomato___late_blight/Tomato_Late_blight_5de6da85-f8c4-48c4-b463-3e6bd78884cc___GHLB_PS Leaf 24 Day 16.jpg",
        "4913a3835e692530e507d542caccacc0d0a7b2fd708782cdec6236a1a0dbbcd6",
    ),
]

# Suspected same-leaf pairs — NOT confirmed duplicates.
SUSPECTED_RELATED = [
    (
        "tomato___bacterial_spot/Tomato_Bacterial_spot_6d746b6c-52f8-4831-b541-c74d0984c130___GCREC_Bact.Sp 3169.JPG",
        "tomato___bacterial_spot/Tomato_Bacterial_spot_196be0af-51c3-4587-bd91-9a606631d4f3___GCREC_Bact.Sp 3453.JPG",
        "pair_4", 16.21,
    ),
    (
        "tomato___bacterial_spot/Tomato_Bacterial_spot_29184f19-db21-475d-8032-a8b7c3a9c7f4___GCREC_Bact.Sp 5784.JPG",
        "tomato___bacterial_spot/Tomato_Bacterial_spot_5c5dbca4-4322-4227-a543-6ff6f876a531___GCREC_Bact.Sp 5785.JPG",
        "pair_5", 21.54,
    ),
    (
        "tomato___bacterial_spot/Tomato_Bacterial_spot_741e2f09-1b62-42c2-b218-6504d57c0f27___GCREC_Bact.Sp 3302.JPG",
        "tomato___bacterial_spot/Tomato_Bacterial_spot_e2286f6d-1e30-4528-ab51-84c18a16b7e1___GCREC_Bact.Sp 3503.JPG",
        "pair_6", 12.88,
    ),
    (
        "tomato___healthy/Tomato_healthy_9b5626b0-ea1d-45d0-bc41-c898f7253a75___GH_HL Leaf 315.2.JPG",
        "tomato___healthy/Tomato_healthy_71967e69-6356-49c1-81ce-624792b4d964___GH_HL Leaf 315.1.JPG",
        "pair_7", 23.05,
    ),
    (
        "tomato___healthy/Tomato_healthy_ca4e96c1-9bf0-49fb-804f-c895905c0584___GH_HL Leaf 210.2.JPG",
        "tomato___healthy/Tomato_healthy_d442075f-73bb-47a0-9545-9b36bca9300b___GH_HL Leaf 210.JPG",
        "pair_8", 9.97,
    ),
]


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_confirmed_duplicates(split_data):
    train_set, test_set = set(), set()
    for c in split_data["per_class"].values():
        train_set.update(c["train"])
        test_set.update(c["test"])

    verified = []
    for test_rel, train_rel, expected_sha in CONFIRMED_DUPLICATES:
        if test_rel not in test_set:
            raise SystemExit(f"Test path not found in splits.json: {test_rel}")
        if train_rel not in train_set:
            raise SystemExit(f"Train path not found in splits.json: {train_rel}")

        test_file = DATA_DIR / test_rel
        train_file = DATA_DIR / train_rel
        if not test_file.is_file():
            raise SystemExit(f"Test file missing: {test_file}")
        if not train_file.is_file():
            raise SystemExit(f"Train file missing: {train_file}")

        test_sha = sha256_of(test_file)
        train_sha = sha256_of(train_file)
        if test_sha != expected_sha:
            raise SystemExit(
                f"SHA-256 mismatch on test {test_rel}\n"
                f"  expected {expected_sha}\n  got      {test_sha}")
        if train_sha != expected_sha:
            raise SystemExit(
                f"SHA-256 mismatch on train {train_rel}\n"
                f"  expected {expected_sha}\n  got      {train_sha}")

        verified.append({
            "test_path": test_rel,
            "train_path": train_rel,
            "sha256": test_sha,
            "verified_at_runtime": True,
        })
    return verified


def verify_suspected_related(split_data):
    train_set, test_set = set(), set()
    for c in split_data["per_class"].values():
        train_set.update(c["train"])
        test_set.update(c["test"])

    verified = []
    for test_rel, train_rel, label, mae in SUSPECTED_RELATED:
        if test_rel not in test_set:
            raise SystemExit(f"Test path not found: {test_rel}")
        if train_rel not in train_set:
            raise SystemExit(f"Train path not found: {train_rel}")

        test_sha = sha256_of(DATA_DIR / test_rel)
        train_sha = sha256_of(DATA_DIR / train_rel)
        if test_sha == train_sha:
            raise SystemExit(
                f"{label} has IDENTICAL SHA-256 — reclassify as confirmed duplicate")

        verified.append({
            "pair": label,
            "test_path": test_rel,
            "train_path": train_rel,
            "pixel_mae": mae,
            "test_sha256": test_sha,
            "train_sha256": train_sha,
            "status": "SUSPECTED_SAME_LEAF_NOT_CONFIRMED",
        })
    return verified


def build_scenario(split_data, exclude_test_paths, metadata):
    new_per_class = {}
    excluded = []
    for cls, entries in split_data["per_class"].items():
        test = []
        for rel in entries["test"]:
            if rel in exclude_test_paths:
                excluded.append({"class": cls, "path": rel})
            else:
                test.append(rel)
        new_per_class[cls] = {
            "train": list(entries["train"]),
            "val": list(entries["val"]),
            "test": test,
            "counts": {
                "train": len(entries["train"]),
                "val": len(entries["val"]),
                "test": len(test),
                "total": len(entries["train"]) + len(entries["val"]) + len(test),
            },
        }
    result = dict(split_data)
    result["per_class"] = new_per_class
    result.update(metadata)
    result["excluded_test_images"] = excluded
    return result


def check_cross_partition(split_data):
    train, val, test = set(), set(), set()
    for c in split_data["per_class"].values():
        train.update(c["train"])
        val.update(c["val"])
        test.update(c["test"])
    return {
        "train_val": len(train & val),
        "train_test": len(train & test),
        "val_test": len(val & test),
    }


def main() -> None:
    if not SPLITS_V1.exists():
        raise SystemExit(f"splits.json not found: {SPLITS_V1}")
    for p in (SPLITS_A, SPLITS_B):
        if p.exists():
            raise SystemExit(f"Refusing to overwrite: {p}")

    split = json.loads(SPLITS_V1.read_text(encoding="utf-8"))

    print("=" * 78)
    print("Verifying CONFIRMED byte-identical duplicates (runtime SHA-256)")
    print("=" * 78)
    confirmed = verify_confirmed_duplicates(split)
    for v in confirmed:
        print(f"  [OK] {v['test_path'].split('/')[-1][:55]}")
        print(f"       sha256={v['sha256']}")

    print()
    print("=" * 78)
    print("Verifying SUSPECTED same-leaf pairs (SHA-256 must differ)")
    print("=" * 78)
    suspected = verify_suspected_related(split)
    for v in suspected:
        print(f"  [SUSPECTED] {v['pair']}: MAE={v['pixel_mae']:.2f}")

    # Scenario A
    a_paths = {v["test_path"] for v in confirmed}
    split_a = build_scenario(split, a_paths, {
        "scenario": "A",
        "description": (
            "Excludes only the 3 confirmed byte-identical duplicates (pairs 9-11). "
            "No speculative exclusions."
        ),
        "confirmed_duplicates_excluded": confirmed,
        "suspected_related_excluded": [],
        "not_yet_audited": [
            "train/validation boundary (10 pHash candidates found, not excluded)",
            "any duplicate pairs beyond the 15 pHash candidates",
        ],
        "does_not_claim_leakage_free": True,
    })
    issues_a = check_cross_partition(split_a)
    if any(issues_a.values()):
        raise SystemExit(f"Scenario A cross-partition duplicate: {issues_a}")
    SPLITS_A.write_text(json.dumps(split_a, indent=2), encoding="utf-8")

    # Scenario B
    b_paths = a_paths | {v["test_path"] for v in suspected}
    split_b = build_scenario(split, b_paths, {
        "scenario": "B",
        "description": (
            "Excludes 3 confirmed byte-identical + 5 suspected same-leaf "
            "candidates (pairs 4-11). Suspected pairs labeled provisional."
        ),
        "confirmed_duplicates_excluded": confirmed,
        "suspected_related_excluded": suspected,
        "not_yet_audited": [
            "train/validation boundary (10 pHash candidates found, not excluded)",
            "any duplicate pairs beyond the 15 pHash candidates",
        ],
        "does_not_claim_leakage_free": True,
    })
    issues_b = check_cross_partition(split_b)
    if any(issues_b.values()):
        raise SystemExit(f"Scenario B cross-partition duplicate: {issues_b}")
    SPLITS_B.write_text(json.dumps(split_b, indent=2), encoding="utf-8")

    print()
    print("=" * 78)
    print("SCENARIO SUMMARY")
    print("=" * 78)
    for label, s, p in [("A", split_a, SPLITS_A), ("B", split_b, SPLITS_B)]:
        train = sum(c["counts"]["train"] for c in s["per_class"].values())
        val = sum(c["counts"]["val"] for c in s["per_class"].values())
        test = sum(c["counts"]["test"] for c in s["per_class"].values())
        print(f"Scenario {label}: {p.name}")
        print(f"  train={train}  val={val}  test={test}  excluded={len(s['excluded_test_images'])}")
        print(f"  cross-partition overlap: {check_cross_partition(s)}")
    print()
    print("Note: validation boundary NOT yet audited. Both scenarios are")
    print("      partial leakage controls, not fully leakage-free evaluations.")


if __name__ == "__main__":
    main()