import os
import shutil

SOURCE = "datasets/ethiopian_crops"
DEST = "datasets/flat_crops"

# Clear destination if exists
if os.path.exists(DEST):
    shutil.rmtree(DEST)
os.makedirs(DEST, exist_ok=True)

total = 0
for crop in os.listdir(SOURCE):
    crop_dir = os.path.join(SOURCE, crop)
    if not os.path.isdir(crop_dir):
        continue
    for disease in os.listdir(crop_dir):
        disease_dir = os.path.join(crop_dir, disease)
        if not os.path.isdir(disease_dir):
            continue

        class_name = f"{crop}___{disease}"
        dest_dir = os.path.join(DEST, class_name)
        os.makedirs(dest_dir, exist_ok=True)

        copied = 0
        for f in os.listdir(disease_dir):
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.jfif', '.webp')):
                src_file = os.path.join(disease_dir, f)
                dst_file = os.path.join(dest_dir, f)
                try:
                    shutil.copy(src_file, dst_file)
                    copied += 1
                except:
                    pass

        if copied > 0:
            print(f"{class_name}: {copied} images")
            total += copied

print(f"\nTOTAL: {total} images across {len(os.listdir(DEST))} classes")