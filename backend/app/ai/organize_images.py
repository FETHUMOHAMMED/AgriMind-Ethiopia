import os
import shutil

SOURCE = r"C:\Users\justice\Downloads\image folder"
DEST = r"C:\projects\AgriMind-Ethiopia\backend\app\ai\datasets\ethiopian_crops"

# Keyword mapping — add more as needed
MAPPING = {
    'tomato_early': 'tomato/early_blight',
    'tomato_early_blight': 'tomato/early_blight',
    'early_blight_tomato': 'tomato/early_blight',
    'tomato_late': 'tomato/late_blight',
    'tomato_late_blight': 'tomato/late_blight',
    'late_blight_tomato': 'tomato/late_blight',
    'healthy_tomato': 'tomato/healthy',
    'tomato_healthy': 'tomato/healthy',
    'corn_leaf_blight': 'maize/northern_leaf_blight',
    'maize_leaf_blight': 'maize/northern_leaf_blight',
    'northern_leaf_blight': 'maize/northern_leaf_blight',
    'corn_rust': 'maize/common_rust',
    'maize_rust': 'maize/common_rust',
    'common_rust': 'maize/common_rust',
    'healthy_corn': 'maize/healthy',
    'maize_healthy': 'maize/healthy',
    'potato_early': 'potato/early_blight',
    'potato_early_blight': 'potato/early_blight',
    'potato_late': 'potato/late_blight',
    'potato_late_blight': 'potato/late_blight',
    'healthy_potato': 'potato/healthy',
    'coffee_rust': 'coffee/leaf_rust',
    'coffee_leaf_rust': 'coffee/leaf_rust',
    'leaf_rust': 'coffee/leaf_rust',
    'wheat_rust': 'wheat/brown_rust',
    'brown_rust': 'wheat/brown_rust',
    'wheat_healthy': 'wheat/healthy',
    'teff_rust': 'teff/rust',
    'teff_healthy': 'teff/healthy',
}

def organize():
    if not os.path.exists(SOURCE):
        print(f"Source folder not found: {SOURCE}")
        return
    
    files = os.listdir(SOURCE)
    print(f"Found {len(files)} files")
    
    moved = 0
    unmatched = []
    
    for filename in files:
        if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue
        
        lower_name = filename.lower().replace('-', '_').replace(' ', '_')
        matched = False
        
        for keyword, dest in MAPPING.items():
            if keyword in lower_name:
                dest_folder = os.path.join(DEST, dest)
                os.makedirs(dest_folder, exist_ok=True)
                shutil.copy(os.path.join(SOURCE, filename), os.path.join(dest_folder, filename))
                print(f"Moved: {filename} -> {dest}")
                moved += 1
                matched = True
                break
        
        if not matched:
            unmatched.append(filename)
    
    print(f"\nMoved: {moved} images")
    if unmatched:
        print(f"\nUnmatched ({len(unmatched)} files):")
        for f in unmatched:
            print(f"  {f}")

if __name__ == '__main__':
    organize()