"""Testes da sugestão de slug (RF-001): normalização, disponibilidade e endpoint."""

import os
import tempfile

os.environ.setdefault("CL_USE_IN_MEMORY_STORE", "true")
os.environ.setdefault("CL_AUTH_MODE", "static")
os.environ.setdefault("CL_ADMIN_TOKEN", "test-token")
os.environ.setdefault("CL_MEDIA_DIR", tempfile.mkdtemp(prefix="cl-media-"))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.slugs import SLUG_MAX_LENGTH, resolve_available_slug, slugify  # noqa: E402

client = TestClient(app)
AUTH = {"Authorization": "Bearer test-token"}


# -- Normalização (função pura) ---------------------------------------------
def test_slugify_basico():
    assert slugify("AWS Community BR") == "aws-community-br"


def test_slugify_acentos():
    assert slugify("Café com Leite") == "cafe-com-leite"


def test_slugify_simbolos_e_colapso():
    assert slugify("A!!!B   C") == "a-b-c"


def test_slugify_vazio_e_so_simbolos():
    assert slugify("") == ""
    assert slugify("@#$") == ""


def test_slugify_truncagem_60():
    out = slugify("a " * 100)  # muitos 'a' separados por espaço
    assert len(out) <= SLUG_MAX_LENGTH
    assert not out.endswith("-")
    import re

    from app.slugs import SLUG_PATTERN

    assert re.match(SLUG_PATTERN, out)


# -- Disponibilidade (função pura) ------------------------------------------
def test_resolve_disponivel_sem_colisao():
    assert resolve_available_slug("aws-sp", lambda s: False) == "aws-sp"


def test_resolve_com_sufixo():
    taken = {"aws-sp"}
    assert resolve_available_slug("aws-sp", lambda s: s in taken) == "aws-sp-2"
    taken.add("aws-sp-2")
    assert resolve_available_slug("aws-sp", lambda s: s in taken) == "aws-sp-3"


def test_resolve_respeita_max_length():
    base = "a" * 59
    out = resolve_available_slug(base, lambda s: s == base)
    assert len(out) <= SLUG_MAX_LENGTH
    assert out.endswith("-2")
    assert not out[:-2].endswith("-")


def test_resolve_reservado_ocupado():
    # 'api' é reservado -> nunca sugerido; deve pular para 'api-2'
    assert resolve_available_slug("api", lambda s: False) == "api-2"


# -- Endpoint ----------------------------------------------------------------
def test_slug_suggestion_requires_auth():
    r = client.get("/api/admin/communities/slug-suggestion?name=X")
    assert r.status_code == 401


def test_slug_suggestion_ok():
    r = client.get(
        "/api/admin/communities/slug-suggestion?name=AWS Community BR", headers=AUTH
    )
    assert r.status_code == 200, r.text
    assert r.json() == {"slug": "aws-community-br"}


def test_slug_suggestion_colisao():
    client.post(
        "/api/admin/communities",
        headers=AUTH,
        json={"name": "Já existe", "slug": "slug-colisao"},
    )
    r = client.get(
        "/api/admin/communities/slug-suggestion?name=Slug Colisao", headers=AUTH
    )
    assert r.status_code == 200, r.text
    assert r.json() == {"slug": "slug-colisao-2"}


def test_slug_suggestion_nao_captura_rota_dinamica():
    # a rota estática deve vencer a dinâmica {slug}: resposta tem shape {"slug": ...}
    r = client.get(
        "/api/admin/communities/slug-suggestion?name=Rota Estatica", headers=AUTH
    )
    assert r.status_code == 200, r.text
    assert "slug" in r.json()
    assert r.json()["slug"] == "rota-estatica"


def test_slug_suggestion_name_vazio():
    r = client.get("/api/admin/communities/slug-suggestion?name=", headers=AUTH)
    assert r.status_code == 200, r.text
    assert r.json() == {"slug": ""}
