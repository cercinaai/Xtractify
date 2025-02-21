import os
import requests
import boto3
from botocore.client import Config
from urllib.parse import urlparse
import logging
from botocore.handlers import disable_signing
import os
import requests
from b2sdk.v2 import InMemoryAccountInfo, B2Api
from urllib.parse import urlparse
import logging
logger = logging.getLogger(__name__)


def get_b2_api():
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)
    b2_api.authorize_account("production", "003a8db8fe4620d0000000001", "K003ytmOR03jy31uqTleH8u6xPGYfN0")
    return b2_api

def upload_buffer_into_bucket(buffer: bytes, filename: str, target: str) -> str:
    try:
        b2_api = get_b2_api()
        bucket = b2_api.get_bucket_by_name("cercina-real-estate-files")
        
        target_name = f"{target}/{filename}"
        
        file_info = bucket.upload_bytes(
            data_bytes=buffer,
            file_name=target_name,
            content_type='image/jpeg'
        )
        
        return f"https://f003.backblazeb2.com/file/cercina-real-estate-files/{target_name}"
    
    except Exception as e:
        logger.error(f"Erreur B2: {str(e)}")
        raise

# The rest of your code (sanitize_filename, upload_image_to_b2) can remain the same




def sanitize_filename(filename: str) -> str:
    """Nettoie le nom du fichier pour éviter les erreurs"""
    if not filename:
        filename = "default_image.jpg"
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in filename)
def upload_image_to_b2(image_url: str, target: str = "real_estate") -> str:
    """Version finale avec vérifications"""
    try:
        # Vérification URL valide
        if not image_url.startswith('http'):
            raise ValueError("URL invalide")

        logger.info(f"📥 Téléchargement de l'image : {image_url}")
        parsed_url = urlparse(image_url)
        filename = sanitize_filename(parsed_url.path.split('/')[-1])
        response = requests.get(
            image_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, comme Gecko) Chrome/91.0.4472.124 Safari/537.36"},
            timeout=10
        )
        response.raise_for_status()

        if not response.content or len(response.content) == 0:
            logger.error(f"⚠️ Image vide après téléchargement : {image_url}")
            return "N/A"

        return upload_buffer_into_bucket(response.content, filename, target)

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Erreur HTTP lors du téléchargement : {str(e)}")
        return "N/A"
    except Exception as e:
        logger.error(f"❌ Erreur générale : {str(e)}")
        return "N/A"

