import logging
from playwright.sync_api import Page, TimeoutError
from src.utils.human_behavior import human_like_click_search, human_like_scroll_to_element, human_like_delay
from src.database.realStateLbc import annonce_exists, save_annonce_to_db
from src.database.realStateLbc import RealStateLBCModel
from src.utils.b2_util import upload_image_to_b2
from datetime import datetime

logger = logging.getLogger(__name__)

TARGET_API_URL = "https://api.leboncoin.fr/finder/search"
total_scraped = 0

def get_attr_by_label(ad: dict, label: str, default=None, get_values: bool = False):
    """Recherche dans ad["attributes"] un attribut dont key_label correspond à label."""
    for attr in ad.get("attributes", []):
        if attr.get("key_label", "").strip() == label:
            if get_values:
                return attr.get("values_label", default) or default
            return attr.get("value_label", default)
    return default

def wait_for_api_response(page: Page, context: str, timeout: int = 70000) -> dict | None:
    """Attend et retourne la dernière réponse API contenant 'ads' en écoutant toutes les requêtes."""
    last_valid_response = None
    elapsed_time = 0
    interval = 1000  # Vérifier toutes les secondes

    def on_response(response):
        nonlocal last_valid_response
        if response.url.startswith(TARGET_API_URL) and response.status == 200:
            try:
                json_response = response.json()
                if "ads" in json_response and json_response["ads"]:
                    last_valid_response = json_response
                    logger.info(f"📡 {context}: API interceptée avec {len(json_response['ads'])} annonces : {response.url}")
            except Exception as e:
                logger.debug(f"⚠️ {context}: Erreur dans {response.url}: {e}")

    logger.debug(f"🔍 {context}: Début de l'écoute des réponses réseau...")
    page.on("response", on_response)
    
    # Attendre jusqu'à ce qu'une réponse valide soit trouvée ou que le timeout soit atteint
    while elapsed_time < timeout:
        if last_valid_response:
            page.remove_listener("response", on_response)
            logger.debug(f"🔍 {context}: Réponse valide trouvée, arrêt immédiat : {last_valid_response}")
            return last_valid_response
        page.wait_for_timeout(interval)
        elapsed_time += interval
    
    logger.debug(f"🔍 {context}: Fin de l'écoute sans réponse valide après {timeout/1000} secondes.")
    logger.warning(f"⚠️ {context}: Aucune réponse valide avec 'ads' après {timeout/1000} secondes.")
    page.remove_listener("response", on_response)
    return None

def process_ad(ad: dict) -> None:
    """Traite une annonce et l'enregistre dans la base de données."""
    global total_scraped
    annonce_id = str(ad.get("list_id"))
    if annonce_exists(annonce_id):
        logger.info(f"⏭ Annonce {annonce_id} déjà existante dans la base.")
        return

    logger.debug(f"📋 Traitement de l'annonce {annonce_id}...")
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

    try:
        save_annonce_to_db(annonce_data)
        total_scraped += 1
        logger.info(f"✅ Annonce enregistrée : {annonce_id} - Total extrait : {total_scraped}")
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'enregistrement de {annonce_id} : {e}")

def reload_filters_and_search(page: Page):
    """Décocher puis recocher 'Maison' et cliquer sur 'Rechercher' pour forcer une nouvelle requête API."""
    try:
        logger.info("🔄 Rechargement des filtres pour forcer l'API...")
        FILTRES_BTN = 'button[title="Afficher tous les filtres"]'
        PRO_CHECKBOX = 'button[role="checkbox"][value="pro"]'
        SEARCH_BTN = 'button[aria-label="Rechercher"]:visible'

        # Ouvrir le dropdown des filtres
        logger.info("🖱️ Clic sur 'Afficher tous les filtres'...")
        filter_button = page.locator(FILTRES_BTN)
        filter_button.wait_for(timeout=60000)
        human_like_click_search(page, FILTRES_BTN, click_delay=0.7, move_cursor=True)
        human_like_delay(1, 2)

        # Décocher "Pro"
        logger.info("📜 Décochage du filtre 'Pro'...")
        maison_button = page.locator(PRO_CHECKBOX)
        maison_button.wait_for(state="visible", timeout=10000)
        human_like_scroll_to_element(page, maison_button, scroll_steps=4, jitter=True)
        maison_button.click()  # Premier clic pour décocher
        human_like_delay(1, 2)

        # Recocher "Maison"
        logger.info("📜 Recochage du filtre 'Maison'...")
        maison_button = page.locator('button[role="checkbox"][value="pro"]')
        maison_button.wait_for(state="visible", timeout=10000)
        human_like_click_search(page, 'button[role="checkbox"][value="pro"]', click_delay=0.5, move_cursor=True)
        human_like_delay(1, 2)

        # Cliquer sur "Rechercher"
        logger.info("🔄 Clic sur 'Rechercher' pour recharger l'API...")
        search_button = page.locator(SEARCH_BTN)
        search_button.wait_for(timeout=60000)
        human_like_click_search(page, SEARCH_BTN, click_delay=0.5, move_cursor=True)
        human_like_delay(2, 4)

        return True
    except Exception as e:
        logger.error(f"❌ Erreur lors du rechargement des filtres : {e}")
        return False

def scrape_listings_via_api(page: Page) -> None:
    """Scrape les annonces des pages 1 à 5 en interceptant l'API."""
    global total_scraped
    current_page = 1
    MAX_PAGES = 5
    MAX_RETRIES = 3

    # Attendre le bouton "Rechercher"
    try:
        expect_search = page.locator('button[aria-label="Rechercher"]:visible')
        expect_search.wait_for(timeout=60000)
    except TimeoutError:
        logger.error("❌ Bouton 'Rechercher' non trouvé.")
        return

    # Page 1 : Utiliser l'API
    logger.info("🔄 Clic sur 'Rechercher' pour charger la page 1...")
    human_like_click_search(page, 'button[aria-label="Rechercher"]:visible', move_cursor=True, click_delay=0.5)
    response = wait_for_api_response(page, "Page 1", timeout=70000)

    if response and "ads" in response and response["ads"]:
        logger.info(f"✅ Page 1: {len(response['ads'])} annonces interceptées via API.")
        for ad in response["ads"]:
            process_ad(ad)
    else:
        logger.warning("⚠️ Page 1: Aucune réponse avec annonces via API. Rechargement des filtres...")
        if reload_filters_and_search(page):
            response = wait_for_api_response(page, "Page 1 (après rechargement)", timeout=70000)
            if response and "ads" in response and response["ads"]:
                logger.info(f"✅ Page 1: {len(response['ads'])} annonces interceptées via API après rechargement.")
                for ad in response["ads"]:
                    process_ad(ad)
            else:
                logger.error("❌ Échec du scraping de la page 1 même après rechargement.")
                return
        else:
            logger.error("❌ Échec du rechargement des filtres pour la page 1.")
            return

    # Pagination : Pages 2 à 5
    while current_page < MAX_PAGES:
        retries = 0
        next_button = page.locator('a[aria-label="Page suivante"]')
        if not next_button.is_visible(timeout=5000):
            logger.info(f"🏁 Fin de la pagination à la page {current_page}.")
            break

        while retries < MAX_RETRIES:
            logger.info(f"🌀 Passage à la page {current_page + 1} (Tentative {retries + 1}/{MAX_RETRIES})...")
            try:
                human_like_scroll_to_element(page, next_button, scroll_steps=2, jitter=True)
                human_like_click_search(page, 'a[aria-label="Page suivante"]', move_cursor=True, click_delay=0.5)
                response = wait_for_api_response(page, f"Page {current_page + 1}", timeout=70000)

                if response and "ads" in response and response["ads"]:
                    logger.info(f"✅ Page {current_page + 1}: {len(response['ads'])} annonces interceptées via API.")
                    for ad in response["ads"]:
                        process_ad(ad)
                    break
                else:
                    logger.warning(f"⚠️ Page {current_page + 1}: Aucune réponse avec annonces via API. Rechargement des filtres...")
                    if reload_filters_and_search(page):
                        response = wait_for_api_response(page, f"Page {current_page + 1} (après rechargement)", timeout=70000)
                        if response and "ads" in response and response["ads"]:
                            logger.info(f"✅ Page {current_page + 1}: {len(response['ads'])} annonces interceptées via API après rechargement.")
                            for ad in response["ads"]:
                                process_ad(ad)
                            break
                        else:
                            logger.warning(f"⚠️ Échec après rechargement, nouvelle tentative...")
                            retries += 1
                            human_like_delay(1, 3)
                    else:
                        logger.error(f"❌ Échec du rechargement des filtres pour la page {current_page + 1}.")
                        retries += 1
                        human_like_delay(1, 3)
            except Exception as e:
                logger.error(f"⚠️ Erreur lors de la navigation vers page {current_page + 1}: {e}")
                retries += 1
                human_like_delay(1, 3)

        if retries >= MAX_RETRIES:
            logger.error(f"❌ Page {current_page + 1}: Échec après {MAX_RETRIES} tentatives, arrêt.")
            break

        current_page += 1
        human_like_delay(2, 4)

    logger.info(f"🏁 Scraping terminé - Total annonces extraites : {total_scraped}")
