"""Rotas públicas — não exigem autenticação (RF-010)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..embeds import build_embed
from ..models import CommunityPublic, SectionWithLinks
from ..repository import get_repository
from ..themes import THEMES

router = APIRouter(tags=["public"])


@router.get("/themes")
def list_themes() -> dict[str, dict]:
    """Lista os temas visuais disponíveis (RF-009)."""
    return THEMES


@router.get("/communities/{slug}", response_model=CommunityPublic)
def get_public_community(slug: str) -> CommunityPublic:
    """Retorna a comunidade com seções e links, para renderização pública."""
    repo = get_repository()
    community = repo.get_community(slug)
    if community is None:
        raise HTTPException(status_code=404, detail="Comunidade não encontrada")

    sections = repo.list_sections(slug)
    links = repo.list_links(slug)

    by_section: dict[str, list] = {}
    for link in links:
        data = link.model_dump()
        # anexa metadados de embed quando aplicável (RF-006 / RN-003)
        data["embed_data"] = build_embed(link.type, link.url) if link.embed else None
        by_section.setdefault(link.section_id, []).append(data)

    sections_with_links = [
        SectionWithLinks(**s.model_dump(), links=by_section.get(s.id, []))
        for s in sections
    ]
    return CommunityPublic(**community.model_dump(), sections=sections_with_links)
