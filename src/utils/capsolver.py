import os
import time
import aiohttp
import logging
import json
import asyncio
from playwright.async_api import Page

logger = logging.getLogger(__name__)

def parse_cookie_string(cookie_string: str) -> dict:
    """Parse une chaîne de cookie comme dans cookies.util.ts."""
    cookie_parts = cookie_string.split(';')
    name_value = cookie_parts[0].strip().split('=')
    cookie = {"name": name_value[0], "value": name_value[1], "domain": ".leboncoin.fr", "path": "/"}
    
    for attr in cookie_parts[1:]:
        attr = attr.strip()
        if '=' in attr:
            key, val = attr.split('=', 1)
            key = key.lower()
            if key == "domain":
                cookie["domain"] = val
            elif key == "path":
                cookie["path"] = val
            elif key == "secure":
                cookie["secure"] = True
            elif key == "httponly":
                cookie["httpOnly"] = True
            elif key == "samesite":
                cookie["sameSite"] = val
            elif key == "max-age":
                cookie["expires"] = int(time.time()) + int(val)
    return cookie

async def bypass_datadome_captcha_by_capsolver(page: Page, captcha_url: str, proxy_info: dict, user_agent: str) -> bool:
    """Résout le CAPTCHA DataDome avec CapSolver."""
    capsolver_api_key = os.getenv("CAPSOLVER_API_KEY")
    if not capsolver_api_key:
        logger.error("❌ CAPSOLVER_API_KEY non configuré.")
        raise ValueError("CAPSOLVER_API_KEY non configuré.")

    proxy_str = f"{proxy_info['username']}:{proxy_info['password']}@{proxy_info['server']}"
    payload = {
        "clientKey": capsolver_api_key,
        "task": {
            "type": "DatadomeSliderTask",
            "websiteURL": page.url,
            "captchaUrl": captcha_url,
            "userAgent": user_agent,
            "proxy": proxy_str.replace("http://", "")
        }
    }

    logger.info(f"🔧 Création de la tâche CapSolver pour {page.url} avec proxy {proxy_str}...")
    logger.debug(f"Payload CapSolver : {json.dumps(payload, indent=2)}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.capsolver.com/createTask", json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                create_task_data = await response.json()
                logger.debug(f"Réponse CapSolver : {json.dumps(create_task_data, indent=2)}")
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création de la tâche CapSolver : {e}")
        raise

    task_id = create_task_data.get("taskId")
    if not task_id:
        error_desc = create_task_data.get("errorDescription", "No taskId returned")
        logger.error(f"❌ Échec de création de tâche CapSolver : {error_desc}")
        raise Exception(f"Échec de création : {error_desc}")

    logger.info(f"⏳ Attente de la résolution (taskId: {task_id})...")
    max_attempts = 30
    for attempt in range(max_attempts):
        await asyncio.sleep(2)
        result_payload = {"clientKey": capsolver_api_key, "taskId": task_id}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post("https://api.capsolver.com/getTaskResult", json=result_payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    result_data = await response.json()
                    logger.debug(f"Réponse getTaskResult CapSolver (tentative {attempt+1}) : {json.dumps(result_data, indent=2)}")
        except Exception as e:
            logger.warning(f"⚠️ Erreur lors de la vérification : {e}")
            continue

        status = result_data.get("status")
        if status == "processing":
            continue
        if status == "ready":
            cookie_value = result_data.get("solution", {}).get("cookie")
            if not cookie_value:
                logger.error("❌ Pas de cookie dans la solution CapSolver.")
                raise Exception("Pas de cookie dans la solution.")
            cookie = parse_cookie_string(cookie_value)
            await page.context.add_cookies([cookie])
            logger.info("✅ Cookie DataDome ajouté, rechargement de la page...")
            await page.reload(wait_until="networkidle")
            return True
        if status == "failed":
            error_desc = result_data.get("errorDescription", "Unknown error")
            logger.error(f"❌ CapSolver a échoué : {error_desc}")
            raise Exception(f"CapSolver a échoué : {error_desc}")

    logger.error(f"❌ Timeout après {max_attempts * 2} secondes.")
    raise Exception("Timeout CapSolver")

async def bypass_datadome_captcha_by_2captcha(page: Page, captcha_url: str, proxy_info: dict, user_agent: str) -> bool:
    """Résout le CAPTCHA DataDome avec 2Captcha."""
    two_captcha_api_key = os.getenv("TWO_CAPTCHA_API_KEY")
    if not two_captcha_api_key:
        logger.error("❌ TWO_CAPTCHA_API_KEY non configuré.")
        raise ValueError("TWO_CAPTCHA_API_KEY non configuré.")

    proxy_host, proxy_port = proxy_info["server"].split(":")
    payload = {
        "key": two_captcha_api_key,
        "method": "datadome",
        "captcha_url": captcha_url,
        "pageurl": page.url,
        "userAgent": user_agent,
        "proxy": f"{proxy_info['username']}:{proxy_info['password']}@{proxy_host}:{proxy_port}",
        "json": 1
    }

    logger.info(f"🔧 Création de la tâche 2Captcha pour {page.url} avec proxy {proxy_host}:{proxy_port}...")
    logger.debug(f"Payload 2Captcha : {json.dumps(payload, indent=2)}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.2captcha.com/in.php", json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                create_task_data = await response.json()
                logger.debug(f"Réponse 2Captcha : {json.dumps(create_task_data, indent=2)}")
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création de la tâche 2Captcha : {e}")
        raise

    if create_task_data.get("errorId", 0) != 0:
        error_desc = create_task_data.get("errorDescription", "Unknown error")
        logger.error(f"❌ Échec de création de tâche 2Captcha : {error_desc}")
        raise Exception(f"Échec de création : {error_desc}")
    task_id = create_task_data.get("request")
    if not task_id or task_id.startswith("ERROR"):
        logger.error(f"❌ Échec de création de tâche 2Captcha : {task_id}")
        raise Exception(f"Échec de création : {task_id}")

    logger.info(f"⏳ Attente de la résolution (taskId: {task_id})...")
    max_attempts = 30
    for attempt in range(max_attempts):
        await asyncio.sleep(5)
        result_payload = {
            "key": two_captcha_api_key,
            "action": "get",
            "id": task_id,
            "json": 1
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post("https://api.2captcha.com/res.php", json=result_payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    result_data = await response.json()
                    logger.debug(f"Réponse getTaskResult 2Captcha (tentative {attempt+1}) : {json.dumps(result_data, indent=2)}")
        except Exception as e:
            logger.warning(f"⚠️ Erreur lors de la vérification : {e}")
            continue

        if result_data.get("errorId", 0) != 0:
            error_desc = result_data.get("errorDescription", "Unknown error")
            logger.error(f"❌ 2Captcha a échoué : {error_desc}")
            raise Exception(f"2Captcha a échoué : {error_desc}")
        status = result_data.get("status")
        if status == "processing" or result_data.get("request") == "CAPCHA_NOT_READY":
            continue
        if status == "ready":
            cookie_value = result_data.get("request")
            if not cookie_value:
                logger.error("❌ Pas de cookie dans la solution 2Captcha.")
                raise Exception("Pas de cookie dans la solution.")
            cookie = parse_cookie_string(cookie_value)
            await page.context.add_cookies([cookie])
            logger.info("✅ Cookie DataDome ajouté, rechargement de la page...")
            await page.reload(wait_until="networkidle")
            return True

    logger.error(f"❌ Timeout après {max_attempts * 5} secondes.")
    raise Exception("Timeout 2Captcha")

async def solve_captcha(page: Page, captcha_url: str, proxy_info: dict, user_agent: str) -> bool:
    """Tente de résoudre le CAPTCHA avec CapSolver, puis 2Captcha."""
    try:
        return await bypass_datadome_captcha_by_capsolver(page, captcha_url, proxy_info, user_agent)
    except Exception as e:
        logger.warning(f"⚠️ Échec de CapSolver : {e}. Passage à 2Captcha...")
        try:
            return await bypass_datadome_captcha_by_2captcha(page, captcha_url, proxy_info, user_agent)
        except Exception as e2:
            logger.error(f"❌ Échec de 2Captcha : {e2}. Résolution impossible.")
            raise