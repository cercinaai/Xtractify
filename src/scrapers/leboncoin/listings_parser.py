import json
import random
import logging
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.sync_api import Page
from src.database.realStateLbc import RealStateLBCModel, save_annonce_to_db, annonce_exists
from src.utils.human_behavior import human_like_delay, human_like_scroll_to_element
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

def extract_ads_from_html(page: Page) -> list:
    """
    Extrait les annonces de la page 1 à partir du contenu HTML
    en analysant le script contenant l'objet __NEXT_DATA__.
    """
    content = page.content()
    soup = BeautifulSoup(content, "html.parser")
    script_tag = soup.find("script", id="__NEXT_DATA__")
    if not script_tag:
        logger.error("❌ Balise __NEXT_DATA__ introuvable sur la page 1.")
        return []
    try:
        data = json.loads(script_tag.string)
    except Exception as e:
        logger.error(f"❌ Erreur lors du parsing du JSON: {e}")
        return []
    ads = data.get("props", {}).get("pageProps", {}).get("searchData", {}).get("ads", [])
    return ads

def intercept_ads_from_api(page: Page, timeout=60000) -> list:
    """
    Intercepte la réponse POST de l'API (https://api.leboncoin.fr/finder/search)
    qui contient l'objet 'ads'. Seule la réponse renvoyant des données 'ads' est retournée.
    """
    try:
        with page.expect_response(
            lambda r: "api.leboncoin.fr/finder/search" in r.url and r.status == 200,
            timeout=timeout
        ) as response_info:
            # Un court délai pour laisser la requête s'exécuter
            page.wait_for_timeout(1000)
        response = response_info.value
        try:
            data = response.json()
            if "ads" in data:
                return data.get("ads", [])
            else:
                logger.error("Réponse API interceptée sans clé 'ads'.")
                return []
        except Exception as je:
            logger.error(f"Erreur lors du décodage JSON de la réponse API: {je}")
            return []
    except Exception as e:
        logger.error(f"Erreur lors de l'interception de la réponse API: {e}")
        return []

def click_pagination_link(page: Page, page_number: int) -> None:
    """
    Clique sur le lien de pagination correspondant à la page donnée.
    Basé sur l'attribut data-index présent sur le lien.
    """
    selector = f"a[data-spark-component='pagination-item'][data-index='{page_number}']"
    page_link = page.query_selector(selector)
    if not page_link:
        logger.error(f"Lien de pagination non trouvé pour la page {page_number}.")
        return
    bbox = page_link.bounding_box()
    if bbox:
        page.mouse.move(bbox["x"] + random.uniform(2, 5), bbox["y"] + random.uniform(2, 5))
    page_link.click()

def scrape_listings_via_api(page: Page):
    """
    Scrape les annonces :
      - Page 1 : extraction via le HTML (balise __NEXT_DATA__)
      - À partir de la page 2 : intercepte la réponse API de la requête POST (https://api.leboncoin.fr/finder/search)
    Chaque annonce est traitée et enregistrée en base.
    """
    global total_scraped
    current_page = 1
    max_pages = 5  # Limite du nombre de pages à scraper

    while current_page <= max_pages:
        logger.info(f"➡️ Traitement de la page {current_page}")
        # Pour la page 1, utiliser l'extraction HTML
        if current_page == 1:
            ads = extract_ads_from_html(page)
        else:
            # Cliquer sur le lien de pagination pour déclencher l'appel API
            click_pagination_link(page, current_page)
            ads = intercept_ads_from_api(page)

        # Si aucune annonce n'est trouvée, passer à la page suivante
        if not ads:
            logger.info(f"🏁 Aucune annonce trouvée sur la page {current_page}. Passage à la suivante...")
            current_page += 1
            human_like_delay(2, 3)
            continue

        for ad in ads:
            annonce_id = str(ad.get("list_id"))
            if annonce_exists(annonce_id):
                logger.info(f"⏭ Annonce {annonce_id} déjà existante.")
                continue

            raw_images = ad.get("images", {}).get("urls")
            b2_images = process_images(raw_images) if raw_images else None

            annonce_data = RealStateLBCModel(
                id=annonce_id,
                publication_date=ad.get("first_publication_date"),
                title=ad.get("subject"),
                url=ad.get("url"),
                price=(ad.get("price", [None])[0] if isinstance(ad.get("price"), list) else ad.get("price")),
                nbrImages=ad.get("images", {}).get("nb_images"),
                images=b2_images,
                typeBien=get_attr_by_label(ad, "Type de bien"),
                meuble=get_attr_by_label(ad, "Ce bien est :"),
                surface=get_attr_by_label(ad, "Surface habitable"),
                nombreDepiece=get_attr_by_label(ad, "Nombre de pièces"),
                nombreSalleEau=get_attr_by_label(ad, "Nombre de salle d'eau"),
                classeEnergie=get_attr_by_label(ad, "Classe énergie"),
                ges=get_attr_by_label(ad, "GES"),
                ascenseur=get_attr_by_label(ad, "Ascenseur"),
                etage=get_attr_by_label(ad, "Étage de votre bien"),
                nombreEtages=get_attr_by_label(ad, "Nombre d’étages dans l’immeuble"),
                exterieur=get_attr_by_label(ad, "Extérieur", default=None, get_values=True),
                charges_incluses=get_attr_by_label(ad, "Charges incluses"),
                depot_garantie=get_attr_by_label(ad, "Dépôt de garantie"),
                caracteristiques=get_attr_by_label(ad, "Caractéristiques", default=None, get_values=True),
                region=ad.get("location", {}).get("region_name"),
                city=ad.get("location", {}).get("city"),
                zipcode=ad.get("location", {}).get("zipcode"),
                agencename=ad.get("owner", {}).get("name"),
                scraped_at=datetime.utcnow()
            )
            save_annonce_to_db(annonce_data)
            total_scraped += 1
            logger.info(f"✅ Annonce enregistrée : {annonce_id} - Total extrait : {total_scraped}")

        # Scroll et délai pour simuler un comportement humain
        human_like_scroll_to_element(page, page.locator("body"), scroll_steps=random.randint(1, 3), jitter=True)
        human_like_delay(2, 3)
        logger.info(f"🌀 Fin de la page {current_page}, passage à la page suivante...")
        current_page += 1