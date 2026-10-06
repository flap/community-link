"""Autenticação dos administradores (RF-019, RF-022).

Dois modos, escolhidos por ``CL_AUTH_MODE``:

* ``supabase`` (produção) — valida o JWT emitido pelo Supabase Auth
  (assinatura, ``iss``, ``aud`` e ``exp``). A assinatura é verificada via
  **JWKS** do projeto (chaves assimétricas) ou, em projetos legados, via
  ``CL_SUPABASE_JWT_SECRET`` (HS256).
* ``static`` (dev/testes) — credencial fixa (``CL_ADMIN_TOKEN``); o usuário
  autenticado é um administrador sintético.

A autorização por comunidade (RF-021) fica em :mod:`app.authz`.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import jwt
from fastapi import Depends, Header, HTTPException, status
from jwt import PyJWKClient

from .config import Settings, get_settings


@dataclass(frozen=True)
class CurrentUser:
    sub: str
    email: str | None


STATIC_USER = CurrentUser(sub="static-admin", email="admin@localhost")


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _bearer(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise _unauthorized("Token ausente")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise _unauthorized("Token ausente")
    return token


# ---------------------------------------------------------------------------
# JWKS com cache (INT-006)
# ---------------------------------------------------------------------------
_jwks_clients: dict[str, tuple[PyJWKClient, float]] = {}


def _jwks_client(settings: Settings) -> PyJWKClient:
    url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    cached = _jwks_clients.get(url)
    now = time.time()
    if cached and now - cached[1] < settings.supabase_jwks_ttl_seconds:
        return cached[0]
    client = PyJWKClient(url, cache_keys=True, lifespan=settings.supabase_jwks_ttl_seconds)
    _jwks_clients[url] = (client, now)
    return client


def decode_supabase_token(token: str, settings: Settings) -> dict:
    """Decodifica e valida um access token do Supabase. Lança HTTP 401 se inválido."""
    if not settings.supabase_url:
        raise HTTPException(status_code=503, detail="CL_SUPABASE_URL não configurado")
    issuer = f"{settings.supabase_url.rstrip('/')}/auth/v1"
    options = {"require": ["exp", "sub"]}
    try:
        if settings.supabase_jwt_secret:
            return jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience=settings.supabase_audience,
                issuer=issuer,
                options=options,
            )
        try:
            signing_key = _jwks_client(settings).get_signing_key_from_jwt(token)
        except jwt.PyJWKClientError as exc:
            # Pode ser rotação de chave: força refetch uma vez.
            _jwks_clients.clear()
            try:
                signing_key = _jwks_client(settings).get_signing_key_from_jwt(token)
            except jwt.PyJWKClientError:
                raise _unauthorized("Chave de assinatura desconhecida") from exc
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "RS256"],
            audience=settings.supabase_audience,
            issuer=issuer,
            options=options,
        )
    except jwt.ExpiredSignatureError as exc:
        raise _unauthorized("Token expirado") from exc
    except jwt.InvalidTokenError as exc:
        raise _unauthorized(f"Token inválido: {exc}") from exc


# ---------------------------------------------------------------------------
# Dependência principal
# ---------------------------------------------------------------------------
def get_current_user(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> CurrentUser:
    """Identifica o usuário autenticado conforme o modo configurado."""
    token = _bearer(authorization)
    if settings.auth_mode == "static":
        if token != settings.admin_token:
            raise _unauthorized("Credencial administrativa inválida")
        return STATIC_USER
    if settings.auth_mode == "supabase":
        claims = decode_supabase_token(token, settings)
        return CurrentUser(sub=str(claims["sub"]), email=claims.get("email"))
    raise HTTPException(status_code=500, detail=f"CL_AUTH_MODE inválido: {settings.auth_mode}")


# Compatibilidade com código da Fase 1.
require_admin = get_current_user
