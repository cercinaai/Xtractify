import os
import boto3
from botocore.client import Config

def get_s3_client():
    s3 = boto3.client(
         's3',
         endpoint_url=os.getenv("AWS_S3_ENDPOINT"),
         aws_access_key_id=os.getenv("AWS_S3_ACCESS_KEY"),
         aws_secret_access_key=os.getenv("AWS_S3_SECRET_KEY"),
         config=Config(signature_version='s3v4')
    )
    return s3

def upload_image_to_b2(image_bytes: bytes, filename: str) -> str:
    """
    Upload une image (image_bytes) vers le bucket S3 de Backblaze et retourne l'URL publique de l'image.
    """
    bucket_name = os.getenv("AWS_S3_BUCKET_NAME")
    s3 = get_s3_client()
    s3.put_object(Bucket=bucket_name, Key=filename, Body=image_bytes, ContentType="image/jpeg")
    # Construit l'URL publique selon votre endpoint et bucket
    return f"{os.getenv('AWS_S3_ENDPOINT')}/file/{bucket_name}/{filename}"