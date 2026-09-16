# AgriMind Ethiopia — Crop Disease Recommendations
# Agronomically-informed treatment guidance

RECOMMENDATIONS = {
    # Tomato
    "tomato___early_blight": {
        "symptoms": "Dark brown spots with concentric rings on lower leaves, yellowing around spots",
        "immediate": "Remove severely affected leaves. Apply copper-based fungicide every 7 days.",
        "prevention": "Avoid overhead irrigation. Rotate crops. Space plants for airflow.",
        "expert_help": "Consult extension expert if spots spread to upper leaves or fruit.",
    },
    "tomato___late_blight": {
        "symptoms": "Large dark blotches on leaves, white mold on underside, fruit rot",
        "immediate": "Remove infected plants immediately. Apply chlorothalonil or mancozeb.",
        "prevention": "Plant resistant varieties. Avoid dense planting. Dry conditions reduce spread.",
        "expert_help": "Urgent: Late blight spreads rapidly. Consult expert immediately if found.",
    },
    "tomato___healthy": {
        "symptoms": "No disease detected",
        "immediate": "Continue regular care. Maintain consistent watering.",
        "prevention": "Monitor weekly for early signs. Maintain soil health.",
        "expert_help": "No action needed.",
    },

    # Maize/Corn
    "maize___northern_leaf_blight": {
        "symptoms": "Gray-green elliptical lesions on leaves, cigar-shaped",
        "immediate": "Apply azoxystrobin or propiconazole. Remove crop residue after harvest.",
        "prevention": "Rotate with non-host crops. Plant resistant hybrids.",
        "expert_help": "Consult if lesions cover >50% of leaf area.",
    },
    "maize___common_rust": {
        "symptoms": "Small brown pustules on leaves, orange-brown powder",
        "immediate": "Apply sulfur or mancozeb. Remove infected leaves.",
        "prevention": "Plant resistant varieties. Avoid excessive nitrogen.",
        "expert_help": "Consult if rust spreads to upper canopy.",
    },
    "maize___healthy": {
        "symptoms": "No disease detected",
        "immediate": "Continue regular field monitoring.",
        "prevention": "Maintain balanced fertilization.",
        "expert_help": "No action needed.",
    },

    # Potato
    "potato___early_blight": {
        "symptoms": "Dark lesions with concentric rings, yellowing leaves",
        "immediate": "Apply chlorothalonil. Remove infected foliage.",
        "prevention": "Avoid overhead irrigation. Rotate with non-solanaceous crops.",
        "expert_help": "Consult if lesions appear on stems.",
    },
    "potato___late_blight": {
        "symptoms": "Dark water-soaked lesions, white mold under leaves",
        "immediate": "Destroy infected plants. Apply metalaxyl-based fungicide.",
        "prevention": "Use certified seed tubers. Avoid wet conditions.",
        "expert_help": "Urgent: Highly destructive disease. Expert intervention recommended.",
    },
    "potato___healthy": {
        "symptoms": "No disease detected",
        "immediate": "Continue regular care.",
        "prevention": "Monitor weekly for early blight signs.",
        "expert_help": "No action needed.",
    },

    # Coffee
    "coffee___leaf_rust": {
        "symptoms": "Orange-yellow powdery spots on underside of leaves",
        "immediate": "Apply copper-based fungicide. Prune affected branches.",
        "prevention": "Improve air circulation. Maintain shade. Plant resistant varieties.",
        "expert_help": "Consult if rust covers >30% of tree.",
    },
    "coffee___healthy": {
        "symptoms": "No disease detected",
        "immediate": "Continue regular care.",
        "prevention": "Monitor for leaf rust during wet season.",
        "expert_help": "No action needed.",
    },

    # Wheat
    "wheat___brown_rust": {
        "symptoms": "Brown pustules on leaves and stems",
        "immediate": "Apply propiconazole. Remove volunteer wheat plants.",
        "prevention": "Plant resistant varieties. Avoid dense planting.",
        "expert_help": "Consult if rust spreads to flag leaf.",
    },
    "wheat___healthy": {
        "symptoms": "No disease detected",
        "immediate": "Continue regular monitoring.",
        "prevention": "Maintain proper spacing and fertilization.",
        "expert_help": "No action needed.",
    },

    # Teff
    "teff___rust": {
        "symptoms": "Small orange-brown pustules on leaves",
        "immediate": "Use sulfur dusting. Remove infected plants.",
        "prevention": "Rotate with legumes. Avoid excessive nitrogen.",
        "expert_help": "Consult if rust appears during grain-fill stage.",
    },
    "teff___healthy": {
        "symptoms": "No disease detected",
        "immediate": "Continue regular care.",
        "prevention": "Monitor for rust during wet conditions.",
        "expert_help": "No action needed.",
    },
}

DEFAULT_RECOMMENDATION = {
    "symptoms": "Unknown condition",
    "immediate": "Consult an agricultural expert. Improve field hygiene.",
    "prevention": "Monitor the crop regularly. Maintain proper spacing and watering.",
    "expert_help": "Seek expert diagnosis for unknown symptoms.",
}

def get_recommendation(disease_name: str) -> dict:
    """Return structured recommendation for a disease."""
    disease_key = disease_name.lower()
    return RECOMMENDATIONS.get(disease_key, DEFAULT_RECOMMENDATION)