import random
import time
import logging

logger = logging.getLogger(__name__)

def human_like_delay(min_time=1, max_time=3):
    """Simule un délai aléatoire pour imiter un comportement humain."""
    delay = random.uniform(min_time, max_time)
    logger.info(f"⏳ Attente aléatoire de {delay:.2f} secondes...")
    time.sleep(delay)

import random
import time
from playwright.sync_api import Page, Locator

def human_like_scroll_to_element(page, element, scroll_steps=6, jitter=True, reverse=False):
    """Défilement progressif avec variabilité humaine, supporte string ou Locator."""
    try:
        if isinstance(element, str):
            locator = page.locator(element).first
        elif isinstance(element, Locator):
            locator = element
        else:
            raise ValueError("L'élément doit être un sélecteur string ou un Locator")

        if not locator.count():
            logger.warning(f"⚠️ Élément {element} introuvable ou non visible.")
            return

        logger.info(f"🌀 Défilement humain vers {element} ({scroll_steps} étapes)...")
        for step in range(scroll_steps):
            step_size = random.randint(80, 150)
            if reverse:
                step_size = -step_size
            if jitter:
                step_size += random.randint(-20, 20)
            if page.evaluate("matchMedia('(pointer: fine)').matches"):
                page.mouse.wheel(0, step_size)
            else:
                page.touchscreen.swipe(0, step_size)
            time.sleep(random.uniform(0.3, 0.6))

        locator.scroll_into_view_if_needed()
        time.sleep(random.uniform(0.5, 1))
        # Pause aléatoire supplémentaire
        if random.random() < 0.3:
            page.mouse.wheel(0, random.randint(-100, -30))
            time.sleep(random.uniform(0.2, 0.7))
        if random.random() < 0.4:
            page.mouse.wheel(0, random.randint(50, 100))
            time.sleep(random.uniform(0.1, 0.3))
    except Exception as e:
        logger.error(f"⚠️ Erreur défilement : {e}")

def human_like_click(page, element, move_cursor=False, click_delay=0.3, click_variance=20, precision=0.95, retries=1):
    """Clic réaliste avec micro-mouvements (accepte string ou Locator)."""
    for attempt in range(retries + 1):
        try:
            if isinstance(element, str):
                locator = page.locator(element).first
            elif isinstance(element, Locator):
                locator = element
            else:
                raise ValueError("L'élément doit être un sélecteur string ou un Locator")

            if not locator.count():
                logger.warning(f"⚠️ Élément {element} introuvable ou non visible.")
                return

            box = locator.bounding_box()
            if not box:
                logger.warning(f"⚠️ Impossible d'obtenir la position de {element}.")
                return

            x = box['x'] + box['width'] * random.uniform(0.1, 0.9)
            y = box['y'] + box['height'] * random.uniform(0.1, 0.9)

            if move_cursor and random.random() < precision:
                page.mouse.move(
                    x + random.randint(-click_variance, click_variance),
                    y + random.randint(-click_variance, click_variance),
                    steps=random.randint(15, 30)
                )
                time.sleep(random.uniform(0.1, click_delay))

            time.sleep(random.uniform(0.05, 0.2))
            locator.click(delay=random.randint(30, 150))

            if random.random() < 0.6:
                page.mouse.move(
                    x + random.randint(-10, 10),
                    y + random.randint(-10, 10),
                    steps=3
                )
            break

        except Exception as e:
            if attempt < retries:
                logger.warning(f"⚠️ Réessai du clic ({attempt+1}/{retries})...")
                continue
            raise

def human_like_delay_search(min_time=1, max_time=3):
    """Simule un délai aléatoire pour imiter un comportement humain."""
    delay = random.uniform(min_time, max_time)
    logger.info(f"⏳ Attente aléatoire de {delay:.2f} secondes...")
    time.sleep(delay)

def human_like_scroll_to_element_search(page, selector, scroll_steps=6, jitter=True, reverse=False):
    """Défilement progressif avec variabilité humaine (supporte mobile et desktop)."""
    try:
        element = page.locator(selector).first
        if not element.count():
            logger.warning(f"⚠️ Élément {selector} introuvable ou non visible.")
            return

        logger.info(f"🌀 Défilement humain vers {selector} ({scroll_steps} étapes)...")

        for step in range(scroll_steps):
            step_size = random.randint(80, 150)
            if reverse:
                step_size = -step_size  # Scroll vers le haut si nécessaire
            if jitter:
                step_size += random.randint(-20, 20)  # Ajoute un peu de variation

            # Défilement souris (Desktop)
            if page.evaluate("matchMedia('(pointer: fine)').matches"):
                page.mouse.wheel(0, step_size)
            else:
                # Défilement tactile (Mobile)
                page.touchscreen.swipe(0, step_size)

            human_like_delay(0.3, 0.6)

        element.scroll_into_view_if_needed()
        human_like_delay(0.5, 1)

    except Exception as e:
        logger.error(f"⚠️ Erreur défilement : {e}")

def human_like_click_search(page, selector, move_cursor=False, click_delay=0.3, click_variance=20, precision=0.95):
    """Clic réaliste avec micro-mouvements."""
    try:
        element = page.locator(selector).first
        if not element.count():
            logger.warning(f"⚠️ Élément {selector} introuvable ou non visible.")
            return

        box = element.bounding_box()
        if not box:
            logger.warning(f"⚠️ Impossible d'obtenir la position de {selector}.")
            return

        x = box['x'] + box['width'] * random.uniform(0.1, 0.9)
        y = box['y'] + box['height'] * random.uniform(0.1, 0.9)

        if move_cursor and random.random() < precision:
            page.mouse.move(
                x + random.randint(-click_variance, click_variance),
                y + random.randint(-click_variance, click_variance),
                steps=random.randint(15, 30)
            )
            human_like_delay(0.1, click_delay)

        time.sleep(random.uniform(0.05, 0.2))
        element.click(delay=random.randint(30, 150))

        if random.random() < 0.6:
            page.mouse.move(
                x + random.randint(-10, 10),
                y + random.randint(-10, 10),
                steps=3
            )

    except Exception as e:
        logger.error(f"⚠️ Erreur clic : {e}")
        
        
def human_like_mouse_pattern(page):
    width, height = page.viewport_size.values()
    for _ in range(random.randint(3, 5)):
        page.mouse.move(
            random.randint(0, width),
            random.randint(0, height),
            steps=random.randint(20, 40),
            delay=random.randint(50, 200)
        )