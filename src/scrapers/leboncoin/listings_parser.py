import json
import random
import logging
from datetime import datetime
import requests
from playwright.sync_api import Page, Response
from src.database.realStateLbc import RealStateLBCModel, save_annonce_to_db, annonce_exists
from src.utils.human_behavior import human_like_delay
from src.utils.b2_util import upload_image_to_b2

logger = logging.getLogger(__name__)
total_scraped = 0

def get_attr_by_label(ad: dict, label: str, default=None, get_values: bool = False):
    for attr in ad.get("attributes", []):
        if attr.get("key_label", "").strip() == label:
            if get_values:
                return attr.get("values_label", default) or default
            return attr.get("value_label", default)
    return default

def process_images(image_urls: list) -> list:
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

def intercept_api_response(page: Page, timeout=60000) -> dict:
    """Attend et intercepte la réponse API contenant les annonces pour la première page.
       Pour éviter le captcha, nous n'effectuons pas de page.reload().
    """
    def handle_response(response):
        if "api.leboncoin.fr/finder/search" in response.url and response.status == 200:
            try:
                data = response.json()
                if "ads" in data:
                    return data
            except json.JSONDecodeError:
                pass
        return None

    try:
        # Attendre que l'API soit appelée naturellement après le chargement initial de la page
        with page.expect_response(
            lambda r: "api.leboncoin.fr/finder/search" in r.url,
            timeout=timeout
        ) as response_info:
            page.wait_for_timeout(1000)  # léger délai pour laisser la page initier l'appel
        
        response = response_info.value
        data = handle_response(response)
        if not data:
            logger.error("Réponse API invalide - pas d'annonces trouvées")
            return {}
        return data
    except TimeoutError:
        logger.error(f"Timeout de {timeout}ms dépassé en attendant la réponse API")
        return {}

def handle_pagination(page: Page, current_page: int, timeout=60000) -> list:
    """Gère la pagination et retourne les nouvelles annonces via l'API pour la page suivante.
       Pour la page 2 (et suivantes), il clique directement sur le lien de pagination.
    """
    try:
        # Sélection du lien de la page voulue
        selector = f"a[data-spark-component='pagination-item'][data-index='{current_page}']"
        page_link = page.query_selector(selector)
        if not page_link:
            logger.info("Lien de pagination non trouvé pour la page {0}".format(current_page))
            return []
        
        # Attendre que la page actuelle soit complètement chargée
        # page.wait_for_load_state("networkidle")
        
        # Optionnel : réalisez un déplacement de la souris pour simuler un comportement humain
        bbox = page_link.bounding_box()
        if bbox:
            page.mouse.move(bbox["x"] + random.uniform(2, 5), bbox["y"] + random.uniform(2, 5))
        
        with page.expect_response(
            lambda r: "api.leboncoin.fr/finder/search" in r.url and r.status == 200,
            timeout=timeout
        ) as response_info:
            page_link.click()
        
        response = response_info.value
        try:
            data = response.json()
            return data.get("ads", [])
        except json.JSONDecodeError:
            logger.error("Erreur lors du décodage de la réponse JSON pour la page {0}".format(current_page))
            return []
    
    except Exception as e:
        logger.error(f"Erreur de pagination pour la page {current_page}: {e}")
        return []

def scrape_listings_from_page2(page: Page):
    """Démarre le scraping directement sur la page suivante (page 2) en interceptant l'API."""
    global total_scraped
    current_page = 2  # On commence directement à la page 2
    max_pages = 3
    max_retries = 3

    while current_page <= max_pages:
        retries = 0
        while retries < max_retries:
            try:
                logger.info(f"Interception de l'API pour la page {current_page}...")
                # Utilisation de la fonction handle_pagination pour cliquer sur « Page suivante » et intercepter la réponse API
                ads = handle_pagination(page, current_page)
                
                if not ads:
                    logger.info("Aucune annonce trouvée - tentative de réessai")
                    retries += 1
                    human_like_delay(5, 10)
                    continue

                new_ads = 0
                for ad in ads:
                    annonce_id = str(ad.get("list_id"))
                    if annonce_exists(annonce_id):
                        continue

                    annonce_data = RealStateLBCModel(
                        id=annonce_id,
                        publication_date=ad.get("first_publication_date"),
                        title=ad.get("subject"),
                        url=ad.get("url"),
                        price=ad.get("price", [None])[0] if isinstance(ad.get("price"), list) else ad.get("price"),
                        nbrImages=ad.get("images", {}).get("nb_images"),
                        images=ad.get("images", {}).get("urls"),
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

                logger.info(f"Page {current_page} traitée - {new_ads} nouvelles annonces")
                current_page += 1
                human_like_delay(2, 4)
                break  # Succès, on sort de la boucle de tentatives

            except Exception as e:
                logger.error(f"Erreur lors du traitement de la page {current_page}: {e}")
                retries += 1
                human_like_delay(5, 10)

        if retries == max_retries:
            logger.error(f"Échec après {max_retries} tentatives pour la page {current_page}")
            break

    logger.info(f"Scraping terminé - Total d'annonces: {total_scraped}")