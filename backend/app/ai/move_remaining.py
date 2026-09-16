import os
import shutil

SOURCE = r"C:\Users\justice\Downloads\image folder"
DEST = r"C:\projects\AgriMind-Ethiopia\backend\app\ai\datasets\ethiopian_crops"

# Keyword mapping for .jfif and .webp files
MAPPING = {
    'coffee_leaf_rust': 'coffee/leaf_rust',
    'coffee leaf rust': 'coffee/leaf_rust',
    'corn_common_rust': 'maize/common_rust',
    'corn common rust': 'maize/common_rust',
    'corn_northern_leaf_blight': 'maize/northern_leaf_blight',
    'corn northern leaf blight': 'maize/northern_leaf_blight',
    'healthy_tomato': 'tomato/healthy',
    'healthy tomato': 'tomato/healthy',
    'potato_early_blight': 'potato/early_blight',
    'potato early blight': 'potato/early_blight',
    'potato_late_blight': 'potato/late_blight',
    'potato late blight': 'potato/late_blight',
    'tomato_early_blight': 'tomato/early_blight',
    'tomato early blight': 'tomato/early_blight',
    'tomato_late_blight': 'tomato/late_blight',
    'tomato late blight': 'tomato/late_blight',
    'wheat_brown_rust': 'wheat/brown_rust',
    'wheat brown rust': 'wheat/brown_rust',
}

def move_remaining():
    if not os.path.exists(SOURCE):
        print(f"Source folder not found")
        return
    
    files = os.listdir(SOURCE)
    moved = 0
    
    for filename in files:
        # Only process .jfif and .webp files
        if not filename.lower().endswith(('.jfif', '.webp')):
            continue
        
        lower_name = filename.lower()
        matched = False
        
        for keyword, dest in MAPPING.items():
            if keyword.lower() in lower_name:
                dest_folder = os.path.join(DEST, dest)
                os.makedirs(dest_folder, exist_ok=True)
                # Convert .jfif/.webp to .jpg extension for consistency
                new_name = filename.rsplit('.', 1)[0] + '.jpg'
                shutil.copy(os.path.join(SOURCE, filename), os.path.join(dest_folder, new_name))
                print(f"Moved: {filename} -> {dest}/{new_name}")
                moved += 1
                matched = True
                break
        
        if not matched:
            print(f"Unmatched: {filename}")
    
    print(f"\nMoved: {moved} files")

if __name__ == '__main__':
    move_remaining()