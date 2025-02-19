from motor.motor_asyncio import AsyncIOMotorClient
from src.config.settings import MONGO_URI
from loguru import logger

# Variables globales pour stocker la connexion
client = None
database = None

async def init_db():
    """Initialisation de la connexion à MongoDB."""
    global client, database
    try:
        client = AsyncIOMotorClient(MONGO_URI)
        
        # Récupérer automatiquement la base de données depuis l'URI
        database_name = MONGO_URI.split("/")[-1]  # Extraire "xtractify_db" de l'URI
        if not database_name:
            raise ValueError("❌ Aucun nom de base de données défini dans MONGO_URI")

        database = client[database_name]  # Sélection de la base de données
        logger.success(f"✅ Connexion à MongoDB réussie ({database_name})")

    except Exception as e:
        logger.critical(f"🚨 Erreur de connexion à MongoDB: {str(e)}")
        raise SystemExit(1)

async def close_db():
    """Ferme proprement la connexion à MongoDB."""
    global client
    if client:
        client.close()
        logger.info("🔌 Connexion MongoDB fermée proprement")
