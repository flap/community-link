"""Autorização por comunidade (RF-021, RN-006, RN-007).

A autenticação diz *quem* é o usuário (:mod:`app.auth`); este módulo decide
*o que* ele pode fazer: apenas administradores de uma comunidade podem
alterá-la. Convites pendentes por e-mail são efetivados no primeiro acesso
do convidado.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status

from .auth import CurrentUser, get_current_user
from .repository import NotFoundError, Repository, get_repository


def ensure_community_admin(repo: Repository, slug: str, user: CurrentUser) -> None:
    """Garante que ``user`` administra ``slug``; efetiva convite pendente se houver."""
    if repo.get_community(slug) is None:
        raise HTTPException(status_code=404, detail="Comunidade não encontrada")
    if repo.is_admin(slug, user.sub):
        return
    if user.email and repo.has_invite(slug, user.email):
        repo.add_admin(slug, user.sub, user.email)
        try:
            repo.remove_invite(slug, user.email)
        except NotFoundError:
            pass
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Você não administra esta comunidade",
    )


def community_admin(
    slug: str,
    user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Dependência FastAPI para rotas ``/admin/communities/{slug}/...``."""
    ensure_community_admin(get_repository(), slug, user)
    return user
