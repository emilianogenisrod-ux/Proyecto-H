"""Cliente MinIO para imágenes, plantillas y videos."""

from __future__ import annotations

from urllib.parse import urlparse

from app.config import settings

_client = None


def minio_enabled() -> bool:
    return bool(
        settings.MINIO_ENABLED
        and settings.MINIO_ACCESS_KEY
        and settings.MINIO_SECRET_KEY
        and settings.MINIO_ENDPOINT
    )


def get_minio_client():
    global _client
    if not minio_enabled():
        return None
    if _client is not None:
        return _client

    from minio import Minio

    endpoint = settings.MINIO_ENDPOINT.strip()
    parsed = urlparse(endpoint if "://" in endpoint else f"https://{endpoint}")
    host = parsed.netloc or parsed.path
    secure = settings.MINIO_SECURE if parsed.scheme != "http" else False
    _client = Minio(
        host,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=secure,
    )
    return _client


def ensure_bucket() -> None:
    client = get_minio_client()
    if not client:
        return
    bucket = settings.MINIO_BUCKET
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)


def upload_bytes(object_key: str, data: bytes, content_type: str) -> str:
    """Sube bytes a MinIO y devuelve URL pública construida."""
    from io import BytesIO

    client = get_minio_client()
    if not client:
        raise RuntimeError("MinIO no está configurado")
    ensure_bucket()
    client.put_object(
        settings.MINIO_BUCKET,
        object_key,
        BytesIO(data),
        length=len(data),
        content_type=content_type or "application/octet-stream",
    )
    base = settings.MINIO_PUBLIC_BASE_URL.rstrip("/")
    return f"{base}/{settings.MINIO_BUCKET}/{object_key}"


def delete_object(object_key: str) -> None:
    client = get_minio_client()
    if not client or not object_key:
        return
    try:
        client.remove_object(settings.MINIO_BUCKET, object_key)
    except Exception:
        pass
