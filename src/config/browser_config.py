from playwright.sync_api import sync_playwright
from src.config.proxy_manager import get_proxy_url, PROXY_USER, PROXY_PASS,get_current_ip
import random
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; SM-N986U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Mobile Safari/537.36",
]
EXTRA_ARGS = [

]
def setup_browser():
    """Initialise et configure le navigateur Playwright avec IP Royal."""
    proxy = get_proxy_url()
    logger.info(f"🎯 Lancement du navigateur avec proxy : {get_current_ip(proxy)}")

    try:
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(
            proxy={
                "server": proxy,
                "username": PROXY_USER,
                "password": PROXY_PASS
            },
            headless=False,
            args=[
                "--disable-infobars",
                "--disable-web-security",
                f"--window-size={random.choice(['1920,1080', '1440,900', '1366,768'])}",
                "--enable-webgl",
                "--hide-scrollbars",
                "--mute-audio",
            ]
        )

        if not browser:
            logger.error("❌ ERREUR: Le navigateur ne s'est pas lancé !")
            return None, None

        user_agent = random.choice(USER_AGENTS)

        context = browser.new_context(
            user_agent=user_agent,
            viewport={"width": random.randint(500, 600), "height": random.randint(600, 750)},
            locale="fr-FR",
            timezone_id="Europe/Paris",
            java_script_enabled=True
        )

        # Empêcher la détection des bots
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'language', {get: () => 'fr-FR'});
            Object.defineProperty(navigator, 'platform', {get: () => 'Linux armv8l'});
        """)

        return browser, context
    
    except Exception as e:
        logger.error(f"❌ Erreur lors du lancement du navigateur : {e}")
        return None, None
