import os
import shutil
import requests
from PIL import Image
import io

# Create dataset folders
CROPS = ['teff', 'coffee', 'maize', 'tomato', 'potato', 'wheat']
DISEASES = {
    'teff': ['rust', 'healthy'],
    'coffee': ['leaf_rust', 'healthy'],
    'maize': ['northern_leaf_blight', 'common_rust', 'healthy'],
    'tomato': ['early_blight', 'late_blight', 'healthy'],
    'potato': ['early_blight', 'late_blight', 'healthy'],
    'wheat': ['brown_rust', 'healthy'],
}

BASE_DIR = 'datasets/ethiopian_crops'

def create_structure():
    for crop in CROPS:
        for disease in DISEASES[crop]:
            folder = os.path.join(BASE_DIR, crop, disease)
            os.makedirs(folder, exist_ok=True)
    print(f"Created folder structure in {BASE_DIR}")

if __name__ == '__main__':
    create_structure()