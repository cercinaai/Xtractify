import json
import logging
import random
from datetime import datetime
import requests
from playwright.sync_api import Page, Response
from src.database.realStateLbc import RealStateLBCModel, save_annonce_to_db, annonce_exists
from src.utils.human_behavior import human_like_delay
from src.utils.b2_util import upload_image_to_b2

logger = logging.getLogger(__name__)
total_scraped = 0

def get_attr_by_label(ad: dict, label: str, default=None, get_values: bool = False):
    """ Extrait un attribut spécifique d'une annonce """
    for attr in ad.get("attributes", []):
        if attr.get("key_label", "").strip() == label:
            return attr.get("values_label", default) if get_values else attr.get("value_label", default)
    return default

def process_images(image_urls: list) -> list:
    """ Télécharge et stocke les images des annonces sur Backblaze B2 """
    new_urls = []
    for url in image_urls:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                filename = url.split("/")[-1].split("?")[0]
                new_url = upload_image_to_b2(response.content, filename)
                new_urls.append(new_url)
            else:
                new_urls.append(url)
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'image {url} : {e}")
            new_urls.append(url)
    return new_urls

def intercept_leboncoin_api(response):
    """ Intercepte l'API de Leboncoin et enregistre les annonces en base de données """
    global total_scraped
    if "api.leboncoin.fr/finder/search" in response.url and response.status == 200:
        try:
            data = response.json()
            if "ads" in data:
                ads = data["ads"]
                logger.info(f"✅ {len(ads)} annonces récupérées depuis l'API !")

                new_ads = 0
                for ad in ads:
                    annonce_id = str(ad.get("list_id"))
                    if annonce_exists(annonce_id):
                        continue  # Éviter les doublons

                    annonce_data = RealStateLBCModel(
                        id=annonce_id,
                        publication_date=ad.get("first_publication_date"),
                        title=ad.get("subject"),
                        url=ad.get("url"),
                        price=ad.get("price", [None])[0] if isinstance(ad.get("price"), list) else ad.get("price"),
                        nbrImages=ad.get("images", {}).get("nb_images"),
                        images=process_images(ad.get("images", {}).get("urls", [])),
                        typeBien=get_attr_by_label(ad, "Type de bien"),
                        meuble=get_attr_by_label(ad, "Ce bien est :"),
                        surface=get_attr_by_label(ad, "Surface habitable"),
                        nombreDepiece=get_attr_by_label(ad, "Nombre de pièces"),
                        nombreSalleEau=get_attr_by_label(ad, "Nombre de salle d'eau"),
                        classeEnergie=get_attr_by_label(ad, "Classe énergie"),
                        ges=get_attr_by_label(ad, "GES"),
                        ascenseur=get_attr_by_label(ad, "Ascenseur"),
                        etage=get_attr_by_label(ad, "Étage de votre bien"),
                        nombreEtages=get_attr_by_label(ad, "Nombre d'étages dans l'immeuble"),
                        exterieur=get_attr_by_label(ad, "Extérieur", get_values=True),
                        charges_incluses=get_attr_by_label(ad, "Charges incluses"),
                        depot_garantie=get_attr_by_label(ad, "Dépôt de garantie"),
                        caracteristiques=get_attr_by_label(ad, "Caractéristiques", get_values=True),
                        region=ad.get("location", {}).get("region_name"),
                        city=ad.get("location", {}).get("city"),
                        zipcode=ad.get("location", {}).get("zipcode"),
                        agencename=ad.get("owner", {}).get("name"),
                        scraped_at=datetime.utcnow()
                    )
                    
                    save_annonce_to_db(annonce_data)
                    new_ads += 1
                    total_scraped += 1

                logger.info(f"📝 {new_ads} nouvelles annonces enregistrées en base de données !")

        except json.JSONDecodeError:
            logger.error("❌ Impossible de décoder la réponse JSON de l'API Leboncoin.")

def scrape_listings_via_api(page: Page, max_pages=5):
    """ Scrape plusieurs pages via l'API en interceptant les requêtes réseau """
    global total_scraped
    page.on("response", intercept_leboncoin_api)

    for current_page in range(1, max_pages + 1):
        try:
            logger.info(f"📄 Chargement de la page {current_page}...")
            page.wait_for_timeout(random.randint(2000, 4000))  # Pause aléatoire pour éviter la détection
            if current_page > 1:
                page.goto(f"https://www.leboncoin.fr/recherche?category=10&real_estate_type=1,2&owner_type=pro?page={current_page}")
        except Exception as e:
            logger.error(f"⚠️ Erreur lors de la navigation à la page {current_page}: {e}")
            break

    logger.info(f"✅ Scraping terminé - Total d'annonces enregistrées : {total_scraped}")
