"""
AGRIMIND 31-IMAGE AUDIT
========================
Audits the Ethiopian reference images to establish what we actually have.
Output: CSV file with full provenance tracking.
"""

import os
import csv
from datetime import datetime

# ============================================================
# CONFIGURATION
# ============================================================
BASE = r"C:\projects\AgriMind-Ethiopia\backend\app\ai\datasets\ethiopian_crops"
OUTPUT_DIR = r"C:\projects\AgriMind-Ethiopia\EAII-Evidence-Pack\A_Dataset_Evidence"
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "31_IMAGE_AUDIT.csv")
OUTPUT_SUMMARY = os.path.join(OUTPUT_DIR, "31_IMAGE_AUDIT_SUMMARY.txt")

# ============================================================
# HELPERS
# ============================================================
def get_file_size_mb(path):
    try:
        return round(os.path.getsize(path) / (1024 * 1024), 3)
    except Exception:
        return 0

def get_image_dimensions(path):
    try:
        from PIL import Image
        with Image.open(path) as img:
            return f"{img.width}x{img.height}"
    except Exception:
        return "Unknown"

# ============================================================
# AUDIT
# ============================================================
def audit():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not os.path.exists(BASE):
        print(f"ERROR: Base folder not found: {BASE}")
        print("Check the path and try again.")
        return

    audit_rows = []
    image_counter = 0

    for crop in sorted(os.listdir(BASE)):
        crop_dir = os.path.join(BASE, crop)
        if not os.path.isdir(crop_dir):
            continue

        for disease in sorted(os.listdir(crop_dir)):
            disease_dir = os.path.join(crop_dir, disease)
            if not os.path.isdir(disease_dir):
                continue

            for filename in sorted(os.listdir(disease_dir)):
                if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.jfif', '.webp')):
                    continue

                image_counter += 1
                full_path = os.path.join(disease_dir, filename)

                audit_rows.append({
                    'Image_ID': f"ETH-{image_counter:04d}",
                    'Crop': crop,
                    'Disease': disease,
                    'Filename': filename,
                    'File_Size_MB': get_file_size_mb(full_path),
                    'Dimensions': get_image_dimensions(full_path),
                    'Source': 'Internet',
                    'Region': 'Unknown',
                    'GPS': 'None',
                    'Collector': 'None',
                    'Date_Collected': '2026-09',
                    'Expert_Label': 'No',
                    'Lab_Test': 'No',
                    'Verification_Level': 'Tier 1',
                    'Notes': 'Reference image from public source'
                })

    # Write CSV
    if audit_rows:
        with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=audit_rows[0].keys())
            writer.writeheader()
            writer.writerows(audit_rows)

    # Write summary
    with open(OUTPUT_SUMMARY, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("AGRIMIND 31-IMAGE AUDIT SUMMARY\n")
        f.write("=" * 60 + "\n")
        f.write(f"Audit Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"Total Images Found: {len(audit_rows)}\n\n")

        # By crop
        by_crop = {}
        for row in audit_rows:
            by_crop[row['Crop']] = by_crop.get(row['Crop'], 0) + 1

        f.write("BY CROP:\n")
        for crop, count in sorted(by_crop.items()):
            f.write(f"  {crop}: {count}\n")
        f.write("\n")

        # By disease
        by_disease = {}
        for row in audit_rows:
            key = f"{row['Crop']}/{row['Disease']}"
            by_disease[key] = by_disease.get(key, 0) + 1

        f.write("BY CROP/DISEASE:\n")
        for key, count in sorted(by_disease.items()):
            f.write(f"  {key}: {count}\n")
        f.write("\n")

        # By verification level
        by_tier = {}
        for row in audit_rows:
            tier = row['Verification_Level']
            by_tier[tier] = by_tier.get(tier, 0) + 1

        f.write("BY VERIFICATION LEVEL:\n")
        for tier, count in sorted(by_tier.items()):
            f.write(f"  {tier}: {count}\n")
        f.write("\n")

        # By source
        by_source = {}
        for row in audit_rows:
            src = row['Source']
            by_source[src] = by_source.get(src, 0) + 1

        f.write("BY SOURCE:\n")
        for src, count in sorted(by_source.items()):
            f.write(f"  {src}: {count}\n")
        f.write("\n")

        # Honest assessment
        f.write("=" * 60 + "\n")
        f.write("HONEST ASSESSMENT\n")
        f.write("=" * 60 + "\n")
        f.write("All images are currently classified as Tier 1 (unverified).\n")
        f.write("Source is recorded as 'Internet' — NOT Ethiopian field data.\n")
        f.write("No expert verification has been performed yet.\n")
        f.write("No laboratory confirmation exists for any image.\n\n")
        f.write("ACTION REQUIRED:\n")
        f.write("1. Agri Expert must review each image and update Expert_Label\n")
        f.write("2. Source must be verified and corrected if possible\n")
        f.write("3. Select 5-10 ambiguous cases for laboratory testing\n")
        f.write("4. Add these images to the master register with full metadata\n")

    # Print summary to console
    print("=" * 60)
    print("AGRIMIND 31-IMAGE AUDIT COMPLETE")
    print("=" * 60)
    print(f"Total images found: {len(audit_rows)}")
    print()
    print("BY CROP:")
    for crop, count in sorted(by_crop.items()):
        print(f"  {crop}: {count}")
    print()
    print("CSV saved to:")
    print(f"  {OUTPUT_CSV}")
    print()
    print("Summary saved to:")
    print(f"  {OUTPUT_SUMMARY}")
    print()
    print("=" * 60)
    print("NEXT STEP: Have your Agri Expert review each row")
    print("and update Expert_Label, Source, and Verification_Level")
    print("=" * 60)

if __name__ == "__main__":
    audit()