"""Rotas administrativas — exigem usuário autenticado (RF-019/RF-022) e, para
operações sobre uma comunidade, que o usuário seja seu administrador (RF-021).

Cobrem cadastro/edição de comunidades (RF-001, RF-015), seções (RF-003,
RF-016), links ricos (RF-004..RF-007, RF-017), reordenação (RF-018) e gestão
de administradores/convites (RF-002, RF-021). Publicação é imediata (RF-008).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from ..auth import CurrentUser, get_current_user
from ..authz import community_admin
from ..config import Settings, get_settings
from ..models import (
    Community,
    CommunityAdmin,
    CommunityAdmins,
    CommunityCreate,
    CommunityUpdate,
    InviteRequest,
    Link,
    LinkCreate,
    LinkUpdate,
    MeResponse,
    ReorderRequest,
    Section,
    SectionCreate,
    SectionUpdate,
)
from ..repository import ConflictError, NotFoundError, get_repository
from ..storage import UploadError, get_storage
from ..themes import theme_exists

router = APIRouter(prefix="/admin", tags=["admin"])


def _repo():
    return get_repository()


def _not_found(exc: Exception) -> HTTPException:
    return HTTPException(status_code=404, detail=str(exc))


# -- Sessão ------------------------------------------------------------------
@router.get("/me", response_model=MeResponse)
def me(
    user: CurrentUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> MeResponse:
    return MeResponse(sub=user.sub, email=user.email, auth_mode=settings.auth_mode)


# -- Upload de imagem (RF-007 / RN-005) ------------------------------------
@router.post("/uploads", status_code=201)
async def upload_image(
    file: UploadFile, _: CurrentUser = Depends(get_current_user)
) -> dict[str, str]:
    """Recebe uma imagem (JPEG/PNG/WebP, <=5MB) e retorna a URL pública."""
    content = await file.read()
    try:
        url = get_storage().save(content, file.content_type or "")
    except UploadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"image_url": url}


# -- Communities ------------------------------------------------------------
@router.get("/communities", response_model=list[Community])
def list_communities(user: CurrentUser = Depends(get_current_user)) -> list[Community]:
    """Lista apenas as comunidades administradas pelo usuário (RF-021)."""
    return _repo().list_user_communities(user.sub)


@router.post("/communities", response_model=Community, status_code=201)
def create_community(
    data: CommunityCreate, user: CurrentUser = Depends(get_current_user)
) -> Community:
    if not theme_exists(data.theme):
        raise HTTPException(status_code=400, detail=f"tema '{data.theme}' inválido")
    repo = _repo()
    try:
        community = repo.create_community(data)
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    # quem cria vira administrador (RF-021)
    repo.add_admin(community.slug, user.sub, user.email)
    return community


@router.get("/communities/{slug}", response_model=Community)
def get_community(slug: str, _: CurrentUser = Depends(community_admin)) -> Community:
    community = _repo().get_community(slug)
    if community is None:
        raise HTTPException(status_code=404, detail="Comunidade não encontrada")
    return community


@router.patch("/communities/{slug}", response_model=Community)
def update_community(
    slug: str, data: CommunityUpdate, _: CurrentUser = Depends(community_admin)
) -> Community:
    if data.theme is not None and not theme_exists(data.theme):
        raise HTTPException(status_code=400, detail=f"tema '{data.theme}' inválido")
    try:
        return _repo().update_community(slug, data)
    except NotFoundError as exc:
        raise _not_found(exc) from exc


@router.delete("/communities/{slug}", status_code=204)
def delete_community(slug: str, _: CurrentUser = Depends(community_admin)) -> None:
    try:
        _repo().delete_community(slug)
    except NotFoundError as exc:
        raise _not_found(exc) from exc


# -- Administradores e convites (RF-002 / RF-021) ---------------------------
@router.get("/communities/{slug}/admins", response_model=CommunityAdmins)
def list_admins(slug: str, _: CurrentUser = Depends(community_admin)) -> CommunityAdmins:
    repo = _repo()
    return CommunityAdmins(admins=repo.list_admins(slug), invites=repo.list_invites(slug))


@router.post("/communities/{slug}/admins", response_model=CommunityAdmins, status_code=201)
def invite_admin(
    slug: str, data: InviteRequest, user: CurrentUser = Depends(community_admin)
) -> CommunityAdmins:
    """Convida um administrador por e-mail; efetivado no primeiro acesso do convidado."""
    repo = _repo()
    email = data.email.strip().lower()
    if any((a.email or "").lower() == email for a in repo.list_admins(slug)):
        raise HTTPException(status_code=409, detail="usuário já é administrador")
    try:
        repo.add_invite(slug, email, invited_by=user.sub)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return CommunityAdmins(admins=repo.list_admins(slug), invites=repo.list_invites(slug))


@router.delete("/communities/{slug}/admins/{sub}", status_code=204)
def remove_admin(slug: str, sub: str, _: CurrentUser = Depends(community_admin)) -> None:
    repo = _repo()
    admins = repo.list_admins(slug)
    if len(admins) <= 1 and any(a.sub == sub for a in admins):
        # RN-007: a comunidade não pode ficar sem administradores
        raise HTTPException(status_code=409, detail="não é possível remover o último administrador")
    try:
        repo.remove_admin(slug, sub)
    except NotFoundError as exc:
        raise _not_found(exc) from exc


@router.delete("/communities/{slug}/invites/{email}", status_code=204)
def remove_invite(slug: str, email: str, _: CurrentUser = Depends(community_admin)) -> None:
    try:
        _repo().remove_invite(slug, email)
    except NotFoundError as exc:
        raise _not_found(exc) from exc


# -- Sections ---------------------------------------------------------------
@router.get("/communities/{slug}/sections", response_model=list[Section])
def list_sections(slug: str, _: CurrentUser = Depends(community_admin)) -> list[Section]:
    try:
        return _repo().list_sections(slug)
    except NotFoundError as exc:
        raise _not_found(exc) from exc


@router.post("/communities/{slug}/sections", response_model=Section, status_code=201)
def create_section(
    slug: str, data: SectionCreate, _: CurrentUser = Depends(community_admin)
) -> Section:
    try:
        return _repo().create_section(slug, data)
    except NotFoundError as exc:
        raise _not_found(exc) from exc


@router.put("/communities/{slug}/sections/reorder", response_model=list[Section])
def reorder_sections(
    slug: str, data: ReorderRequest, _: CurrentUser = Depends(community_admin)
) -> list[Section]:
    """Reordena as seções conforme a lista de IDs (RF-018)."""
    try:
        return _repo().reorder_sections(slug, data.ordered_ids)
    except NotFoundError as exc:
        raise _not_found(exc) from exc


@router.patch("/communities/{slug}/sections/{section_id}", response_model=Section)
def update_section(
    slug: str, section_id: str, data: SectionUpdate, _: CurrentUser = Depends(community_admin)
) -> Section:
    try:
        return _repo().update_section(slug, section_id, data)
    except NotFoundError as exc:
        raise _not_found(exc) from exc


@router.delete("/communities/{slug}/sections/{section_id}", status_code=204)
def delete_section(slug: str, section_id: str, _: CurrentUser = Depends(community_admin)) -> None:
    try:
        _repo().delete_section(slug, section_id)
    except NotFoundError as exc:
        raise _not_found(exc) from exc


@router.put(
    "/communities/{slug}/sections/{section_id}/links/reorder", response_model=list[Link]
)
def reorder_links(
    slug: str, section_id: str, data: ReorderRequest, _: CurrentUser = Depends(community_admin)
) -> list[Link]:
    """Reordena os links de uma seção conforme a lista de IDs (RF-018)."""
    try:
        return _repo().reorder_links(slug, section_id, data.ordered_ids)
    except NotFoundError as exc:
        raise _not_found(exc) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


# -- Links ------------------------------------------------------------------
@router.get("/communities/{slug}/links", response_model=list[Link])
def list_links(slug: str, _: CurrentUser = Depends(community_admin)) -> list[Link]:
    try:
        return _repo().list_links(slug)
    except NotFoundError as exc:
        raise _not_found(exc) from exc


@router.post("/communities/{slug}/links", response_model=Link, status_code=201)
def create_link(slug: str, data: LinkCreate, _: CurrentUser = Depends(community_admin)) -> Link:
    try:
        return _repo().create_link(slug, data)
    except NotFoundError as exc:
        raise _not_found(exc) from exc


@router.patch("/communities/{slug}/links/{link_id}", response_model=Link)
def update_link(
    slug: str, link_id: str, data: LinkUpdate, _: CurrentUser = Depends(community_admin)
) -> Link:
    try:
        return _repo().update_link(slug, link_id, data)
    except NotFoundError as exc:
        raise _not_found(exc) from exc


@router.delete("/communities/{slug}/links/{link_id}", status_code=204)
def delete_link(slug: str, link_id: str, _: CurrentUser = Depends(community_admin)) -> None:
    try:
        _repo().delete_link(slug, link_id)
    except NotFoundError as exc:
        raise _not_found(exc) from exc
