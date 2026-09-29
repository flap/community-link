"""Community Link — aplicação FastAPI (MVP Fase 1).

Expõe rotas públicas (renderização da página) e administrativas (edição),
servidas sob o domínio ``awscommunity.com.br`` via CloudFront + API Gateway.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .config import get_settings
from .routers import admin, public

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="Portal agregador de links para comunidades (SaaS multi-tenant).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas de API sob /api (CloudFront roteia /api/* para o API Gateway)
app.include_router(public.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/api/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name, "version": __version__}


# Handler para AWS Lambda (API Gateway) — usado no deploy serverless.
try:  # pragma: no cover - só relevante no ambiente Lambda
    from mangum import Mangum

    handler = Mangum(app)
except Exception:  # noqa: BLE001
    handler = None
