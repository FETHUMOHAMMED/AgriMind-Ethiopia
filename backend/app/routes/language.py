from fastapi import APIRouter
from app.languages import TRANSLATIONS

router = APIRouter(prefix="/language", tags=["language"])

@router.get("/{lang}")
async def get_translations(lang: str):
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"])