"""Autenticação simplificada do MVP (RF-011).

ATENÇÃO: solução TEMPORÁRIA para testes. A área administrativa é protegida
por uma credencial fixa (bearer token) definida em ``CL_ADMIN_TOKEN``.
Deve ser substituída por autenticação completa antes de produção aberta.
"""

from fastapi import Depends, Header, HTTPException, status

from .config import Settings, get_settings


def require_admin(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    """Valida o header ``Authorization: Bearer <token>`` contra a credencial fixa."""
    expected = f"Bearer {settings.admin_token}"
    if not authorization or authorization != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credencial administrativa inválida ou ausente",
            headers={"WWW-Authenticate": "Bearer"},
        )
