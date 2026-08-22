from __future__ import annotations

import re
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import Settings

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
SAFE_NAME = re.compile(r"^[0-9a-f-]{36}\.(jpg|png|webp|gif)$")


class StorageService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.root = Path(settings.storage_dir).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def public_url(self, filename: str) -> str:
        return f"/api/v1/media/{filename}"

    def resolve_file(self, filename: str) -> Path:
        if not SAFE_NAME.fullmatch(filename):
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
        data = await upload.read()
        if not data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")
        if len(data) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image must be 5MB or smaller")
        filename = f"{uuid.uuid4()}{suffix}"
        path = self.root / filename
        path.write_bytes(data)
        return self.public_url(filename)
