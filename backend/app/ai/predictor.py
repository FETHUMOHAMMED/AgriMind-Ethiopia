import random

diseases = [
    {
        "name": "Tomato Early Blight",
        "confidence": 0.94,
        "recommendation": "Apply copper fungicide every 7 days. Remove affected leaves."
    },
    {
        "name": "Tomato Late Blight",
        "confidence": 0.91,
        "recommendation": "Remove infected leaves immediately. Use chlorothalonil."
    },
    {
        "name": "Maize Northern Leaf Blight",
        "confidence": 0.89,
        "recommendation": "Apply azoxystrobin. Rotate with non-host crops."
    },
    {
        "name": "Coffee Leaf Rust",
        "confidence": 0.92,
        "recommendation": "Spray copper-based fungicide. Improve air circulation."
    },
    {
        "name": "Healthy Plant",
        "confidence": 0.99,
        "recommendation": "No disease detected. Continue regular care."
    }
]

def predict_disease(image_bytes=None):
    # image_bytes is accepted but not used yet; compatile with future real AI
    return random.choice(diseases)