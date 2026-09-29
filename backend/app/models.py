"""Modelos Pydantic do domínio Community Link (Fase 1)."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return uuid4().hex[:12]


class LinkType(str, Enum):
    """Tipos de link suportados (RF-004)."""

    video = "video"
    site = "site"
    calendario = "calendario"
    pessoa = "pessoa"
    linkedin = "linkedin"
    instagram = "instagram"
    tiktok = "tiktok"
    builder_center = "builder_center"
    meetup = "meetup"


# ---------------------------------------------------------------------------
# Link
# ---------------------------------------------------------------------------
class LinkBase(BaseModel):
    type: LinkType
    title: str = Field(min_length=1, max_length=140)
    url: str = Field(min_length=1, max_length=2048)
    emoji: str | None = Field(default=None, max_length=8)
    image_url: str | None = Field(default=None, max_length=2048)
    author: str | None = Field(default=None, max_length=140)
    embed: bool = False
    order: int = 0


class LinkCreate(LinkBase):
    section_id: str


class LinkUpdate(BaseModel):
    type: LinkType | None = None
    title: str | None = Field(default=None, min_length=1, max_length=140)
    url: str | None = Field(default=None, min_length=1, max_length=2048)
    emoji: str | None = Field(default=None, max_length=8)
    image_url: str | None = Field(default=None, max_length=2048)
    author: str | None = Field(default=None, max_length=140)
    embed: bool | None = None
    order: int | None = None
    section_id: str | None = None


class Link(LinkBase):
    id: str = Field(default_factory=_new_id)
    section_id: str
    created_at: str = Field(default_factory=_now_iso)


# ---------------------------------------------------------------------------
# Section
# ---------------------------------------------------------------------------
class SectionBase(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    order: int = 0


class SectionCreate(SectionBase):
    pass


class SectionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    order: int | None = None


class Section(SectionBase):
    id: str = Field(default_factory=_new_id)


# ---------------------------------------------------------------------------
# Community
# ---------------------------------------------------------------------------
SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


class CommunityBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str = Field(min_length=1, max_length=60)
    description: str | None = Field(default=None, max_length=500)
    theme: str = "default"
    logo_url: str | None = Field(default=None, max_length=2048)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        import re

        v = v.strip().lower()
        if not re.match(SLUG_PATTERN, v):
            raise ValueError(
                "slug deve conter apenas letras minúsculas, números e hífens"
            )
        reserved = {"api", "admin", "static", "assets", "www"}
        if v in reserved:
            raise ValueError(f"slug '{v}' é reservado")
        return v


class CommunityCreate(CommunityBase):
    pass


class CommunityUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    theme: str | None = None
    logo_url: str | None = Field(default=None, max_length=2048)


class Community(CommunityBase):
    created_at: str = Field(default_factory=_now_iso)


class PublicLink(Link):
    """Link enriquecido para a página pública, com metadados de embed (RF-006)."""

    embed_data: dict | None = None


class SectionWithLinks(Section):
    links: list[PublicLink] = []


class CommunityPublic(Community):
    """Comunidade com suas seções e links, para renderização pública (RF-010)."""

    sections: list[SectionWithLinks] = []


CommunityPublic.model_rebuild()
