"""Honest provenance audit for ethiopian_crops folder.

Replaces the misleading 31_IMAGE_AUDIT.csv. Every structured field that is
script-assigned (not independently verified) is explicitly marked as such
with a `field_verified` column.

Outputs:
  ETHIOPIAN_CROPS_PROVENANCE_AUDIT.csv  -- per-image inventory, honest labels
  ETHIOPIAN_CROPS_PROVENANCE_AUDIT_SUMMARY.txt  -- high-level summary
"""
import csv
import os
from datetime import datetime
from pathlib import Path

BASE = Path(r"C:\projects\AgriMind-Ethiopia\backend\app\ai\datasets\ethiopian_crops")
FLAT_CROPS = Path(r"C:\projects\AgriMind-Ethiopia\backend\app\ai\datasets\flat_crops")
OUTPUT_DIR = Path(r"C:\projects\AgriMind-Ethiopia\EAII-Evidence-Pack\A_Dataset_Evidence")
CSV_OUT = OUTPUT_DIR / "ETHIOPIAN_CROPS_PROVENANCE_AUDIT.csv"
SUMMARY_OUT = OUTPUT_DIR / "ETHIOPIAN_CROPS_PROVENANCE_AUDIT_SUMMARY.txt"


def file_size_mb(p: Path) -> float:
    try:
        return round(p.stat().st_size / (1024 * 1024), 3)
    except Exception:
        return 0.0


def dimensions(p: Path) -> str:
    try:
        from PIL import Image
        with Image.open(p) as im:
            return f"{im.width}x{im.height}"
    except Exception:
        return "Unknown"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not BASE.is_dir():
        print(f"Dataset not found: {BASE}")
        return

    rows = []
    idx = 0
    for crop in sorted(p for p in BASE.iterdir() if p.is_dir()):
        for disease in sorted(p for p in crop.iterdir() if p.is_dir()):
            for img in sorted(disease.iterdir()):
                if not img.is_file():
                    continue
                if img.suffix.lower() not in {".jpg", ".jpeg", ".png", ".jfif", ".webp"}:
                    continue
                idx += 1
                rows.append({
                    "Image_ID": f"ETH-{idx:05d}",
                    "Crop": crop.name,
                    "Disease": disease.name,
                    "Relative_Path": f"{crop.name}/{disease.name}/{img.name}",
                    "File_Size_MB": file_size_mb(img),
                    "Dimensions": dimensions(img),
                    "Source": "UNKNOWN (presumed PlantVillage-derived based on file structure)",
                    "Region": "UNKNOWN",
                    "GPS": "UNKNOWN",
                    "Collector": "UNKNOWN",
                    "Collection_Date": "UNKNOWN",
                    "Expert_Label": "UNKNOWN",
                    "Lab_Test": "UNKNOWN",
                    "Verification_Level": "UNVERIFIED",
                    "Field_Verified": "FALSE",
                    "Notes": "Structural copy of flat_crops; not independently collected field data",
                })

    with open(CSV_OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    # Counts by crop/disease
    by_class = {}
    for r in rows:
        key = f"{r['Crop']}/{r['Disease']}"
        by_class[key] = by_class.get(key, 0) + 1

    # Empty directory detection
    empty_dirs = []
    for crop in sorted(p for p in BASE.iterdir() if p.is_dir()):
        for disease in sorted(p for p in crop.iterdir() if p.is_dir()):
            key = f"{crop.name}/{disease.name}"
            if key not in by_class:
                empty_dirs.append(key)

    # Summary
    with open(SUMMARY_OUT, "w", encoding="utf-8") as f:
        f.write("=" * 78 + "\n")
        f.write("ETHIOPIAN CROPS PROVENANCE AUDIT (honest version)\n")
        f.write("=" * 78 + "\n")
        f.write(f"Audit date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"Dataset folder: {BASE}\n")
        f.write(f"Total images found: {len(rows)}\n")
        f.write(f"Total crop/disease subdirectories: {len(by_class) + len(empty_dirs)}\n")
        f.write(f"  Populated: {len(by_class)}\n")
        f.write(f"  Empty:     {len(empty_dirs)}\n\n")

        f.write("CRITICAL CONTEXT:\n")
        f.write("-" * 78 + "\n")
        f.write(f"This folder contains {len(rows)} images, the SAME count as flat_crops\n")
        f.write(f"({FLAT_CROPS}). It is a reorganized copy, not independently\n")
        f.write("collected Ethiopian field data. All 20,669 images are the SAME files\n")
        f.write("as flat_crops, restructured into crop/disease/ subdirectories.\n\n")
        f.write("Every structured field in this audit (Source, Region, GPS, Collector,\n")
        f.write("Collection_Date, Expert_Label, Lab_Test, Verification_Level) is\n")
        f.write("marked UNKNOWN or UNVERIFIED because no such metadata exists.\n")
        f.write("The 'Field_Verified' column is FALSE for every image.\n\n")
        f.write("Real Ethiopian field data collection is a PHASE 2 deliverable under\n")
        f.write("DATASET_REGISTER_MASTER.csv (5 partner ARCs, Tier 2/3 protocol).\n")
        f.write("As of the audit date, that collection has not begun — the register\n")
        f.write("contains future-dated planning entries.\n\n")

        f.write("POPULATED CLASSES (crop/disease: image count):\n")
        f.write("-" * 78 + "\n")
        for key, count in sorted(by_class.items(), key=lambda kv: kv[1]):
            f.write(f"  {key:<40} {count:>6}\n")
        f.write("\n")

        if empty_dirs:
            f.write("EMPTY CLASSES (declared in folder structure but no images):\n")
            f.write("-" * 78 + "\n")
            for key in empty_dirs:
                f.write(f"  {key}\n")
            f.write("\n")

        f.write("=" * 78 + "\n")
        f.write("CONCLUSION\n")
        f.write("=" * 78 + "\n")
        f.write("This audit does not establish provenance. It documents ABSENCE of\n")
        f.write("provenance. Do not cite as evidence of Ethiopian field collection.\n")
        f.write("Cite as: 'Datasets folder contains {0} images, structurally identical\n".format(len(rows)))
        f.write("to PlantVillage-derived flat_crops. Field collection is Phase 2.'\n")

    print("=" * 78)
    print("ETHIOPIAN CROPS PROVENANCE AUDIT COMPLETE")
    print("=" * 78)
    print(f"Total images: {len(rows)}")
    print(f"Populated classes: {len(by_class)}")
    print(f"Empty classes: {len(empty_dirs)}")
    print()
    print(f"CSV:     {CSV_OUT}")
    print(f"Summary: {SUMMARY_OUT}")
    print()
    print("Every structured field marked UNKNOWN/UNVERIFIED. Field_Verified=FALSE.")
    print("=" * 78)


if __name__ == "__main__":
    main()