import logging
import random
from src.utils.human_behavior import human_like_click_search, human_like_delay_search, human_like_scroll_to_element_search
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

def close_cookies_popup(page):
    """Ferme la popup des cookies si elle est présente."""
    try:
        logger.info("🔍 Vérification de la présence de la popup des cookies...")
        cookie_button = page.locator("button:has-text('Accepter')")
        expect(cookie_button).to_be_visible(timeout=5000)
        human_like_click_search(page, "button:has-text('Accepter')", move_cursor=True, click_delay=0.5)
        human_like_delay_search(1, 2)
        logger.info("✅ Popup des cookies fermée.")
    except Exception:
        logger.info("✅ Aucune popup de cookies détectée ou déjà fermée.")

def wait_for_page_load(page):
    """Attend le chargement initial basé sur un élément clé."""
    try:
        logger.info("⏳ Attente du chargement initial de la page...")
        expect(page.locator('a[title="Locations"][href="/c/locations"]')).to_be_visible(timeout=60000)
        human_like_delay_search(1, 3)
    except Exception as e:
        logger.error(f"⚠️ Erreur lors de l'attente du chargement de la page : {e}")

def log_search_requests(page, context: str):
    """Logue toutes les requêtes contenant 'search'."""
    search_requests = []
    def on_response(response):
        if "search" in response.url.lower() and response.status == 200:
            search_requests.append(response.url)
    page.on("response", on_response)
    human_like_delay_search(1, 2)  # Attendre un court délai pour capturer les requêtes
    if search_requests:
        logger.info(f"📡 {context}: Requêtes 'search' trouvées : {search_requests}")
    else:
        logger.warning(f"⚠️ {context}: Aucune requête 'search' détectée.")

def navigate_to_locations(page):
    """Navigue vers la section 'Locations' avec un comportement humain."""
    try:
        LOCATIONS_LINK = 'a[title="Locations"][href="/c/locations"]'
        logger.info("🌀 Défilement progressif vers 'Locations'...")
        human_like_scroll_to_element_search(page, LOCATIONS_LINK, scroll_steps=random.randint(6, 10), jitter=True)

        logger.info("🖱️ Déplacement progressif vers 'Locations'...")
        element = page.locator(LOCATIONS_LINK).first
        expect(element).to_be_visible(timeout=10000)
        box = element.bounding_box()
        if box:
            x, y = box['x'] + box['width'] / 2, box['y'] + box['height'] / 2
            page.mouse.move(x, y, steps=random.randint(10, 20))
            human_like_delay_search(0.5, 1.5)

        logger.info("✅ Clic sur 'Locations'...")
        human_like_click_search(page, LOCATIONS_LINK, move_cursor=True, click_variance=30)

        if page.locator("span[jsselect='heading']").is_visible(timeout=5000):
            logger.error("⚠️ Page inaccessible, tentative de rechargement...")
            page.reload()
            human_like_delay_search(3, 5)
            if page.locator("span[jsselect='heading']").is_visible(timeout=5000):
                logger.critical("❌ Échec du rechargement, page toujours inaccessible.")
                return False
        
        log_search_requests(page, "Après accès à Locations")
        logger.info("✅ Navigation vers 'Locations' réussie.")
        return True
    except Exception as e:
        logger.error(f"⚠️ Erreur lors de la navigation : {e}")
        raise

def apply_filters(page):
    """Applique les filtres avec un comportement humain réaliste et logue les requêtes 'search'."""
    try:
        if page.locator('iframe[title="DataDome CAPTCHA"]').is_visible(timeout=5000):
            logger.warning("⚠️ CAPTCHA détecté avant application des filtres.")
            return False

        FILTRES_BTN = 'button[title="Afficher tous les filtres"]'
        MAISON_CHECKBOX = 'button[role="checkbox"][value="1"]'
        APPARTEMENT_CHECKBOX = 'button[role="checkbox"][value="2"]'
        PRO_CHECKBOX = 'button[role="checkbox"][value="pro"]'

        logger.info("🖱️ Clic sur 'Afficher tous les filtres'...")
        filter_button = page.locator(FILTRES_BTN)
        expect(filter_button).to_be_visible(timeout=60000)
        human_like_click_search(page, FILTRES_BTN, click_delay=0.7, move_cursor=True)
        human_like_delay_search(2, 4)
        log_search_requests(page, "Après ouverture des filtres")

        logger.info("📜 Application du filtre 'Maison'...")
        page.wait_for_selector(MAISON_CHECKBOX, state="visible", timeout=10000)
        human_like_scroll_to_element_search(page, MAISON_CHECKBOX, scroll_steps=4, jitter=True)
        human_like_click_search(page, MAISON_CHECKBOX, click_delay=0.5, move_cursor=True)
        log_search_requests(page, "Après filtre Maison")

        logger.info("📜 Application du filtre 'Appartement'...")
        page.wait_for_selector(APPARTEMENT_CHECKBOX, state="visible", timeout=10000)
        human_like_scroll_to_element_search(page, APPARTEMENT_CHECKBOX, scroll_steps=4, jitter=True)
        human_like_click_search(page, APPARTEMENT_CHECKBOX, click_delay=0.5, move_cursor=True)
        log_search_requests(page, "Après filtre Appartement")

        logger.info("📜 Application du filtre 'Professionnel'...")
        human_like_delay_search(1, 2)
        human_like_scroll_to_element_search(page, PRO_CHECKBOX, scroll_steps=4, jitter=True)
        human_like_click_search(page, PRO_CHECKBOX, click_delay=0.5, move_cursor=True)
        log_search_requests(page, "Après filtre Professionnel")

        logger.info("✅ Filtres appliqués, prêt pour la recherche.")
        return True
    except Exception as e:
        logger.error(f"⚠️ Erreur lors de l'application des filtres : {e}")
        return False