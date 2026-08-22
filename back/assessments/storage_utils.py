"""Helpers para upload direto de evidências em S3 ou Cloudflare R2."""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict
from uuid import uuid4

from django.conf import settings


class PresignedUpload(TypedDict):
    url: str
    object_key: str
    expires_in: int


def create_presigned_upload(
    filename: str,
    content_type: str,
    *,
    expires_in: int = 900,
    prefix: str = 'evidencias',
) -> PresignedUpload:
    """Gera uma URL PUT temporária; nenhum arquivo é salvo no servidor."""
    if not filename or not content_type:
        raise ValueError('filename e content_type são obrigatórios')
    if not 60 <= expires_in <= 3600:
        raise ValueError('expires_in deve estar entre 60 e 3600 segundos')

    suffix = Path(filename).suffix.lower()[:20]
    object_key = f'{prefix.strip("/")}/{uuid4()}{suffix}'

    client = _s3_client()
    url = client.generate_presigned_url(
        ClientMethod='put_object',
        Params={
            'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
            'Key': object_key,
            'ContentType': content_type,
        },
        ExpiresIn=expires_in,
        HttpMethod='PUT',
    )
    return {'url': url, 'object_key': object_key, 'expires_in': expires_in}


def _s3_client():
    import boto3

    return boto3.client(
        's3',
        endpoint_url=settings.AWS_S3_ENDPOINT_URL or None,
        region_name=settings.AWS_S3_REGION_NAME,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        config=boto3.session.Config(signature_version='s3v4'),
    )
