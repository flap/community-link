"""Rotas públicas — não exigem autenticação (RF-010)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..config import get_settings
from ..embeds import build_embed
from ..models import CommunityPublic, SectionWithLinks
from ..repository import get_repository
from ..themes import THEMES

router = APIRouter(tags=["public"])


@router.get("/themes")
def list_themes() -> dict[str, dict]:
    """Lista os temas visuais disponíveis (RF-009)."""
    return THEMES


@router.get("/media/{name}")
def get_media(name: str) -> FileResponse:
    """Serve imagens enviadas localmente em dev (foto de destaque — RF-007).

    Em produção, as imagens são servidas diretamente pelo S3/CloudFront e
    esta rota não é utilizada.
    """
    settings = get_settings()
    if settings.s3_bucket:
        raise HTTPException(status_code=404, detail="mídia servida via S3")
    # evita path traversal: aceita apenas o nome do arquivo
    if "/" in name or "\\" in name or ".." in name:
        raise HTTPException(status_code=400, detail="nome inválido")
    from ..storage import LocalStorage, get_storage

    storage = get_storage()
    if not isinstance(storage, LocalStorage):
        raise HTTPException(status_code=404, detail="mídia indisponível")
    path = storage.path_for(name)
    if not path.exists():
        raise HTTPException(status_code=404, detail="imagem não encontrada")
    return FileResponse(path)


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
