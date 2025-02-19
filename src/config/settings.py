import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv("src/environment/local.env")

# Vérifier si la variable MONGO_URI est bien définie
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("❌ MONGO_URI n'est pas défini dans src/environment/local.env")
