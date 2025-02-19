import logging
import random
from src.utils.human_behavior import human_like_click_search, human_like_delay_search, human_like_scroll_to_element_search
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

def close_cookies_popup(page):
    """Ferme la popup des cookies si elle est présente."""
    try:
        logger.info("🔍 Vérification de la présence de la popup des cookies...")
        human_like_click_search(page, "button:has-text('Accepter')")
    except Exception:
        logger.info("✅ Aucune popup de cookies détectée ou déjà fermée.")

def wait_for_page_load(page):
    """Attend le chargement complet de la page avant de continuer."""
    try:
        logger.info("⏳ Attente du chargement complet de la page...")
        page.wait_for_load_state("networkidle")
        human_like_delay_search(1, 3)
    except Exception as e:
        logger.error(f"⚠️ Erreur lors de l'attente du chargement de la page : {e}")

def navigate_to_locations(page):
    """Navigue vers la section 'Locations' en simulant un comportement humain."""
    try:
        # Sélecteur du lien "Locations"
        LOCATIONS_LINK = 'a[title="Locations"][href="/c/locations"]'

        logger.info("🌀 Défilement progressif vers 'Locations'...")
        human_like_scroll_to_element_search(page, LOCATIONS_LINK, scroll_steps=random.randint(6, 10), jitter=True)

        logger.info("🖱️ Déplacement progressif de la souris vers 'Locations'...")
        element = page.locator(LOCATIONS_LINK).first
        if element.count():
            box = element.bounding_box()
            if box:
                x, y = box['x'] + box['width'] / 2, box['y'] + box['height'] / 2
                page.mouse.move(x, y, steps=random.randint(10, 20))
                human_like_delay_search(0.5, 1.5)

            logger.info("✅ Clic sur 'Locations'...")
            human_like_click_search(page, LOCATIONS_LINK, move_cursor=True, click_variance=30)
        else:
            logger.warning("⚠️ Lien 'Locations' introuvable après le défilement.")
            
        if page.locator("span[jsselect='heading']").is_visible(timeout=5000):
            logger.error("La page est inaccessible ! Tentative de rechargement...")
            page.reload()
            human_like_delay_search(3, 5)

        # Vérifier à nouveau si la page est toujours inaccessible
        if page.locator("span[jsselect='heading']").is_visible(timeout=5000):
            logger.critical("Échec du rechargement, la page reste inaccessible.")
            return False
        else:
            logger.info("Page rechargée avec succès, reprise de l'exécution.")    
        
    except Exception as e:
        logger.error(f"⚠️ Erreur navigation : {e}")
        raise

def apply_filters(page):
    """Applique les filtres avec un comportement réaliste en attendant l'affichage des éléments essentiels."""
    try:
        # Vérification préalable du captcha avant de cliquer sur les filtres
        if page.locator('iframe[title="DataDome CAPTCHA"]').is_visible(timeout=5000):
            logger.warning("⚠️ CAPTCHA détecté. Fermeture du navigateur et relance de open_leboncoin()...")
            page.context.browser.close()
            from src.scrapers.leboncoin.location_scraper import open_leboncoin
            open_leboncoin()
            return

        # Sélecteurs des éléments
        FILTRES_BTN = 'button[title="Afficher tous les filtres"]'
        MAISON_CHECKBOX = 'button[role="checkbox"][value="1"]'
        APPARTEMENT_CHECKBOX = 'button[role="checkbox"][value="2"]'
        PRO_CHECKBOX = 'button[role="checkbox"][value="pro"]'
        RECHERCHE_BTN = 'button[aria-label="Rechercher"]:visible'

        # Attendre et cliquer sur le bouton des filtres
        filter_button = page.locator(FILTRES_BTN)
        expect(filter_button).to_be_visible(timeout=60000)
        human_like_delay_search(2, 3)
        logger.info("🖱️ Clic sur le bouton 'Filtres'...")
        human_like_click_search(page, FILTRES_BTN, click_delay=0.7, move_cursor=True)
        human_like_delay_search(3, 6)  # Pause pour chargement du menu des filtres

        # Appliquer les filtres
        logger.info("📜 Attente de l'affichage du filtre 'Maison'...")
        page.wait_for_selector(MAISON_CHECKBOX, state="visible", timeout=10000)
        logger.info("📜 Filtre 'Maison' affiché.")
        human_like_scroll_to_element_search(page, MAISON_CHECKBOX, scroll_steps=4, jitter=True)
        human_like_click_search(page, MAISON_CHECKBOX, click_delay=0.5, move_cursor=True)

        logger.info("📜 Attente de l'affichage du filtre 'Appartement'...")
        page.wait_for_selector(APPARTEMENT_CHECKBOX, state="visible", timeout=10000)
        logger.info("📜 Filtre 'Appartement' affiché.")
        human_like_scroll_to_element_search(page, APPARTEMENT_CHECKBOX, scroll_steps=4, jitter=True)
        human_like_click_search(page, APPARTEMENT_CHECKBOX, click_delay=0.5, move_cursor=True)

        # Pause avant le filtre "Professionnel"
        logger.info("⏳ Pause de réflexion avant d'appliquer le filtre 'Professionnel'...")
        human_like_delay_search(2, 3)
        logger.info("🖱️ Défilement et activation du filtre 'Professionnel'...")
        human_like_scroll_to_element_search(page, PRO_CHECKBOX, scroll_steps=4, jitter=True)
        human_like_click_search(page, PRO_CHECKBOX, click_delay=0.5, move_cursor=True)

        # Attendre et cliquer sur le bouton "Rechercher"
        logger.info("⏳ Attente du chargement des filtres appliqués...")
        human_like_delay_search(2.5, 6)
        logger.info("🧐 Vérification du bouton 'Rechercher' avant clic...")
        page.wait_for_selector(RECHERCHE_BTN, state="visible", timeout=5000)
        logger.info("🔄 Défilement et clic sur 'Rechercher'...")
        human_like_scroll_to_element_search(page, RECHERCHE_BTN, scroll_steps=4, jitter=True)
        if page.locator(RECHERCHE_BTN).is_visible():
            human_like_click_search(page, RECHERCHE_BTN, move_cursor=True, precision=0.8)
            logger.info("✅ Clic réussi sur 'Rechercher'.")
        else:
            logger.warning("⚠️ Bouton 'Rechercher' toujours invisible après l'attente.")

        # Attendre que la page se charge complètement après le clic sur "Rechercher"
        logger.info("⏳ Attente du chargement complet de la page de recherche...")
        filter_button = page.locator(FILTRES_BTN)
        expect(filter_button).to_be_visible(timeout=60000) 
        human_like_delay_search(1, 3)

        # # Désactivation des CSS et images pour accélérer le scraping
        # page.route("**/*.css", lambda route, request: route.abort())
        # page.route("**/*.{png,jpg,jpeg,gif}", lambda route, request: route.abort())
        # logger.info("✅ CSS et images désactivées après le clic sur 'Rechercher'.")

    except Exception as e:
        logger.error(f"⚠️ Erreur filtres : {e}")