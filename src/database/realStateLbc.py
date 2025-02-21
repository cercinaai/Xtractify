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
    index_date: Optional[datetime] = None         # index_date (date d'indexation)
    expiration_date: Optional[datetime] = None    # expiration_date (date d'expiration)
    status: Optional[str] = None                  # status (statut de l'annonce)
    ad_type: Optional[str] = None                 # ad_type (type d'annonce : offer/demand)
    title: Optional[str] = None  
    description: Optional[str] = None             # subject
    body: Optional[str] = Field(None, max_length=100000)  # ✅ Permet de stocker de très longues chaînes
    url: Optional[str] = None                     # url
    category_id: Optional[str] = None             # category_id
    category_name: Optional[str] = None           # category_name
    price: Optional[float] = None                 # price

    nbrImages: Optional[int] = None               # images.nb_images
    images: Optional[List[str]] = None            # images.urls

    # 🔹 Caractéristiques du bien immobilier
    typeBien: Optional[str] = None                # Type de bien
    meuble: Optional[str] = None                  # Ce bien est :
    surface: Optional[str] = None                 # Surface habitable
    nombreDepiece: Optional[str] = None           # Nombre de pièces
    nombreChambres: Optional[str] = None          # Nombre de chambres
    nombreSalleEau: Optional[str] = None          # Nombre de salle d'eau
    nb_salles_de_bain: Optional[str] = None       # Nombre de salle de bain
    nb_parkings: Optional[str] = None             # Places de parking
    nb_niveaux: Optional[str] = None              # Nombre de niveaux dans une maison
    disponibilite: Optional[str] = None           # Disponible à partir de
    annee_construction: Optional[str] = None      # Année de construction

    # 🔹 Performances énergétiques
    classeEnergie: Optional[str] = None           # Classe énergie
    ges: Optional[str] = None                     # GES

    # 🔹 Informations sur l'immeuble
    ascenseur: Optional[str] = None               # Ascenseur
    etage: Optional[str] = None                   # Étage de votre bien
    nombreEtages: Optional[str] = None            # Nombre d’étages dans l’immeuble

    # 🔹 Commodités et charges
    exterieur: Optional[List[str]] = None         # Extérieur (Balcon, Terrasse, etc.)
    charges_incluses: Optional[str] = None        # Charges incluses
    depot_garantie: Optional[str] = None          # Dépôt de garantie
    loyer_mensuel_charges: Optional[str] = None   # Charges locatives
    caracteristiques: Optional[List[str]] = None  # Caractéristiques spécifiques

    # 🔹 Localisation
    region: Optional[str] = None                  # location.region_name
    city: Optional[str] = None                    # location.city
    zipcode: Optional[str] = None                 # location.zipcode
    departement: Optional[str] = None             # location.department_name
    latitude: Optional[float] = None              # location.lat
    longitude: Optional[float] = None             # location.lng
    region_id: Optional[str] = None               # location.region_id
    departement_id: Optional[str] = None          # location.department_id

    # 🔹 Informations sur l'agence
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
    # Vérifier si l'annonce existe déjà via son ID
    if collection.find_one({"id": annonce.id}):  
        logger.info(f"⏭ Annonce {annonce.id} déjà existante en base.")
        return False
    
    # Insérer l'annonce avec `id` comme `_id` pour éviter les doublons
    annonce_dict = annonce.dict(by_alias=True, exclude_none=True)
    annonce_dict["_id"] = annonce_dict["id"]  # ✅ Définir `_id` comme étant l'ID de l'annonce
    
    collection.insert_one(annonce_dict)
    return True


# ✅ Vérifier si une annonce existe déjà en base
def annonce_exists(annonce_id: str) -> bool:
    return collection.find_one({"id": annonce_id}) is not None  # ✅ Recherche sur `id`
