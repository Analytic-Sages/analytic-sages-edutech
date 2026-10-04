from __future__ import annotations

import logging
import re
import uuid
from pathlib import Path

import httpx
from fastapi import HTTPException, UploadFile, status

from app.core.config import Settings

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}

# Downloadable lesson resources (PDFs, slides, datasets, source code, archives).
ALLOWED_DOCUMENT_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.ms-powerpoint": ".ppt",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/zip": ".zip",
    "application/x-zip-compressed": ".zip",
    "application/gzip": ".gz",
    "text/csv": ".csv",
    "text/plain": ".txt",
    "text/x-python": ".py",
    "text/x-sql": ".sql",
    "application/x-ipynb+json": ".ipynb",
    "application/json": ".json",
}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_DOCUMENT_BYTES = 25 * 1024 * 1024
SAFE_NAME = re.compile(r"^[0-9a-f-]{36}\.(jpg|png|webp|gif|pdf|ppt|pptx|xls|xlsx|zip|gz|csv|txt|py|sql|ipynb|json)$")

logger = logging.getLogger(__name__)


class StorageService:
    """Uploads images to Supabase Storage when configured; otherwise falls back to local disk.

    Local disk only survives deploys if STORAGE_DIR points at a persistent volume/disk
    (e.g. a Render Persistent Disk mount path). Plain ephemeral disk is dev-only — most
    hosts wipe it on every deploy, which silently breaks already-published articles.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.is_live = bool(settings.supabase_url and settings.supabase_service_role_key)
        if not self.is_live:
            self.root = Path(settings.storage_dir).resolve()
            self.root.mkdir(parents=True, exist_ok=True)

    def public_url(self, filename: str) -> str:
        return f"/api/v1/media/{filename}"

    def resolve_file(self, filename: str) -> Path:
        if self.is_live or not SAFE_NAME.fullmatch(filename):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
        path = (self.root / filename).resolve()
        if not str(path).startswith(str(self.root)) or not path.is_file():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
        return path

    async def save_image(self, upload: UploadFile) -> str:
        content_type = (upload.content_type or "").lower()
        suffix = ALLOWED_IMAGE_TYPES.get(content_type)
        if not suffix:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Upload a JPG, PNG, WebP, or GIF image",
            )
        data = await self._read_upload(upload, MAX_UPLOAD_BYTES, "Image must be 5MB or smaller")
        return await self._store(suffix, data, content_type)

    async def save_document(self, upload: UploadFile) -> str:
        """Persist a downloadable lesson resource (PDF, slides, dataset, source, zip)."""
        content_type = (upload.content_type or "").lower()
        suffix = ALLOWED_DOCUMENT_TYPES.get(content_type)
        if not suffix:
            # Fall back to the filename extension when the browser sends a generic type.
            name_suffix = Path(upload.filename or "").suffix.lower()
            if name_suffix in set(ALLOWED_DOCUMENT_TYPES.values()):
                suffix = name_suffix
        if not suffix:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Upload a PDF, slides, spreadsheet, dataset, source file, or zip archive",
            )
        data = await self._read_upload(
            upload, MAX_DOCUMENT_BYTES, "File must be 25MB or smaller"
        )
        return await self._store(suffix, data, content_type or "application/octet-stream")

    async def _read_upload(self, upload: UploadFile, max_bytes: int, too_large_detail: str) -> bytes:
        data = await upload.read()
        if not data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")
        if len(data) > max_bytes:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=too_large_detail)
        return data

    async def _store(self, suffix: str, data: bytes, content_type: str) -> str:
        filename = f"{uuid.uuid4()}{suffix}"
        if self.is_live:
            return await self._upload_to_supabase(filename, data, content_type)
        path = self.root / filename
        path.write_bytes(data)
        return self.public_url(filename)

    async def _upload_to_supabase(self, filename: str, data: bytes, content_type: str) -> str:
        base = (self.settings.supabase_url or "").rstrip("/")
        bucket = self.settings.supabase_storage_bucket
        key = self.settings.supabase_service_role_key
        upload_url = f"{base}/storage/v1/object/{bucket}/{filename}"
        headers = {
            "Authorization": f"Bearer {key}",
            "apikey": key or "",
            "Content-Type": content_type,
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(upload_url, headers=headers, content=data)
        except httpx.HTTPError as exc:
            logger.exception("Supabase Storage upload failed")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, detail="Image upload failed"
            ) from exc
        if response.status_code >= 400:
            logger.error("Supabase Storage upload rejected: %s %s", response.status_code, response.text)
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Image upload failed")
        return f"{base}/storage/v1/object/public/{bucket}/{filename}"
