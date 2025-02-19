import logging
import random
import time
from urllib.parse import urlparse
from playwright.sync_api import Page, TimeoutError, expect
from src.utils.human_behavior import (
    human_like_click, 
    human_like_delay,
    human_like_scroll_to_element
)
from src.scrapers.leboncoin.annonce_details import scrape_annonce_details
from src.database.realStateLbc import annonce_exists

logger = logging.getLogger(__name__)

# Compteur global d'annonces extraites
total_scraped = 0
# Compteur global de pages parcourues
page_counter = 1

def load_all_listings(page: Page, container_selector: str, scroll_pause: float = 2.0, max_attempts: int = 10):
    """
    Effectue un scroll progressif pour charger toutes les annonces visibles sur la page.
    """
    last_count = 0
    attempts = 0
    while attempts < max_attempts:
        page.wait_for_timeout(scroll_pause * 1000)
        current_count = len(page.locator(container_selector).all())
        if current_count == last_count:
            break
        last_count = current_count
        # Scroll sur le dernier élément pour déclencher le chargement de nouveaux listings
        last_element = page.locator(container_selector).last
        human_like_scroll_to_element(page, last_element, scroll_steps=random.randint(3, 5), jitter=True)
        attempts += 1
    logger.info(f"⏳ Nombre total d'annonces chargées sur la page : {last_count}")

def collect_listing_ids(page: Page):
    """
    Récupère la liste des IDs d'annonces depuis la page actuelle.
    """
    LISTING_CONTAINER = 'li.styles_adCard__klAb3:not(.styles_ad__UbObc)'
    ANCHOR_SELECTOR = 'a[href^="/ad/locations/"]'
    
    load_all_listings(page, LISTING_CONTAINER, scroll_pause=2, max_attempts=15)
    page.wait_for_selector(LISTING_CONTAINER, state="visible", timeout=15000)
    containers = page.locator(LISTING_CONTAINER).all()
    
    annonce_ids = []
    for container in containers:
        link = container.locator(ANCHOR_SELECTOR)
        if link.count() == 0:
            continue
        href = link.get_attribute('href')
        annonce_id = urlparse(href).path.split("/")[-1]
        if not annonce_exists(annonce_id):
            annonce_ids.append(annonce_id)
        else:
            logger.info(f"⏭ Annonce {annonce_id} déjà existante, ignorée.")
    logger.info(f"⏳ {len(annonce_ids)} annonces à traiter sur la page.")
    return annonce_ids

def process_listing_by_id(main_page: Page, annonce_id: str):
    url = f"https://www.leboncoin.fr/ad/locations/{annonce_id}"
    try:
        logger.info(f"➡️ Ouverture d'un nouvel onglet pour l'annonce {annonce_id}")
        new_page = main_page.context.new_page()  # Crée un nouvel onglet
        new_page.goto(url, timeout=60000)
        human_like_delay(2, 4)
        details = scrape_annonce_details(new_page, url)
        if details is None:
            logger.error(f"🚨 Échec du scraping de l'annonce {annonce_id}")
        else:
            global total_scraped
            total_scraped += 1
            logger.info(f"✅ Annonce traitée. Total extrait: {total_scraped}")
        new_page.close()  # Ferme l'onglet de l'annonce après traitement
        # Petit scroll sur la page de listings pour simuler un comportement humain
        human_like_scroll_to_element(main_page, main_page.locator("body"), scroll_steps=random.randint(1, 2), jitter=True)
    except Exception as e:
        logger.error(f"⏰ Erreur lors de l'ouverture de l'annonce {annonce_id}: {e}")
        
def process_all_listings(page: Page):
    """Traite toutes les annonces de la page actuelle en naviguant manuellement par ID."""
    annonce_ids = collect_listing_ids(page)
    for idx, annonce_id in enumerate(annonce_ids, start=1):
        if total_scraped >= 100:
            logger.info("🏁 100 annonces traitées, arrêt du scraping.")
            return
        logger.info(f"🔍 Traitement de l'annonce {idx}/{len(annonce_ids)} – ID : {annonce_id}")
        process_listing_by_id(page, annonce_id)
        # Optionnel : revenir à la page de listings pour continuer
        # Vous pouvez rediriger vers l'URL de la page actuelle si nécessaire
        human_like_delay(2, 3)

def handle_pagination(page: Page) -> bool:
    """Gère la navigation entre les pages de résultats."""
    global page_counter
    # Sélecteur pour le bouton "Page suivante"
    NEXT_PAGE_SELECTOR = 'a[data-spark-component="pagination-next-trigger"]'
    try:
        next_btn = page.locator(NEXT_PAGE_SELECTOR)
        if next_btn.count() > 0:
            href = next_btn.first.get_attribute("href")
            if href:
                page_counter += 1
                logger.info(f"➡️ Passage à la page suivante... Page actuelle : {page_counter}")
                human_like_scroll_to_element(page, next_btn, scroll_steps=random.randint(3, 5), jitter=True)
                human_like_click(page, next_btn, move_cursor=True, click_variance=30)
                # Attendre le chargement de la nouvelle page via l'URL "recherche"
                page.wait_for_url("**/recherche?*", timeout=60000)
                human_like_delay(3, 5)
                return True
        return False
    except Exception as e:
        logger.error(f"Erreur pagination: {e}")
        return False

def scrape_listings(page: Page):
    """Fonction principale de scraping multi-pages en simulant une navigation humaine."""
    while True:
        process_all_listings(page)
        if total_scraped >= 100:
            logger.info("🏁 100 annonces extraites, fin du scraping multi-pages.")
            break
        if not handle_pagination(page):
            logger.info("🏁 Fin du scraping - Toutes les pages traitées")
            break