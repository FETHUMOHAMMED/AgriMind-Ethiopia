import os
import numpy as np
from PIL import Image
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pickle

BASE_DIR = 'datasets/ethiopian_crops'
IMG_SIZE = (64, 64)

def load_dataset():
    X, y, classes = [], [], []
    
    for crop in sorted(os.listdir(BASE_DIR)):
        crop_dir = os.path.join(BASE_DIR, crop)
        if not os.path.isdir(crop_dir):
            continue
        for disease in sorted(os.listdir(crop_dir)):
            disease_dir = os.path.join(crop_dir, disease)
            if not os.path.isdir(disease_dir):
                continue
            class_name = f"{crop}___{disease}"
            if class_name not in classes:
                classes.append(class_name)
            
            for img_file in os.listdir(disease_dir):
                if img_file.lower().endswith(('.jpg', '.jpeg', '.png', '.jfif', '.webp')):
                    img_path = os.path.join(disease_dir, img_file)
                    try:
                        img = Image.open(img_path).convert('RGB')
                        img = img.resize(IMG_SIZE)
                        X.append(np.array(img).flatten())
                        y.append(classes.index(class_name))
                    except Exception as e:
                        print(f"Error loading {img_path}: {e}")
    
    return np.array(X), np.array(y), classes

def train():
    print("Loading dataset...")
    X, y, classes = load_dataset()
    
    if len(X) < 10:
        print(f"Not enough images ({len(X)} found). Need at least 10.")
        return
    
    print(f"Dataset: {len(X)} images, {len(classes)} classes")
    
    # Print class distribution
    unique, counts = np.unique(y, return_counts=True)
    for cls_idx, count in zip(unique, counts):
        print(f"  {classes[cls_idx]}: {count} images")
    
    # Train on all data (since we have limited samples)
    print("\nTraining Random Forest on all data...")
    model = RandomForestClassifier(n_estimators=100, max_depth=20, random_state=42)
    model.fit(X, y)
    
    # Training accuracy
    train_acc = model.score(X, y)
    print(f"Training accuracy: {train_acc:.2%}")
    print("(Note: Limited data means accuracy may be high but not generalize well)")
    
    # Save model
    model_path = os.path.join('model', 'ethiopian_crop_model.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump({'model': model, 'classes': classes}, f)
    print(f"\nModel saved to {model_path}")
    
    return model, classes

if __name__ == '__main__':
    train()