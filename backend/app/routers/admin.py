"""Rotas administrativas — exigem credencial fixa (RF-011).

Cobrem cadastro/edição de comunidades (RF-001), seções (RF-003) e links
ricos com emoji/foto/embed (RF-004..RF-007). Publicação é imediata (RF-008).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..auth import require_admin
from ..models import (
    Community,
    CommunityCreate,
    CommunityUpdate,
    Link,
    LinkCreate,
    LinkUpdate,
    ReorderRequest,
    Section,
    SectionCreate,
    SectionUpdate,
)
from ..repository import ConflictError, NotFoundError, get_repository
from ..themes import theme_exists

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _repo():
    return get_repository()


# -- Communities ------------------------------------------------------------
@router.get("/communities", response_model=list[Community])
def list_communities() -> list[Community]:
    return _repo().list_communities()


@router.post("/communities", response_model=Community, status_code=201)
def create_community(data: CommunityCreate) -> Community:
    if not theme_exists(data.theme):
        raise HTTPException(status_code=400, detail=f"tema '{data.theme}' inválido")
    try:
        return _repo().create_community(data)
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/communities/{slug}", response_model=Community)
def get_community(slug: str) -> Community:
    community = _repo().get_community(slug)
    if community is None:
        raise HTTPException(status_code=404, detail="Comunidade não encontrada")
    return community


@router.patch("/communities/{slug}", response_model=Community)
def update_community(slug: str, data: CommunityUpdate) -> Community:
    if data.theme is not None and not theme_exists(data.theme):
        raise HTTPException(status_code=400, detail=f"tema '{data.theme}' inválido")
    try:
        return _repo().update_community(slug, data)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/communities/{slug}", status_code=204)
def delete_community(slug: str) -> None:
    try:
        _repo().delete_community(slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# -- Sections ---------------------------------------------------------------
@router.get("/communities/{slug}/sections", response_model=list[Section])
def list_sections(slug: str) -> list[Section]:
    try:
        return _repo().list_sections(slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/communities/{slug}/sections", response_model=Section, status_code=201)
def create_section(slug: str, data: SectionCreate) -> Section:
    try:
        return _repo().create_section(slug, data)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/communities/{slug}/sections/{section_id}", response_model=Section)
def update_section(slug: str, section_id: str, data: SectionUpdate) -> Section:
    try:
        return _repo().update_section(slug, section_id, data)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/communities/{slug}/sections/{section_id}", status_code=204)
def delete_section(slug: str, section_id: str) -> None:
    try:
        _repo().delete_section(slug, section_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/communities/{slug}/sections/reorder", response_model=list[Section])
def reorder_sections(slug: str, data: ReorderRequest) -> list[Section]:
    """Reordena as seções conforme a lista de IDs (RF-018)."""
    try:
        return _repo().reorder_sections(slug, data.ordered_ids)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# -- Links ------------------------------------------------------------------
@router.get("/communities/{slug}/links", response_model=list[Link])
def list_links(slug: str) -> list[Link]:
    try:
        return _repo().list_links(slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/communities/{slug}/links", response_model=Link, status_code=201)
def create_link(slug: str, data: LinkCreate) -> Link:
    try:
        return _repo().create_link(slug, data)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/communities/{slug}/links/{link_id}", response_model=Link)
def update_link(slug: str, link_id: str, data: LinkUpdate) -> Link:
    try:
        return _repo().update_link(slug, link_id, data)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/communities/{slug}/links/{link_id}", status_code=204)
def delete_link(slug: str, link_id: str) -> None:
    try:
        _repo().delete_link(slug, link_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/communities/{slug}/sections/{section_id}/links/reorder", response_model=list[Link])
def reorder_links(slug: str, section_id: str, data: ReorderRequest) -> list[Link]:
    """Reordena os links de uma seção conforme a lista de IDs (RF-018)."""
    try:
        return _repo().reorder_links(slug, section_id, data.ordered_ids)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
