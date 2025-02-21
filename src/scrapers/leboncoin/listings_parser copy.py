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
    """
    Recherche dans ad["attributes"] un attribut dont key_label correspond exactement à label.
    Renvoie value_label ou values_label (si get_values est True) sinon default.
    """
    for attr in ad.get("attributes", []):
        if attr.get("key_label", "").strip() == label:
            if get_values:
                return attr.get("values_label", default) or default
            return attr.get("value_label", default)
    return default

def process_images(image_urls: list) -> list:
    """
    Télécharge les images de image_urls, les upload vers S3 et retourne la liste des nouvelles URL.
    """
    new_urls = []
    for url in image_urls:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                # Utilisez le nom de fichier extrait depuis l'URL (sans query params)
                filename = url.split("/")[-1].split("?")[0]
                new_url = upload_image_to_b2(response.content, filename)
                new_urls.append(new_url)
            else:
                # Si téléchargement échoue, conserver l'URL d'origine
                new_urls.append(url)
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'image {url} : {e}")
            new_urls.append(url)
    return new_urls

def scrape_listings_via_api(page: Page):
    """
    Scrape les annonces en se basant sur l'objet ads et enregistre chaque annonce dans la base.
    Télécharge les images et les upload sur Backblaze S3.
    """
    current_page = 1
    global total_scraped

    while True:
        url = f"https://www.leboncoin.fr/recherche?category=10&real_estate_type=1,2&owner_type=pro&page={current_page}"
        logger.info(f"➡️ Chargement de la page : {current_page}")
        page.goto(url, timeout=60000)
        human_like_delay(2, 3)

        # Vérification du captcha
        if page.locator('iframe[title="DataDome CAPTCHA"]').is_visible(timeout=5000):
            logger.warning("⚠️ CAPTCHA détecté. Fermeture du navigateur et relance de open_leboncoin()...")
            page.context.browser.close()
            from src.scrapers.leboncoin.location_scraper import open_leboncoin
            open_leboncoin()
            return
        
        content = page.content()
        soup = BeautifulSoup(content, "html.parser")
        script_tag = soup.find("script", id="__NEXT_DATA__")
        if not script_tag:
            logger.error("❌ Balise __NEXT_DATA__ introuvable.")
            break

        try:
            data = json.loads(script_tag.string)
        except Exception as e:
            logger.error(f"❌ Erreur lors du parsing du JSON: {e}")
            break

        ads = data.get("props", {}).get("pageProps", {}).get("searchData", {}).get("ads", [])
        if not ads:
            logger.info("🏁 Aucune annonce retournée, fin du scraping.")
            break

        for ad in ads:
            annonce_id = str(ad.get("list_id"))
            if annonce_exists(annonce_id):
                logger.info(f"⏭ Annonce {annonce_id} déjà existante.")
                continue

            # Traitement des images : upload sur S3 et récupérer les nouvelles URL.
            raw_images = ad.get("images", {}).get("urls", [])
            bucketed_images = [upload_image_to_b2(url, "real_estate") for url in raw_images]

            annonce_data = RealStateLBCModel(
                 id=annonce_id,
                publication_date=ad.get("first_publication_date"),
                index_date=ad.get("index_date"),
                expiration_date=ad.get("expiration_date"),
                status=ad.get("status"),
                ad_type=ad.get("ad_type"),
                title=ad.get("subject"),
                description=ad.get("body"),
                descrip=ad.get("body"),
                url=ad.get("url"),
                category_id=ad.get("category_id"),
                category_name=ad.get("category_name"),
                price=(ad.get("price", [None])[0] if isinstance(ad.get("price"), list) else ad.get("price")),
                nbrImages=ad.get("images", {}).get("nb_images"),
                images=bucketed_images,
                typeBien=get_attr_by_label(ad, "Type de bien"),
                meuble=get_attr_by_label(ad, "Ce bien est :"),
                surface=get_attr_by_label(ad, "Surface habitable"),
                nombreDepiece=get_attr_by_label(ad, "Nombre de pièces"),
                nombreChambres=get_attr_by_label(ad, "Nombre de chambres"),
                nombreSalleEau=get_attr_by_label(ad, "Nombre de salle d'eau"),
                nb_salles_de_bain=get_attr_by_label(ad, "Nombre de salle de bain"),
                nb_parkings=get_attr_by_label(ad, "Places de parking"),
                nb_niveaux=get_attr_by_label(ad, "Nombre de niveaux"),
                disponibilite=get_attr_by_label(ad, "Disponible à partir de"),
                annee_construction=get_attr_by_label(ad, "Année de construction"),
                classeEnergie=get_attr_by_label(ad, "Classe énergie"),
                ges=get_attr_by_label(ad, "GES"),
                ascenseur=get_attr_by_label(ad, "Ascenseur"),
                etage=get_attr_by_label(ad, "Étage de votre bien"),
                nombreEtages=get_attr_by_label(ad, "Nombre d’étages dans l’immeuble"),
                exterieur=get_attr_by_label(ad, "Extérieur", get_values=True),
                charges_incluses=get_attr_by_label(ad, "Charges incluses"),
                depot_garantie=get_attr_by_label(ad, "Dépôt de garantie"),
                loyer_mensuel_charges=get_attr_by_label(ad, "Charges locatives"),
                caracteristiques=get_attr_by_label(ad, "Caractéristiques", get_values=True),
                region=ad.get("location", {}).get("region_name"),
                city=ad.get("location", {}).get("city"),
                zipcode=ad.get("location", {}).get("zipcode"),
                departement=ad.get("location", {}).get("department_name"),
                latitude=ad.get("location", {}).get("lat"),
                longitude=ad.get("location", {}).get("lng"),
                region_id=ad.get("location", {}).get("region_id"),
                departement_id=ad.get("location", {}).get("department_id"),
                agencename=ad.get("owner", {}).get("name"),
                scraped_at=datetime.utcnow()
            )

            save_annonce_to_db(annonce_data)
            total_scraped += 1
            logger.info(f"✅ Annonce enregistrée : {annonce_id} - Total extrait : {total_scraped}")

        human_like_scroll_to_element(page, page.locator("body"), scroll_steps=random.randint(1, 3), jitter=True)
        human_like_delay(2, 3)
        logger.info(f"🌀 Fin de la page {current_page}, passage à la page suivante...")
        current_page += 1