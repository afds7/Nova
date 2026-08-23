"""Helpers para upload direto de evidências em S3 ou Cloudflare R2."""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict
from uuid import uuid4

from django.conf import settings

ALLOWED_UPLOADS = {
    'application/pdf': {'.pdf'},
    'image/png': {'.png'},
    'image/jpeg': {'.jpg', '.jpeg'},
    'video/mp4': {'.mp4'},
}
MAX_UPLOAD_BYTES = 25 * 1024 * 1024


class PresignedUpload(TypedDict):
    url: str
    object_key: str
    expires_in: int


def create_presigned_upload(
    filename: str,
    content_type: str,
    *,
    profile_id: str | None = None,
    file_size: int | None = None,
    expires_in: int = 900,
    prefix: str = 'evidencias',
) -> PresignedUpload:
    """Gera uma URL PUT temporária; nenhum arquivo é salvo no servidor."""
    if not filename or content_type not in ALLOWED_UPLOADS:
        raise ValueError('filename e content_type são obrigatórios')
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_UPLOADS[content_type]:
        raise ValueError('tipo de arquivo não permitido')
    if file_size is None or file_size < 1 or file_size > MAX_UPLOAD_BYTES:
        raise ValueError('o arquivo deve ter entre 1 byte e 25 MB')
    if not 60 <= expires_in <= 3600:
        raise ValueError('expires_in deve estar entre 60 e 3600 segundos')

    safe_prefix = prefix.strip('/')
    owner_prefix = f'{safe_prefix}/{profile_id}' if profile_id else safe_prefix
    object_key = f'{owner_prefix}/{uuid4()}{suffix}'

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
    return {
        'url': url,
        'object_key': object_key,
        'expires_in': expires_in,
    }


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
