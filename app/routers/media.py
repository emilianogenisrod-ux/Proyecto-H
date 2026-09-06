from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import MediaAsset, MediaKind
from app.storage_minio import delete_object, minio_enabled, upload_bytes

router = APIRouter(prefix="/media", tags=["Medios"])

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MEDIA_ROOT = PROJECT_ROOT / "media"

IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
VIDEO_TYPES = {
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/quicktime": ".mov",
}
TEMPLATE_TYPES = {
    **IMAGE_TYPES,
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}


class MediaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    kind: MediaKind
    filename: str
    original_name: str
    content_type: str
    size_bytes: int
    folder: str
    url: str
    storage_key: str | None = None
    storage_url: str | None = None
    bucket: str | None = None
    uploaded_by: str | None
    created_at: datetime


def _require_user(request: Request) -> dict:
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Debe iniciar sesión")
    return user


def ensure_media_dirs() -> None:
    for name in ("images", "videos", "avatars", "templates"):
        (MEDIA_ROOT / name).mkdir(parents=True, exist_ok=True)


def _public_url(asset: MediaAsset) -> str:
    if asset.storage_url:
        return asset.storage_url
    return f"/media/{asset.folder}/{asset.filename}"


def _serialize(asset: MediaAsset) -> MediaRead:
    return MediaRead(
        id=asset.id,
        title=asset.title,
        kind=asset.kind,
        filename=asset.filename,
        original_name=asset.original_name,
        content_type=asset.content_type,
        size_bytes=asset.size_bytes,
        folder=asset.folder,
        url=_public_url(asset),
        storage_key=asset.storage_key,
        storage_url=asset.storage_url,
        bucket=asset.bucket,
        uploaded_by=asset.uploaded_by,
        created_at=asset.created_at,
    )


def _resolve_kind(kind: str, content_type: str) -> tuple[MediaKind, str, str, int]:
    """Returns store_kind, folder, extension, max_bytes."""
    ct = (content_type or "").lower()
    kind_n = (kind or "auto").lower().strip()

    if kind_n == "avatar":
        if ct not in IMAGE_TYPES:
            raise HTTPException(status_code=400, detail="El avatar debe ser una imagen JPG/PNG/WEBP/GIF")
        return MediaKind.image, "avatars", IMAGE_TYPES[ct], settings.MAX_IMAGE_BYTES

    if kind_n == "template":
        if ct not in TEMPLATE_TYPES:
            raise HTTPException(status_code=400, detail="Plantilla no válida (imagen/PDF/DOCX)")
        return MediaKind.template, "templates", TEMPLATE_TYPES[ct], settings.MAX_IMAGE_BYTES

    if kind_n == "image" or (kind_n == "auto" and ct in IMAGE_TYPES):
        if ct not in IMAGE_TYPES:
            raise HTTPException(status_code=400, detail="Imagen no válida. Use JPG/PNG/WEBP/GIF")
        return MediaKind.image, "images", IMAGE_TYPES[ct], settings.MAX_IMAGE_BYTES

    if kind_n == "video" or (kind_n == "auto" and ct in VIDEO_TYPES):
        if ct not in VIDEO_TYPES:
            raise HTTPException(status_code=400, detail="Video no válido. Use MP4/WEBM/MOV")
        return MediaKind.video, "videos", VIDEO_TYPES[ct], settings.MAX_VIDEO_BYTES

    raise HTTPException(
        status_code=400,
        detail="Formato no permitido. Use JPG/PNG/WEBP/GIF, PDF/DOCX o MP4/WEBM/MOV.",
    )


@router.get("", response_model=list[MediaRead])
def list_media(
    request: Request,
    kind: MediaKind | None = None,
    mine: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    user = _require_user(request)
    query = db.query(MediaAsset).order_by(MediaAsset.created_at.desc())
    if kind:
        query = query.filter(MediaAsset.kind == kind)
    if mine or user.get("role") not in {"admin", "director"}:
        query = query.filter(MediaAsset.uploaded_by == user.get("email"))
    return [_serialize(a) for a in query.all()]


@router.post("/upload", response_model=MediaRead, status_code=status.HTTP_201_CREATED)
async def upload_media(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(default=""),
    kind: str = Form(default="auto"),
    db: Session = Depends(get_db),
):
    user = _require_user(request)
    ensure_media_dirs()

    content_type = (file.content_type or "").lower()
    store_kind, folder, ext, max_bytes = _resolve_kind(kind, content_type)

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="El archivo está vacío")
    if len(data) > max_bytes:
        mb = max_bytes // (1024 * 1024)
        raise HTTPException(status_code=400, detail=f"El archivo supera el límite de {mb} MB")

    filename = f"{uuid.uuid4().hex}{ext}"
    storage_key = None
    storage_url = None
    bucket = None

    if minio_enabled():
        storage_key = f"{folder}/{filename}"
        storage_url = upload_bytes(storage_key, data, content_type)
        bucket = settings.MINIO_BUCKET
    else:
        dest = MEDIA_ROOT / folder / filename
        dest.write_bytes(data)

    asset = MediaAsset(
        title=((title or "").strip() or (file.filename or filename))[:200],
        kind=store_kind,
        filename=filename,
        original_name=(file.filename or filename)[:255],
        content_type=content_type,
        size_bytes=len(data),
        folder=folder,
        storage_key=storage_key,
        storage_url=storage_url,
        bucket=bucket,
        uploaded_by=user.get("email"),
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return _serialize(asset)


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media(media_id: int, request: Request, db: Session = Depends(get_db)):
    user = _require_user(request)
    asset = db.get(MediaAsset, media_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    if user.get("role") != "admin" and asset.uploaded_by != user.get("email"):
        raise HTTPException(status_code=403, detail="No puede eliminar este archivo")

    if asset.storage_key and minio_enabled():
        delete_object(asset.storage_key)
    else:
        path = MEDIA_ROOT / asset.folder / asset.filename
        if path.exists():
            path.unlink(missing_ok=True)

    db.delete(asset)
    db.commit()
