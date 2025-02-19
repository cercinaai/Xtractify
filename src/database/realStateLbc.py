from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from pymongo import MongoClient
from loguru import logger

# 🔹 Connexion à la base de données MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client["xtracto"]
collection = db["realStateLbc"]

class RealStateLBCModel(BaseModel):
    id: str                                       # list_id
    publication_date: Optional[datetime] = None   # first_publication_date
    title: Optional[str] = None                   # subject
    url: Optional[str] = None                     # url
    price: Optional[float] = None                 # price
    nbrImages: Optional[int] = None               # images.nb_images
    images: Optional[List[str]] = None            # images.urls

    typeBien: Optional[str] = None                # attributs.value_label where key_label == "Type de bien"
    meuble: Optional[str] = None                  # attributs.value_label where key_label == "Ce bien est :"
    surface: Optional[str] = None                 # attributs.value_label where key_label == "Surface habitable"
    nombreDepiece: Optional[str] = None           # attributs.value_label where key_label == "Nombre de pièces"
    nombreSalleEau: Optional[str] = None          # attributs.value_label where key_label == "Nombre de salle d'eau"
    classeEnergie: Optional[str] = None           # attributs.value_label where key_label == "Classe énergie"
    ges: Optional[str] = None                     # attributs.value_label where key_label == "GES"
    ascenseur: Optional[str] = None               # attributs.value_label where key_label == "Ascenseur"
    etage: Optional[str] = None                   # attributs.value_label where key_label == "Étage de votre bien"
    nombreEtages: Optional[str] = None            # attributs.value_label where key_label == "Nombre d’étages dans l’immeuble"
    exterieur: Optional[List[str]] = None         # attributs.values_label where key_label == "Extérieur"
    charges_incluses: Optional[str] = None        # attributs.value_label where key_label == "Charges incluses"
    depot_garantie: Optional[str] = None          # attributs.value_label where key_label == "Dépôt de garantie"
    caracteristiques: Optional[List[str]] = None  # attributs.values_label where key_label == "Caractéristiques"

    region: Optional[str] = None                  # location.region_name
    city: Optional[str] = None                    # location.city
    zipcode: Optional[str] = None                 # location.zipcode
    agencename: Optional[str] = None              # owner.name

    scraped_at: datetime

    @validator("publication_date", pre=True, always=True)
    def parse_publication_date(cls, v):
        if not v or v == "":
            return None
        try:
            return datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return None

# ✅ Sauvegarde d'une annonce dans MongoDB
def save_annonce_to_db(annonce: RealStateLBCModel) -> bool:
    if collection.find_one({"_id": annonce.id}):
        return False
    collection.insert_one(annonce.dict(by_alias=True, exclude_none=True))
    return True

# ✅ Vérifier si une annonce existe déjà en base
def annonce_exists(annonce_id: str) -> bool:
    return collection.find_one({"_id": annonce_id}) is not None