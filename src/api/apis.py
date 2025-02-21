from fastapi import APIRouter, HTTPException
from src.scrapers.leboncoin.location_scraper import access_leboncoin
from loguru import logger

api_router = APIRouter()

@api_router.get("/scrape/leboncoin")
async def scrape_leboncoin():
    """API pour ouvrir Leboncoin avec Playwright et IP Royal."""
    try:
        result = access_leboncoin()  # ✅ Lancement continu en arrière-plan
        print(f"🔍 DEBUG API: {result}")  
        return result
    except Exception as e:
        logger.error(f"⚠️ Erreur lors du scraping : {e}")
        raise HTTPException(status_code=500, detail="Erreur lors du scraping")