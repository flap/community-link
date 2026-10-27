"""Rotas públicas — não exigem autenticação (RF-010)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from ..config import get_settings
from ..embeds import build_embed
from ..models import (
    CommunityPublic,
    LinkType,
    SearchResponse,
    SectionWithLinks,
)
from ..repository import (
    DEFAULT_SEARCH_LIMIT,
    MAX_SEARCH_LIMIT,
    NotFoundError,
    get_repository,
)
from ..themes import THEMES

router = APIRouter(tags=["public"])


def _validate_date(value: str | None, field: str) -> str | None:
    """Valida um parâmetro de data (RF-012). Malformado → 422.

    Aceita ``YYYY-MM-DD`` ou ISO-8601 completo. A comparação posterior é
    lexicográfica sobre ``created_at`` (ISO-8601), então basta validar que a
    string é parseável e devolvê-la como veio.
    """
    if value is None:
        return None
    raw = value.strip()
    if not raw:
        return None
    candidate = raw.replace("Z", "+00:00")
    try:
        datetime.fromisoformat(candidate)
    except ValueError:
        try:
            datetime.strptime(raw, "%Y-%m-%d")
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail=f"parâmetro '{field}' não é uma data válida (use YYYY-MM-DD ou ISO-8601)",
            ) from exc
    return raw


def _parse_type(type: str | None) -> LinkType | None:
    """Converte o param ``type`` em LinkType; valor inválido → 422."""
    if type is None or type.strip() == "":
        return None
    try:
        return LinkType(type)
    except ValueError as exc:
        valid = ", ".join(t.value for t in LinkType)
        raise HTTPException(
            status_code=422,
            detail=f"type inválido; valores aceitos: {valid}",
        ) from exc



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


@router.get("/communities/{slug}/search", response_model=SearchResponse)
def search_community(
    slug: str,
    q: str | None = Query(default=None),
    type: str | None = Query(default=None),
    author: str | None = Query(default=None),
    date_from: str | None = Query(default=None, alias="from"),
    date_to: str | None = Query(default=None, alias="to"),
    limit: int = Query(default=DEFAULT_SEARCH_LIMIT, ge=1, le=MAX_SEARCH_LIMIT),
    cursor: str | None = Query(default=None),
) -> SearchResponse:
    """Busca/filtra os links de uma comunidade (RF-012 + RF-013 escopo local).

    Pública. 404 se a comunidade não existe. ``type`` inválido → 422; datas
    malformadas → 422; ``from > to`` coerente porém invertido → resultado vazio.
    """
    repo = get_repository()
    link_type = _parse_type(type)
    _from = _validate_date(date_from, "from")
    _to = _validate_date(date_to, "to")
    try:
        page = repo.search_links_in_community(
            slug,
            q=q,
            type=link_type,
            author=author,
            date_from=_from,
            date_to=_to,
            limit=limit,
            cursor=cursor,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail="Comunidade não encontrada") from exc
    return SearchResponse(
        results=page.items, next_cursor=page.next_cursor, count=len(page.items)
    )


@router.get("/search", response_model=SearchResponse)
def search_global(
    q: str | None = Query(default=None),
    type: str | None = Query(default=None),
    author: str | None = Query(default=None),
    date_from: str | None = Query(default=None, alias="from"),
    date_to: str | None = Query(default=None, alias="to"),
    limit: int = Query(default=DEFAULT_SEARCH_LIMIT, ge=1, le=MAX_SEARCH_LIMIT),
    cursor: str | None = Query(default=None),
) -> SearchResponse:
    """Busca global entre comunidades (RF-013).

    Pública. Cada resultado carrega ``community_slug``/``community_name``
    (indicação da comunidade de origem). ``type`` inválido → 422; datas
    malformadas → 422; ``from > to`` → resultado vazio.
    """
    repo = get_repository()
    link_type = _parse_type(type)
    _from = _validate_date(date_from, "from")
    _to = _validate_date(date_to, "to")
    page = repo.search_links_global(
        q=q,
        type=link_type,
        author=author,
        date_from=_from,
        date_to=_to,
        limit=limit,
        cursor=cursor,
    )
    return SearchResponse(
        results=page.items, next_cursor=page.next_cursor, count=len(page.items)
    )
