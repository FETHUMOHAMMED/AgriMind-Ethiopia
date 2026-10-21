import io
import os
import random
import torch
import torch.nn as nn
import numpy as np
from PIL import Image
from typing import Dict
from torchvision import models, transforms

# ------------------------------
# Load trained CNN model
# ------------------------------
MODEL_AVAILABLE = False
model = None
CLASS_NAMES = []
IMG_SIZE = 128

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model", "agrimind_mobilenetv2.pth")

try:
    if os.path.exists(MODEL_PATH):
        checkpoint = torch.load(MODEL_PATH, map_location="cpu", weights_only=False)
        CLASS_NAMES = checkpoint["classes"]
        IMG_SIZE = checkpoint.get("img_size", 128)

        model = models.mobilenet_v2(weights=None)
        model.classifier[1] = nn.Linear(model.last_channel, len(CLASS_NAMES))
        model.load_state_dict(checkpoint["model_state"])
        model.eval()
        MODEL_AVAILABLE = True
        print(f"REAL CNN MODEL LOADED — {len(CLASS_NAMES)} classes (MobileNetV2)")
    else:
        print(f"Model not found at {MODEL_PATH}")
except Exception as e:
    print(f"CNN load error: {e}")

# Image preprocessing (same as training)
transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

CONFIDENCE_THRESHOLD = 0.30

# ------------------------------
# Recommendation engine
# ------------------------------
# ⚠️ REVIEW REQUIRED: All pesticide/fungicide recommendations below
# must be validated by a qualified Ethiopian agronomist before field use.
# Do not present as field-ready guidance until expert-approved.
RECOMMENDATIONS = {
    "tomato___early_blight": {
        "symptoms": "Dark brown spots with concentric rings on lower leaves.",
        "immediate": "Remove affected leaves. Apply copper-based fungicide every 7 days.",
        "prevention": "Avoid overhead irrigation. Rotate crops. Space plants for airflow.",
        "expert_help": "Consult extension expert if spots spread to upper leaves or fruit.",
    },
    "tomato___late_blight": {
        "symptoms": "Large dark blotches, white mold on underside, fruit rot.",
        "immediate": "Remove infected plants. Apply chlorothalonil or mancozeb.",
        "prevention": "Plant resistant varieties. Avoid dense planting.",
        "expert_help": "Urgent: Late blight spreads rapidly. Consult expert immediately.",
    },
    "tomato___healthy": {
        "symptoms": "No disease detected.",
        "immediate": "Continue regular care.",
        "prevention": "Monitor weekly for early signs.",
        "expert_help": "No action needed.",
    },
    "tomato___bacterial_spot": {
        "symptoms": "Small dark water-soaked spots on leaves and fruit.",
        "immediate": "Apply copper-based bactericide. Remove infected debris.",
        "prevention": "Use certified seed. Avoid working in wet fields.",
        "expert_help": "Consult if spots spread rapidly.",
    },
    "tomato___leaf_mold": {
        "symptoms": "Pale green/yellow spots on upper leaf surface, olive-green mold underneath.",
        "immediate": "Improve air circulation. Apply fungicide.",
        "prevention": "Reduce humidity. Avoid overhead watering.",
        "expert_help": "Consult if mold persists after treatment.",
    },
    "tomato___septoria_leaf_spot": {
        "symptoms": "Small circular spots with gray centers and dark borders.",
        "immediate": "Remove affected leaves. Apply chlorothalonil.",
        "prevention": "Mulch to prevent soil splash. Rotate crops.",
        "expert_help": "Consult if defoliation is severe.",
    },
    "tomato___spider_mites": {
        "symptoms": "Tiny yellow stippling on leaves, fine webbing underneath.",
        "immediate": "Apply insecticidal soap or neem oil.",
        "prevention": "Keep plants well-watered. Encourage natural predators.",
        "expert_help": "Consult if infestation persists.",
    },
    "tomato___target_spot": {
        "symptoms": "Brown spots with concentric rings and yellow halos.",
        "immediate": "Apply fungicide. Remove infected leaves.",
        "prevention": "Improve airflow. Avoid overhead watering.",
        "expert_help": "Consult if spreading.",
    },
    "tomato___mosaic_virus": {
        "symptoms": "Mottled yellow-green leaves, distorted growth.",
        "immediate": "Remove infected plants. Disinfect tools.",
        "prevention": "Use resistant varieties. Control aphids.",
        "expert_help": "Consult immediately — viral, no cure.",
    },
    "tomato___yellow_leaf_curl": {
        "symptoms": "Yellowing leaves with upward curling, stunted growth.",
        "immediate": "Remove infected plants. Control whiteflies.",
        "prevention": "Use resistant varieties. Use row covers.",
        "expert_help": "Consult immediately — viral.",
    },
    "potato___early_blight": {
        "symptoms": "Dark lesions with concentric rings on older leaves.",
        "immediate": "Apply chlorothalonil. Remove infected foliage.",
        "prevention": "Avoid overhead irrigation. Rotate crops.",
        "expert_help": "Consult if lesions appear on stems.",
    },
    "potato___late_blight": {
        "symptoms": "Dark water-soaked lesions, white mold under leaves.",
        "immediate": "Destroy infected plants. Apply metalaxyl-based fungicide.",
        "prevention": "Use certified seed tubers. Avoid wet conditions.",
        "expert_help": "Urgent: highly destructive. Expert intervention needed.",
    },
    "potato___healthy": {
        "symptoms": "No disease detected.",
        "immediate": "Continue regular care.",
        "prevention": "Monitor weekly.",
        "expert_help": "No action needed.",
    },
    "pepper___bacterial_spot": {
        "symptoms": "Water-soaked spots on leaves turning brown.",
        "immediate": "Apply copper bactericide. Remove infected plants.",
        "prevention": "Use certified seed. Avoid overhead watering.",
        "expert_help": "Consult if spreading.",
    },
    "pepper___healthy": {
        "symptoms": "No disease detected.",
        "immediate": "Continue regular care.",
        "prevention": "Monitor weekly.",
        "expert_help": "No action needed.",
    },
    "coffee___leaf_rust": {
        "symptoms": "Orange-yellow powdery spots on underside of leaves.",
        "immediate": "Apply copper-based fungicide. Prune affected branches.",
        "prevention": "Improve air circulation. Maintain shade.",
        "expert_help": "Consult if rust covers >30% of tree.",
    },
    "maize___common_rust": {
        "symptoms": "Small brown pustules on leaves, orange-brown powder.",
        "immediate": "Apply sulfur or mancozeb. Remove infected leaves.",
        "prevention": "Plant resistant varieties. Avoid excess nitrogen.",
        "expert_help": "Consult if rust spreads to upper canopy.",
    },
    "maize___northern_leaf_blight": {
        "symptoms": "Gray-green elliptical lesions on leaves.",
        "immediate": "Apply azoxystrobin. Remove crop residue after harvest.",
        "prevention": "Rotate with non-host crops. Plant resistant hybrids.",
        "expert_help": "Consult if lesions cover >50% of leaf area.",
    },
    "wheat___brown_rust": {
        "symptoms": "Brown pustules on leaves and stems.",
        "immediate": "Apply propiconazole. Remove volunteer wheat plants.",
        "prevention": "Plant resistant varieties. Avoid dense planting.",
        "expert_help": "Consult if rust spreads to flag leaf.",
    },
}

DEFAULT_REC = {
    "symptoms": "Unknown condition.",
    "immediate": "Consult an agricultural expert.",
    "prevention": "Monitor crop regularly.",
    "expert_help": "Seek expert diagnosis.",
}

def get_recommendation(name: str) -> dict:
    return RECOMMENDATIONS.get(name.lower(), DEFAULT_REC)


# ------------------------------
# Prediction function
# ------------------------------
def predict_disease(image_bytes: bytes = None) -> Dict[str, any]:
    # FIX 2a: Never fabricate a diagnosis if the model is unavailable
    if not MODEL_AVAILABLE or model is None:
        raise RuntimeError("Disease classification model is unavailable.")

    # FIX 2b: Explicit error for missing image
    if not image_bytes:
        raise ValueError("No image data was provided.")

    # FIX 3: Decode and validate the actual image bytes
    try:
        with Image.open(io.BytesIO(image_bytes)) as source:
            source.verify()
        with Image.open(io.BytesIO(image_bytes)) as source:
            image = source.convert("RGB")
    except Exception as exc:
        raise ValueError("The uploaded file is not a valid image.") from exc

    # Run model inference — fail explicitly instead of returning a fake result
    try:
        img_tensor = transform(image).unsqueeze(0)
        with torch.no_grad():
            outputs = model(img_tensor)
            probs = torch.nn.functional.softmax(outputs[0], dim=0)
            confidence, predicted_idx = torch.max(probs, 0)

        idx = int(predicted_idx.item())
        conf = float(confidence.item())

        if idx < 0 or idx >= len(CLASS_NAMES):
            raise RuntimeError("Model returned an invalid class index.")

        disease_name = CLASS_NAMES[idx]
    except Exception as exc:
        raise RuntimeError("Disease inference failed.") from exc

    # Low-confidence = valid "uncertain" result (not an error)
    if conf < CONFIDENCE_THRESHOLD:
        return {
            "name": "Unknown / Uncertain",
            "confidence": round(conf, 4),
            "recommendation": (
                "The image could not be identified confidently. "
                "Please consult an agricultural expert."
            ),
            "symptoms": "N/A",
            "prevention": "N/A",
            "expert_help": "Please consult an agricultural expert.",
        }

    rec = get_recommendation(disease_name)

    return {
        "name": disease_name,
        "confidence": round(conf, 4),
        "recommendation": rec["immediate"],
        "symptoms": rec["symptoms"],
        "prevention": rec["prevention"],
        "expert_help": rec["expert_help"],
    }