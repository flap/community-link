"""Testes de busca e filtros (RF-012 / RF-013 — Fase 2b).

Rodam contra o InMemoryRepository (CL_USE_IN_MEMORY_STORE=true), que SIMULA os
GSIs implementando o mesmo contrato ``search_links_*`` que o DynamoDBRepository.
"""

import os
import tempfile

os.environ.setdefault("CL_USE_IN_MEMORY_STORE", "true")
os.environ.setdefault("CL_AUTH_MODE", "static")
os.environ.setdefault("CL_ADMIN_TOKEN", "test-token")
os.environ.setdefault("CL_MEDIA_DIR", tempfile.mkdtemp(prefix="cl-media-"))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.repository import get_repository  # noqa: E402

client = TestClient(app)
AUTH = {"Authorization": "Bearer test-token"}


# ---------------------------------------------------------------------------
# Fixture helper: cria comunidade/seção/links com created_at controlado.
# Não altera o contrato público de LinkCreate — injeta created_at via
# model_copy direto no item armazenado pelo repositório (override de teste).
# ---------------------------------------------------------------------------
def _make_community(slug: str, name: str) -> str:
    r = client.post(
        "/api/admin/communities",
        headers=AUTH,
        json={"name": name, "slug": slug, "theme": "aws"},
    )
    assert r.status_code == 201, r.text
    s = client.post(
        f"/api/admin/communities/{slug}/sections",
        headers=AUTH,
        json={"title": "Seção", "order": 0},
    )
    assert s.status_code == 201, s.text
    return s.json()["id"]


def _add_link(slug, section_id, *, type, title, url, author=None, created_at=None):
    payload = {"section_id": section_id, "type": type, "title": title, "url": url}
    if author is not None:
        payload["author"] = author
    r = client.post(
        f"/api/admin/communities/{slug}/links", headers=AUTH, json=payload
    )
    assert r.status_code == 201, r.text
    link = r.json()
    if created_at is not None:
        # Override de teste do created_at diretamente no repositório in-memory.
        repo = get_repository()
        stored = repo._links[slug][link["id"]]
        repo._links[slug][link["id"]] = stored.model_copy(
            update={"created_at": created_at}
        )
    return link


# ===========================================================================
# 1. Filtro por tipo
# ===========================================================================
def test_filter_by_type():
    sid = _make_community("c-type", "C Type")
    _add_link("c-type", sid, type="video", title="V1", url="https://v1")
    _add_link("c-type", sid, type="site", title="S1", url="https://s1")
    r = client.get("/api/communities/c-type/search", params={"type": "video"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["count"] == 1
    assert body["results"][0]["link"]["type"] == "video"


# ===========================================================================
# 2. Filtro por intervalo de data (inclusivo nas bordas)
# ===========================================================================
def test_filter_by_date_range_inclusive():
    sid = _make_community("c-date", "C Date")
    _add_link("c-date", sid, type="site", title="old", url="https://o",
              created_at="2026-01-01T00:00:00+00:00")
    _add_link("c-date", sid, type="site", title="edge-from", url="https://a",
              created_at="2026-06-01T00:00:00+00:00")
    _add_link("c-date", sid, type="site", title="edge-to", url="https://b",
              created_at="2026-06-30T23:00:00+00:00")
    _add_link("c-date", sid, type="site", title="future", url="https://f",
              created_at="2026-12-31T00:00:00+00:00")
    r = client.get(
        "/api/communities/c-date/search",
        params={"from": "2026-06-01", "to": "2026-06-30"},
    )
    assert r.status_code == 200, r.text
    titles = {res["link"]["title"] for res in r.json()["results"]}
    assert titles == {"edge-from", "edge-to"}


# ===========================================================================
# 3. Busca textual case-insensitive (title/url/author)
# ===========================================================================
def test_text_search_case_insensitive():
    sid = _make_community("c-text", "C Text")
    _add_link("c-text", sid, type="site", title="Palestra AWS", url="https://x")
    _add_link("c-text", sid, type="site", title="Outro", url="https://y")
    r = client.get("/api/communities/c-text/search", params={"q": "aws"})
    assert r.status_code == 200, r.text
    assert r.json()["count"] == 1
    assert r.json()["results"][0]["link"]["title"] == "Palestra AWS"


# ===========================================================================
# 4. Combinação AND de critérios
# ===========================================================================
def test_combination_and():
    sid = _make_community("c-and", "C And")
    _add_link("c-and", sid, type="video", title="Palestra AWS", url="https://x",
              created_at="2026-05-10T00:00:00+00:00")
    _add_link("c-and", sid, type="site", title="Palestra AWS", url="https://y",
              created_at="2026-05-10T00:00:00+00:00")
    _add_link("c-and", sid, type="video", title="Outra", url="https://z",
              created_at="2026-05-10T00:00:00+00:00")
    r = client.get(
        "/api/communities/c-and/search",
        params={"type": "video", "q": "palestra", "from": "2026-05-01", "to": "2026-05-31"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["count"] == 1
    assert r.json()["results"][0]["link"]["url"] == "https://x"


# ===========================================================================
# 5. Filtro por autor normalizado + sparse (link sem autor não casa)
# ===========================================================================
def test_filter_by_author_normalized_and_sparse():
    sid = _make_community("c-author", "C Author")
    _add_link("c-author", sid, type="site", title="A", url="https://a", author="Fulano")
    _add_link("c-author", sid, type="site", title="B", url="https://b", author=None)
    # normalização: " Fulano " / "fulano" devem casar o autor "Fulano"
    r = client.get("/api/communities/c-author/search", params={"author": "  fulano  "})
    assert r.status_code == 200, r.text
    assert r.json()["count"] == 1
    assert r.json()["results"][0]["link"]["title"] == "A"


# ===========================================================================
# 6. Escopo comunidade vs global, com community_slug/name
# ===========================================================================
def test_scope_community_vs_global():
    a = _make_community("c-a", "Comunidade A")
    b = _make_community("c-b", "Comunidade B")
    _add_link("c-a", a, type="site", title="AWS na A", url="https://a")
    _add_link("c-b", b, type="site", title="AWS na B", url="https://b")

    ra = client.get("/api/communities/c-a/search", params={"q": "aws"})
    assert ra.status_code == 200
    assert {r["community_slug"] for r in ra.json()["results"]} == {"c-a"}

    rg = client.get("/api/search", params={"q": "aws"})
    assert rg.status_code == 200
    by_slug = {r["community_slug"]: r["community_name"] for r in rg.json()["results"]}
    # A busca global cruza todas as comunidades (o repositório in-memory é um
    # singleton compartilhado entre testes). Verifica que A e B estão presentes
    # com o nome correto, sem exigir exclusividade.
    assert by_slug.get("c-a") == "Comunidade A"
    assert by_slug.get("c-b") == "Comunidade B"


# ===========================================================================
# 7. Ordenação por created_at desc
# ===========================================================================
def test_ordering_created_at_desc():
    sid = _make_community("c-order", "C Order")
    _add_link("c-order", sid, type="site", title="oldest", url="https://1",
              created_at="2026-01-01T00:00:00+00:00")
    _add_link("c-order", sid, type="site", title="newest", url="https://3",
              created_at="2026-03-01T00:00:00+00:00")
    _add_link("c-order", sid, type="site", title="middle", url="https://2",
              created_at="2026-02-01T00:00:00+00:00")
    r = client.get("/api/communities/c-order/search")
    assert r.status_code == 200
    titles = [res["link"]["title"] for res in r.json()["results"]]
    assert titles == ["newest", "middle", "oldest"]


# ===========================================================================
# 8. Paginação por cursor — união sem duplicatas
# ===========================================================================
def test_pagination_cursor_union_no_duplicates():
    sid = _make_community("c-page", "C Page")
    for i in range(5):
        _add_link("c-page", sid, type="site", title=f"L{i}", url=f"https://{i}",
                  created_at=f"2026-01-0{i + 1}T00:00:00+00:00")
    seen = []
    cursor = None
    pages = 0
    while True:
        params = {"limit": 2}
        if cursor:
            params["cursor"] = cursor
        r = client.get("/api/communities/c-page/search", params=params)
        assert r.status_code == 200
        body = r.json()
        seen.extend(res["link"]["id"] for res in body["results"])
        cursor = body["next_cursor"]
        pages += 1
        if not cursor:
            break
        assert pages < 10  # guarda contra loop
    assert len(seen) == 5
    assert len(set(seen)) == 5  # sem duplicatas


# ===========================================================================
# 9. Validação de params: type inválido → 422; limite acima do teto → 422
# ===========================================================================
def test_invalid_type_422():
    _make_community("c-val", "C Val")
    r = client.get("/api/communities/c-val/search", params={"type": "nope"})
    assert r.status_code == 422


def test_limit_above_cap_422():
    _make_community("c-cap", "C Cap")
    r = client.get("/api/communities/c-cap/search", params={"limit": 101})
    assert r.status_code == 422


# ===========================================================================
# 10. Datas: from > to coerente porém invertido → resultado vazio (não erro)
# ===========================================================================
def test_from_greater_than_to_empty():
    sid = _make_community("c-inv", "C Inv")
    _add_link("c-inv", sid, type="site", title="x", url="https://x",
              created_at="2026-06-15T00:00:00+00:00")
    r = client.get(
        "/api/communities/c-inv/search",
        params={"from": "2026-12-01", "to": "2026-01-01"},
    )
    assert r.status_code == 200
    assert r.json() == {"results": [], "next_cursor": None, "count": 0}


def test_malformed_date_422():
    _make_community("c-mal", "C Mal")
    r = client.get("/api/communities/c-mal/search", params={"from": "not-a-date"})
    assert r.status_code == 422


# ===========================================================================
# 11. Comunidade inexistente → 404
# ===========================================================================
def test_community_not_found_404():
    r = client.get("/api/communities/inexistente/search", params={"q": "x"})
    assert r.status_code == 404


# ===========================================================================
# 12. Vazio e acesso sem auth (200)
# ===========================================================================
def test_empty_result():
    _make_community("c-empty", "C Empty")
    r = client.get("/api/communities/c-empty/search", params={"q": "nada"})
    assert r.status_code == 200
    assert r.json() == {"results": [], "next_cursor": None, "count": 0}


def test_no_auth_returns_200():
    sid = _make_community("c-noauth", "C NoAuth")
    _add_link("c-noauth", sid, type="site", title="Pub", url="https://p")
    # sem header Authorization
    assert client.get("/api/communities/c-noauth/search").status_code == 200
    assert client.get("/api/search").status_code == 200
