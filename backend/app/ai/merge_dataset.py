import os
import shutil

SOURCE = r"C:\Users\justice\Downloads\plant_disease_model.h5"
DEST = r"C:\projects\AgriMind-Ethiopia\backend\app\ai\datasets\ethiopian_crops"

MAPPING = {
    "Tomato_Early_blight": "tomato/early_blight",
    "Tomato_Late_blight": "tomato/late_blight",
    "Tomato_healthy": "tomato/healthy",
    "Tomato_Bacterial_spot": "tomato/bacterial_spot",
    "Tomato_Leaf_Mold": "tomato/leaf_mold",
    "Tomato_Septoria_leaf_spot": "tomato/septoria_leaf_spot",
    "Tomato_Spider_mites_Two_spotted_spider_mite": "tomato/spider_mites",
    "Tomato__Target_Spot": "tomato/target_spot",
    "Tomato__Tomato_mosaic_virus": "tomato/mosaic_virus",
    "Tomato__Tomato_YellowLeaf__Curl_Virus": "tomato/yellow_leaf_curl",
    "Potato___Early_blight": "potato/early_blight",
    "Potato___Late_blight": "potato/late_blight",
    "Potato___healthy": "potato/healthy",
    "Pepper__bell___Bacterial_spot": "pepper/bacterial_spot",
    "Pepper__bell___healthy": "pepper/healthy",
}

def merge():
    total_copied = 0
    for src_name, dest_path in MAPPING.items():
        src_folder = os.path.join(SOURCE, src_name)
        if not os.path.exists(src_folder):
            print(f"SKIP (not found): {src_name}")
            continue

        dest_folder = os.path.join(DEST, dest_path)
        os.makedirs(dest_folder, exist_ok=True)

        files = [f for f in os.listdir(src_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        copied = 0
        for f in files:
            src_file = os.path.join(src_folder, f)
            dst_file = os.path.join(dest_folder, f"{src_name}_{f}")
            try:
                shutil.copy(src_file, dst_file)
                copied += 1
            except Exception as e:
                print(f"Error: {e}")

        print(f"{src_name} -> {dest_path}: {copied} images")
        total_copied += copied

    print(f"\nTOTAL COPIED: {total_copied} images")

if __name__ == '__main__':
    merge()