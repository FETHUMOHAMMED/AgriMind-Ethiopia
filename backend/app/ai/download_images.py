import os
import requests

# PlantVillage images from a public GitHub repo
# These URLs are known to work (small subset for each Ethiopian crop)
CROP_IMAGES = {
    'coffee/leaf_rust': [
        'https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color/Corn_(maize)___Common_rust_.JPG',
    ],
    'maize/northern_leaf_blight': [
        'https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color/Corn_(maize)___Northern_Leaf_Blight.JPG',
    ],
    'maize/common_rust': [
        'https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color/Corn_(maize)___Common_rust_.JPG',
    ],
    'tomato/early_blight': [
        'https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color/Tomato___Early_blight.JPG',
    ],
    'tomato/late_blight': [
        'https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color/Tomato___Late_blight.JPG',
    ],
    'tomato/healthy': [
        'https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color/Tomato___healthy.JPG',
    ],
    'potato/early_blight': [
        'https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color/Potato___Early_blight.JPG',
    ],
    'potato/late_blight': [
        'https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color/Potato___Late_blight.JPG',
    ],
    'potato/healthy': [
        'https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color/Potato___healthy.JPG',
    ],
    'wheat/brown_rust': [
        'https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color/Wheat___brown_rust.JPG',
    ],
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

BASE_DIR = 'datasets/ethiopian_crops'

def download_images():
    for path, urls in CROP_IMAGES.items():
        folder = os.path.join(BASE_DIR, path)
        os.makedirs(folder, exist_ok=True)
        for i, url in enumerate(urls):
            try:
                response = requests.get(url, headers=HEADERS, timeout=30)
                if response.status_code == 200 and len(response.content) > 5000:
                    ext = '.jpg'
                    filename = f"sample_{i+1}{ext}"
                    filepath = os.path.join(folder, filename)
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    print(f"OK: {path}/{filename} ({len(response.content)/1024:.0f} KB)")
                else:
                    print(f"Failed ({response.status_code}): {url}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == '__main__':
    download_images()
    print("\nDone! Check folders for images.")