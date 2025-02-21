import random
import time
import logging
from playwright.sync_api import Page, Locator

logger = logging.getLogger(__name__)

def human_like_delay(min_time=1, max_time=3):
    """Simule un délai aléatoire avec une distribution humaine plus réaliste."""
    delay = random.uniform(min_time, max_time) * (1 + random.random() * 0.3)
    if random.random() < 0.15:  # 15% de chance d'une pause plus longue (hésitation)
        delay += random.uniform(1.5, 3)
    logger.info(f"⏳ Attente aléatoire de {delay:.2f} secondes...")
    time.sleep(delay)

def human_like_scroll_to_element(page: Page, element: str | Locator, scroll_steps=6, jitter=True, reverse=False):
    """Défilement progressif avec variabilité humaine, adapté au navigateur."""
    try:
        if isinstance(element, str):
            locator = page.locator(element).first
        elif isinstance(element, Locator):
            locator = element
        else:
            raise ValueError("L'élément doit être un sélecteur string ou un Locator")

        if not locator.is_visible(timeout=5000):
            logger.warning(f"⚠️ Élément {element} introuvable ou non visible.")
            return

        logger.info(f"🌀 Défilement humain vers {element} ({scroll_steps} étapes)...")
        viewport_height = page.evaluate("window.innerHeight")
        current_scroll = page.evaluate("window.scrollY")

        # Calculer la position cible
        box = locator.bounding_box()
        if not box:
            logger.warning(f"⚠️ Impossible de calculer la position de {element}.")
            return
        target_y = box["y"] + box["height"] / 2 - viewport_height / 2

        # Simuler un défilement progressif avec des variations
        for step in range(scroll_steps):
            step_size = (target_y - current_scroll) / (scroll_steps - step)
            if jitter:
                step_size += random.uniform(-viewport_height * 0.15, viewport_height * 0.15)
            if reverse:
                step_size = -abs(step_size)

            page.mouse.wheel(0, int(step_size))  # Utilisation de wheel pour simuler le scroll
            human_like_delay(0.2, 0.6)
            current_scroll += step_size

        # Ajustement final
        locator.scroll_into_view_if_needed(timeout=2000)

        # Simuler un léger overscroll ou ajustement
        if random.random() < 0.35:
            overscroll = random.uniform(-120, -40) if not reverse else random.uniform(40, 120)
            page.mouse.wheel(0, int(overscroll))
            human_like_delay(0.3, 0.8)

        human_like_delay(0.5, 1.5)  # Pause naturelle après arrivée

    except Exception as e:
        logger.error(f"⚠️ Erreur défilement : {e}")

def human_like_click(page: Page, element: str | Locator, move_cursor=False, click_delay=0.3, click_variance=20, precision=0.95, retries=1):
    """Clic réaliste avec micro-mouvements, compatible avec mobile et desktop."""
    for attempt in range(retries + 1):
        try:
            if isinstance(element, str):
                locator = page.locator(element).first
            elif isinstance(element, Locator):
                locator = element
            else:
                raise ValueError("L'élément doit être un sélecteur string ou un Locator")

            if not locator.is_visible(timeout=5000):
                logger.warning(f"⚠️ Élément {element} introuvable ou non visible.")
                return

            box = locator.bounding_box()
            if not box:
                logger.warning(f"⚠️ Impossible d'obtenir la position de {element}.")
                return

            # Position de clic réaliste (éviter les bords)
            x = box['x'] + box['width'] * random.uniform(0.25, 0.75)
            y = box['y'] + box['height'] * random.uniform(0.25, 0.75)

            # Simuler un déplacement du curseur avant clic
            if move_cursor and random.random() < precision:
                page.mouse.move(
                    x + random.randint(-click_variance, click_variance),
                    y + random.randint(-click_variance, click_variance),
                    steps=random.randint(15, 35)
                )
                human_like_delay(0.1, click_delay)

            # Hésitation avant clic
            if random.random() < 0.25:
                human_like_delay(0.4, 1.0)

            # Clic avec légère variation
            page.mouse.click(
                x + random.randint(-5, 5),
                y + random.randint(-5, 5),
                delay=random.randint(50, 200)
            )

            # Micro-mouvement post-clic
            if random.random() < 0.7:
                page.mouse.move(
                    x + random.randint(-15, 15),
                    y + random.randint(-15, 15),
                    steps=random.randint(3, 8)
                )
                human_like_delay(0.05, 0.25)

            break

        except Exception as e:
            if attempt < retries:
                logger.warning(f"⚠️ Réessai du clic ({attempt+1}/{retries})...")
                human_like_delay(0.5, 1.2)
                continue
            logger.error(f"⚠️ Erreur clic : {e}")
            raise

# Fonctions "_search" conservées avec les mêmes paramètres
def human_like_delay_search(min_time=1, max_time=3):
    """Wrapper pour human_like_delay avec les mêmes paramètres."""
    human_like_delay(min_time, max_time)

def human_like_scroll_to_element_search(page: Page, selector: str, scroll_steps=6, jitter=True, reverse=False):
    """Wrapper pour human_like_scroll_to_element avec selector string."""
    human_like_scroll_to_element(page, selector, scroll_steps, jitter, reverse)

def human_like_click_search(page: Page, selector: str, move_cursor=False, click_delay=0.3, click_variance=20, precision=0.95):
    """Wrapper pour human_like_click avec selector string."""
    human_like_click(page, selector, move_cursor, click_delay, click_variance, precision, retries=1)

def human_like_mouse_pattern(page: Page):
    """Simule des mouvements aléatoires réalistes adaptés au viewport."""
    width, height = page.viewport_size["width"], page.viewport_size["height"]

    logger.info("🖱️ Simulation de mouvements humains aléatoires...")
    for _ in range(random.randint(3, 7)):  # Variation du nombre de mouvements
        target_x = random.randint(int(width * 0.15), int(width * 0.85))
        target_y = random.randint(int(height * 0.15), int(height * 0.85))

        # Mouvement fluide avec courbe naturelle
        page.mouse.move(
            target_x + random.randint(-25, 25),
            target_y + random.randint(-25, 25),
            steps=random.randint(20, 50)
        )

        # Pause avec probabilité d'hésitation
        if random.random() < 0.5:
            human_like_delay(0.4, 1.2)
        else:
            human_like_delay(0.1, 0.5)

    # Simuler un ajustement final
    if random.random() < 0.6:
        page.mouse.wheel(0, random.randint(-80, 80))
        human_like_delay(0.3, 0.8)