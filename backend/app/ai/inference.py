import torch
from torchvision import transforms, models
from PIL import Image
import io
import os

# Paths
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model", "plant_model.pth")
CLASSES_PATH = os.path.join(os.path.dirname(__file__), "model", "classes.txt")

# Load class names
with open(CLASSES_PATH, "r") as f:
    CLASS_NAMES = [line.strip() for line in f.readlines()]

# Load model once (cached)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = models.mobilenet_v2(weights=None)
num_classes = len(CLASS_NAMES)
model.classifier[1] = torch.nn.Linear(model.last_channel, num_classes)
model.load_state_dict(torch.load(MODEL_PATH, map_location=device, weights_only=False))
model.to(device)
model.eval()

# Image preprocessing (same as training)
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

def predict_disease(image_bytes: bytes):
    """Return predicted disease name and confidence."""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image_tensor = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(image_tensor)
        probabilities = torch.nn.functional.softmax(outputs, dim=1)
        confidence, predicted_idx = torch.max(probabilities, 1)

    disease_name = CLASS_NAMES[predicted_idx.item()]
    confidence_value = confidence.item()
    return disease_name, confidence_value