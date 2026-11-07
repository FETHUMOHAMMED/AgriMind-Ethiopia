"""Approved diagnosis taxonomy used by training-data eligibility checks."""

APPROVED_TAXONOMY_VERSION = "agrimind-field-v1"


def _normalize(value: str) -> str:
    return " ".join(value.strip().casefold().split())


# This is an explicit application taxonomy, not an assertion that every model
# class is agronomically validated. Labels outside this map are not eligible
# for training until the taxonomy is deliberately expanded and reviewed.
_APPROVED_LABELS = {
    "wheat rust": "wheat_rust",
    "wheat septoria": "wheat_septoria",
    "apple___apple_scab": "apple_apple_scab",
    "apple___black_rot": "apple_black_rot",
    "apple___cedar_apple_rust": "apple_cedar_apple_rust",
    "apple___healthy": "apple_healthy",
    "blueberry___healthy": "blueberry_healthy",
    "cherry_(including_sour)___powdery_mildew": "cherry_powdery_mildew",
    "cherry_(including_sour)___healthy": "cherry_healthy",
    "corn_(maize)___cercospora_leaf_spot gray_leaf_spot": "maize_cercospora_leaf_spot",
    "corn_(maize)___common_rust_": "maize_common_rust",
    "corn_(maize)___northern_leaf_blight": "maize_northern_leaf_blight",
    "corn_(maize)___healthy": "maize_healthy",
    "grape___black_rot": "grape_black_rot",
    "grape___esca_(black_measles)": "grape_esca",
    "grape___leaf_blight_(isariopsis_leaf_spot)": "grape_leaf_blight",
    "grape___healthy": "grape_healthy",
    "orange___haunglongbing_(citrus_greening)": "orange_haunglongbing",
    "peach___bacterial_spot": "peach_bacterial_spot",
    "peach___healthy": "peach_healthy",
    "pepper,_bell___bacterial_spot": "pepper_bacterial_spot",
    "pepper,_bell___healthy": "pepper_healthy",
    "potato___early_blight": "potato_early_blight",
    "potato___late_blight": "potato_late_blight",
    "potato___healthy": "potato_healthy",
    "raspberry___healthy": "raspberry_healthy",
    "soybean___healthy": "soybean_healthy",
    "squash___powdery_mildew": "squash_powdery_mildew",
    "strawberry___leaf_scorch": "strawberry_leaf_scorch",
    "strawberry___healthy": "strawberry_healthy",
    "tomato___bacterial_spot": "tomato_bacterial_spot",
    "tomato___early_blight": "tomato_early_blight",
    "tomato___late_blight": "tomato_late_blight",
    "tomato___leaf_mold": "tomato_leaf_mold",
    "tomato___septoria_leaf_spot": "tomato_septoria_leaf_spot",
    "tomato___spider_mites two-spotted_spider_mite": "tomato_spider_mites",
    "tomato___target_spot": "tomato_target_spot",
    "tomato___tomato_yellow_leaf_curl_virus": "tomato_yellow_leaf_curl_virus",
    "tomato___tomato_mosaic_virus": "tomato_mosaic_virus",
    "tomato___healthy": "tomato_healthy",
}


def canonical_diagnosis(
    diagnosis: str | None,
    taxonomy_version: str | None,
) -> str | None:
    if not diagnosis or taxonomy_version != APPROVED_TAXONOMY_VERSION:
        return None
    return _APPROVED_LABELS.get(_normalize(diagnosis))


def is_approved_diagnosis(diagnosis: str | None, taxonomy_version: str | None) -> bool:
    return canonical_diagnosis(diagnosis, taxonomy_version) is not None
