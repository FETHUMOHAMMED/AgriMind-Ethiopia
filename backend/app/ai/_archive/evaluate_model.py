import os
import numpy as np
from PIL import Image
from sklearn.metrics import classification_report, confusion_matrix
import pickle

MODEL_PATH = 'model/ethiopian_crop_model.pkl'
DATA_DIR = 'datasets/ethiopian_crops'
IMG_SIZE = (64, 64)

def load_and_evaluate():
    # Load model
    with open(MODEL_PATH, 'rb') as f:
        data = pickle.load(f)
    model = data['model']
    all_classes = data['classes']
    
    print(f"Model has {len(all_classes)} total classes")
    print()
    
    # Load images and track which classes have data
    X, y_true = [], []
    active_classes = []
    active_indices = []
    
    for cls_idx, cls in enumerate(all_classes):
        # Convert class name like 'coffee___leaf_rust' to folder path 'coffee/leaf_rust'
        parts = cls.split('___')
        if len(parts) == 2:
            cls_dir = os.path.join(DATA_DIR, parts[0], parts[1])
        else:
            cls_dir = os.path.join(DATA_DIR, cls)
        
        if not os.path.exists(cls_dir):
            continue
        
        images_found = 0
        for img_file in os.listdir(cls_dir):
            if img_file.lower().endswith(('.jpg', '.jpeg', '.png', '.jfif')):
                img_path = os.path.join(cls_dir, img_file)
                try:
                    img = Image.open(img_path).convert('RGB')
                    img = img.resize(IMG_SIZE)
                    X.append(np.array(img).flatten())
                    y_true.append(cls_idx)
                    images_found += 1
                except:
                    pass
        
        if images_found > 0:
            active_classes.append(cls)
            active_indices.append(cls_idx)
            print(f"  {cls}: {images_found} images")
    
    if len(X) == 0:
        print("No images found!")
        return
    
    X = np.array(X)
    y_true = np.array(y_true)
    
    print(f"\nEvaluating on {len(X)} images across {len(active_classes)} classes")
    print()
    
    # Predict
    y_pred = model.predict(X)
    probabilities = model.predict_proba(X)
    
    # Get confidence for predicted class
    confidences = np.max(probabilities, axis=1)
    
    # Overall accuracy (on training data — honest note needed)
    accuracy = np.mean(y_pred == y_true)
    print(f"Training Accuracy: {accuracy:.2%}")
    print(f"Average Confidence: {confidences.mean():.2%}")
    print()
    print("NOTE: This is training-set accuracy, not field validation accuracy.")
    print("With only 31 images, this number is misleading — do NOT cite as field performance.")
    print()
    
    # Per-class results
    print("Per-Class Results:")
    for cls_idx, cls in zip(active_indices, active_classes):
        mask = y_true == cls_idx
        if mask.sum() > 0:
            cls_acc = np.mean(y_pred[mask] == y_true[mask])
            cls_conf = confidences[mask].mean()
            print(f"  {cls}: accuracy={cls_acc:.0%}, avg_conf={cls_conf:.1%}")

if __name__ == '__main__':
    load_and_evaluate()