import logging
import time
import multiprocessing
from src.config.browser_config import setup_browser
from src.scrapers.leboncoin.search_parser import (
    close_cookies_popup, wait_for_page_load,
    navigate_to_locations, apply_filters
)
from src.scrapers.leboncoin.listings_parser import scrape_listings_via_api

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def open_leboncoin():
    """Ouvre Leboncoin avec Playwright et un proxy IP Royal dans un processus séparé."""
    logger.info("🚀 Démarrage du navigateur Playwright avec IP Royal...")

    try:
        browser, context = setup_browser()

        if browser is None or context is None:
            logger.error("⚠️ ERREUR: Impossible d'ouvrir le navigateur, vérifiez `setup_browser()`.")
            return {"status": "error", "message": "Impossible d'ouvrir le navigateur"}

        page = context.new_page()

        logger.info("🌍 Accès à https://mobile.leboncoin.fr/ ...")
        page.goto("https://mobile.leboncoin.fr/", timeout=60000)

        # Attendre le chargement complet de la page
        wait_for_page_load(page)

        # Fermer la popup des cookies
        close_cookies_popup(page)

        # Naviguer vers Locations
        navigate_to_locations(page)

        # Appliquer les filtres
        apply_filters(page)

        # Extraire les annonces
        # scrape_listings_via_api(page)
        scrape_listings_via_api(page)


        # # Lancer la recherche

        title = page.title()
        logger.info(f"✅ Page ouverte - Titre : {title}")

        # Maintenir le navigateur ouvert pour test
        time.sleep(60)

        return {"status": "success", "title": title}

    except Exception as e:
        logger.error(f"⚠️ Erreur lors de l'accès à Leboncoin : {e}")
        return {"status": "error", "message": str(e)}

def access_leboncoin():
    """Lance Playwright dans un processus séparé et attend indéfiniment la fin du scraping."""
    process = multiprocessing.Process(target=open_leboncoin)
    process.start()
    process.join()  # Attend la fin du processus sans timeout
    return {"status": "success", "message": "Scraping terminé."}
