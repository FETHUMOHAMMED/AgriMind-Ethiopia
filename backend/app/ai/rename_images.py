import os

# ============================================================
# BULK IMAGE RENAMER
# ============================================================
# Edit the values below for each batch, then run the script.
# ============================================================

FOLDER = r"C:\projects\AgriMind-Ethiopia\backend\app\ai\datasets\field_images\raw\coffee\leaf_rust"

CASE_ID = "ETH-0001"
CROP = "Coffee"
DISEASE = "LeafRust"
DATE = "20261115"

# ============================================================

def rename_images():
    if not os.path.exists(FOLDER):
        print(f"Folder not found: {FOLDER}")
        return

    images = sorted([f for f in os.listdir(FOLDER) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])

    if not images:
        print("No images found.")
        return

    print(f"Found {len(images)} images in {FOLDER}")

    for i, old_name in enumerate(images, start=1):
        ext = os.path.splitext(old_name)[1].lower()
        new_name = f"{CASE_ID}_{CROP}_{DISEASE}_{DATE}_{i:02d}{ext}"

        old_path = os.path.join(FOLDER, old_name)
        new_path = os.path.join(FOLDER, new_name)

        # Skip if already renamed
        if old_name == new_name:
            print(f"  Skipped (already correct): {old_name}")
            continue

        os.rename(old_path, new_path)
        print(f"  {old_name} → {new_name}")

    print("Done!")

if __name__ == "__main__":
    rename_images()