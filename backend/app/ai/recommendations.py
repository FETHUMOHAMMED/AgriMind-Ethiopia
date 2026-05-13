# Mapping disease name to actionable advice (English – will later translate)
RECOMMENDATIONS = {
    "Tomato___Early_blight": "Apply copper-based fungicide weekly. Remove affected leaves.",
    "Tomato___Late_blight": "Use chlorothalonil or mancozeb. Ensure good air circulation.",
    "Corn_(maize)___Common_rust_": "Apply sulfur or mancozeb. Plant resistant varieties.",
    "Corn_(maize)___Northern_Leaf_Blight": "Fungicide containing azoxystrobin. Rotate crops.",
    "Potato___Early_blight": "Apply chlorothalonil. Avoid overhead irrigation.",
    "Potato___Late_blight": "Use metalaxyl-based fungicides. Destroy infected tubers.",
    # Add common ones... for all we can default to:
    "default": "Consult an agricultural expert. Remove diseased parts and improve field hygiene."
}

def get_recommendation(disease_name: str) -> str:
    return RECOMMENDATIONS.get(disease_name, RECOMMENDATIONS["default"])