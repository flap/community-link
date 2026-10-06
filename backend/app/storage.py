"""Armazenamento de imagens de destaque / logos (RF-007, RN-005).

Duas estratégias, escolhidas automaticamente pela configuração:

* **S3** quando ``CL_S3_BUCKET`` está definido (produção).
* **Local** (sistema de arquivos) caso contrário (dev/testes), servindo os
  arquivos pela própria API em ``CL_MEDIA_BASE_URL``.

Valida formato (JPEG/PNG/WebP) e tamanho (<= ``CL_MAX_UPLOAD_BYTES``).
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from pathlib import Path
from uuid import uuid4

from .config import Settings, get_settings


class UploadError(Exception):
    """Erro de validação de upload (formato/tamanho)."""


_EXT_BY_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def _validate(content: bytes, content_type: str, settings: Settings) -> str:
    allowed = {t.strip() for t in settings.allowed_image_types.split(",")}
    if content_type not in allowed:
        raise UploadError(
            f"formato '{content_type}' não suportado (aceitos: {', '.join(sorted(allowed))})"
        )
    if len(content) > settings.max_upload_bytes:
        mb = settings.max_upload_bytes / (1024 * 1024)
        raise UploadError(f"arquivo excede o limite de {mb:.0f} MB")
    return _EXT_BY_TYPE.get(content_type, "")


class Storage(ABC):
    @abstractmethod
    def save(self, content: bytes, content_type: str) -> str:
        """Persiste a imagem e retorna a URL pública para uso em ``image_url``."""


class LocalStorage(Storage):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._dir = Path(settings.media_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def save(self, content: bytes, content_type: str) -> str:
        ext = _validate(content, content_type, self._settings)
        name = f"{uuid4().hex}{ext}"
        (self._dir / name).write_bytes(content)
        base = self._settings.media_base_url.rstrip("/")
        return f"{base}/{name}"

    def path_for(self, name: str) -> Path:
        return self._dir / name


class S3Storage(Storage):  # pragma: no cover - depende da AWS
    def __init__(self, settings: Settings) -> None:
        import boto3

        self._settings = settings
        self._bucket = settings.s3_bucket
        self._client = boto3.client("s3", region_name=settings.aws_region)

    def save(self, content: bytes, content_type: str) -> str:
        ext = _validate(content, content_type, self._settings)
        key = f"links/{uuid4().hex}{ext}"
        self._client.put_object(
            Bucket=self._bucket, Key=key, Body=content, ContentType=content_type
        )
        return f"https://{self._bucket}.s3.{self._settings.aws_region}.amazonaws.com/{key}"


_storage: Storage | None = None


def get_storage() -> Storage:
    global _storage
    if _storage is not None:
        return _storage
    settings = get_settings()
    _storage = S3Storage(settings) if settings.s3_bucket else LocalStorage(settings)
    return _storage
