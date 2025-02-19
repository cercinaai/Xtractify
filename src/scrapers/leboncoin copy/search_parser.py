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
    """Applique les filtres avec un comportement réaliste."""
    try:
        # Sélecteurs des éléments
        FILTRES_BTN = 'button[title="Afficher tous les filtres"]'
        MAISON_CHECKBOX = 'button[role="checkbox"][value="1"]'
        APPARTEMENT_CHECKBOX = 'button[role="checkbox"][value="2"]'
        PRO_CHECKBOX = 'button[role="checkbox"][value="pro"]'
        RECHERCHE_BTN = 'button[aria-label="Rechercher"]:visible'
        
        filter_button = page.locator('button[title="Afficher tous les filtres"]')
        expect(filter_button).to_be_visible(timeout=60000)
        human_like_delay_search(2, 3) 

        logger.info("🖱️ Clic sur le bouton 'Filtres'...")
        human_like_click_search(page, FILTRES_BTN, click_delay=0.7, move_cursor=True)
        human_like_delay_search(3, 6)  # Pause pour chargement du menu des filtres


        # Sélection de "Maison" et "Appartement"
        for filter_name, checkbox_selector in [("Maison", MAISON_CHECKBOX), ("Appartement", APPARTEMENT_CHECKBOX)]:
            logger.info(f"📜 Défilement et sélection de '{filter_name}'...")
            
            human_like_scroll_to_element_search(page, checkbox_selector, scroll_steps=4, jitter=True)
            human_like_click_search(page, checkbox_selector, click_delay=0.5, move_cursor=True)

        logger.info("⏳ Pause de réflexion avant d'appliquer le filtre 'Professionnel'...")
        human_like_delay_search(2, 3)

        # Sélection de "Professionnel"
        logger.info("🖱️ Défilement et activation du filtre 'Professionnel'...")
        human_like_scroll_to_element_search(page, PRO_CHECKBOX, scroll_steps=4, jitter=True)
        human_like_click_search(page, PRO_CHECKBOX, click_delay=0.5, move_cursor=True)

        logger.info("⏳ Attente du chargement des filtres appliqués...")
        human_like_delay_search(2.5, 6)  # Pause réaliste

        # Attente supplémentaire si le bouton "Rechercher" n'est pas encore visible
        logger.info("🧐 Vérification du bouton 'Rechercher' avant clic...")
        page.wait_for_selector(RECHERCHE_BTN, state="visible", timeout=5000)

        # Scroll progressif vers le bouton "Rechercher"
        logger.info("🔄 Défilement et clic sur 'Rechercher'...")
        human_like_scroll_to_element_search(page, RECHERCHE_BTN, scroll_steps=4, jitter=True)

        # Vérification que le bouton est interactif
        if page.locator(RECHERCHE_BTN).is_visible():
            human_like_click_search(page, RECHERCHE_BTN, move_cursor=True, precision=0.8)
            logger.info("✅ Clic réussi sur 'Rechercher'.")
        else:
            logger.warning("⚠️ Bouton 'Rechercher' toujours invisible après l'attente.")

    except Exception as e:
        logger.error(f"⚠️ Erreur filtres : {e}")