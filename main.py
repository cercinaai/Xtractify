import asyncio
import platform

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.database.database import init_db, close_db
from loguru import logger
import uvicorn

from src.api.apis import api_router  # Import du routeur d'API

# Initialisation de l'application FastAPI
app = FastAPI(
    title="Xtractify Scraper API",
    description="API de gestion du scraping pour divers sites comme LeBonCoin",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

# Inclusion des routes API
app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    try:
        await init_db()
        logger.success("✅ Connexion à MongoDB établie avec succès")
        logger.info("🚀 Serveur disponible sur http://localhost:8000")
    except Exception as e:
        logger.critical(f"🚨 Erreur critique lors du démarrage: {str(e)}")
        raise SystemExit(1)

@app.on_event("shutdown")
async def shutdown_event():
    try:
        await close_db()
        logger.info("🔌 Connexion MongoDB fermée proprement")
    except Exception as e:
        logger.error(f"⚠️ Erreur lors de la fermeture de MongoDB: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="debug",
        reload=False  # Désactive l'auto-reload sur Windows pour éviter les problèmes de subprocess
    )
