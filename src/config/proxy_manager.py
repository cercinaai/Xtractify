import random
import string
import logging
import requests

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_session_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

SESSION_ID = generate_session_id()

PROXY_HOST = "geo.iproyal.com"
PROXY_PORT = "12321"
PROXY_USER = "MEEr6bZGGdo8q1xU"
PROXY_PASS = f"uSMU7Zv9SRjhG60b_country-fr_session-{SESSION_ID}_lifetime-35m_streaming-1"

PROXY_URL = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"

def get_proxy_url():
    """Retourne l'URL du proxy pour l'utiliser dans tout le projet."""
    session_id = generate_session_id()
    proxy_pass = f"uSMU7Zv9SRjhG60b_country-fr_session-{session_id}_lifetime-35m_streaming-1"
    # proxy_pass = "uSMU7Zv9SRjhG60b_country-fr_session-hNYOQSCI_lifetime-30m"
    proxy_url = f"http://{PROXY_USER}:{proxy_pass}@{PROXY_HOST}:{PROXY_PORT}"
    return proxy_url

def get_current_ip(proxy_url):
    """Vérifie l'IP actuelle utilisée par le proxy."""
    try:
        response = requests.get("https://api64.ipify.org?format=json", proxies={"http": proxy_url, "https": proxy_url}, timeout=10)
        ip = response.json().get("ip", "Unknown")
        logger.info(f"📡 IP actuelle via proxy : {ip}")
        return ip
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Impossible de récupérer l'IP via proxy: {e}")
        return "Unknown"
