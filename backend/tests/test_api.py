"""Testes básicos da API (Fase 1) usando o repositório em memória."""

import os
import tempfile

os.environ.setdefault("CL_USE_IN_MEMORY_STORE", "true")
os.environ.setdefault("CL_ADMIN_TOKEN", "test-token")
os.environ.setdefault("CL_MEDIA_DIR", tempfile.mkdtemp(prefix="cl-media-"))
os.environ.setdefault("CL_MAX_UPLOAD_BYTES", str(1024 * 1024))  # 1MB nos testes

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)
AUTH = {"Authorization": "Bearer test-token"}


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_admin_requires_auth():
    r = client.get("/api/admin/communities")
    assert r.status_code == 401


def test_full_flow_community_section_link():
    # cria comunidade
    r = client.post(
        "/api/admin/communities",
        headers=AUTH,
        json={"name": "AWS User Group SP", "slug": "aws-ug-sp", "theme": "aws"},
    )
    assert r.status_code == 201, r.text

    # slug duplicado -> 409
    r_dup = client.post(
        "/api/admin/communities",
        headers=AUTH,
        json={"name": "Outro", "slug": "aws-ug-sp"},
    )
    assert r_dup.status_code == 409

    # cria seção
    r_sec = client.post(
        "/api/admin/communities/aws-ug-sp/sections",
        headers=AUTH,
        json={"title": "Eventos", "order": 0},
    )
    assert r_sec.status_code == 201, r_sec.text
    section_id = r_sec.json()["id"]

    # cria link de vídeo (embeddável)
    r_link = client.post(
        "/api/admin/communities/aws-ug-sp/links",
        headers=AUTH,
        json={
            "section_id": section_id,
            "type": "video",
            "title": "Palestra AWS",
            "url": "https://youtu.be/dQw4w9WgXcQ",
            "emoji": "🎥",
            "embed": True,
        },
    )
    assert r_link.status_code == 201, r_link.text

    # página pública monta seções + links + embed
    r_pub = client.get("/api/communities/aws-ug-sp")
    assert r_pub.status_code == 200, r_pub.text
    body = r_pub.json()
    assert body["slug"] == "aws-ug-sp"
    assert len(body["sections"]) == 1
    link = body["sections"][0]["links"][0]
    assert link["emoji"] == "🎥"
    assert link["embed_data"]["kind"] == "youtube"


def test_invalid_slug_rejected():
    r = client.post(
        "/api/admin/communities",
        headers=AUTH,
        json={"name": "X", "slug": "Invalid Slug!"},
    )
    assert r.status_code == 422


def test_reserved_slug_rejected():
    r = client.post(
        "/api/admin/communities",
        headers=AUTH,
        json={"name": "X", "slug": "api"},
    )
    assert r.status_code == 422


def test_edit_community_section_link_and_reorder():
    slug = "edit-flow"
    client.post(
        "/api/admin/communities",
        headers=AUTH,
        json={"name": "Edit Flow", "slug": slug, "theme": "aws"},
    )

    # edita comunidade (RF-015) — nome/descrição/tema
    r = client.patch(
        f"/api/admin/communities/{slug}",
        headers=AUTH,
        json={"name": "Edit Flow 2", "description": "nova desc", "theme": "light"},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Edit Flow 2"
    assert r.json()["theme"] == "light"

    # tema inválido rejeitado
    assert client.patch(
        f"/api/admin/communities/{slug}", headers=AUTH, json={"theme": "nope"}
    ).status_code == 400

    # cria duas seções
    s1 = client.post(
        f"/api/admin/communities/{slug}/sections", headers=AUTH,
        json={"title": "A", "order": 0},
    ).json()
    s2 = client.post(
        f"/api/admin/communities/{slug}/sections", headers=AUTH,
        json={"title": "B", "order": 1},
    ).json()

    # edita título da seção (RF-016)
    r = client.patch(
        f"/api/admin/communities/{slug}/sections/{s1['id']}",
        headers=AUTH, json={"title": "A editada"},
    )
    assert r.status_code == 200 and r.json()["title"] == "A editada"

    # reordena seções: B antes de A (RF-018)
    r = client.put(
        f"/api/admin/communities/{slug}/sections/reorder",
        headers=AUTH, json={"ordered_ids": [s2["id"], s1["id"]]},
    )
    assert r.status_code == 200
    ordered = r.json()
    assert ordered[0]["id"] == s2["id"] and ordered[0]["order"] == 0

    # cria dois links na seção A
    l1 = client.post(
        f"/api/admin/communities/{slug}/links", headers=AUTH,
        json={"section_id": s1["id"], "type": "site", "title": "L1", "url": "https://a.com"},
    ).json()
    l2 = client.post(
        f"/api/admin/communities/{slug}/links", headers=AUTH,
        json={"section_id": s1["id"], "type": "site", "title": "L2", "url": "https://b.com"},
    ).json()

    # edita link (RF-017)
    r = client.patch(
        f"/api/admin/communities/{slug}/links/{l1['id']}",
        headers=AUTH, json={"title": "L1 editado", "emoji": "🔗"},
    )
    assert r.status_code == 200 and r.json()["title"] == "L1 editado"

    # reordena links: L2 antes de L1 (RF-018)
    r = client.put(
        f"/api/admin/communities/{slug}/sections/{s1['id']}/links/reorder",
        headers=AUTH, json={"ordered_ids": [l2["id"], l1["id"]]},
    )
    assert r.status_code == 200 and r.json()[0]["id"] == l2["id"]

    # move link L2 para a seção B (RF-017)
    r = client.patch(
        f"/api/admin/communities/{slug}/links/{l2['id']}",
        headers=AUTH, json={"section_id": s2["id"]},
    )
    assert r.status_code == 200 and r.json()["section_id"] == s2["id"]

    # a página pública reflete tudo
    pub = client.get(f"/api/communities/{slug}").json()
    sec_titles = [s["title"] for s in pub["sections"]]
    assert sec_titles == ["B", "A editada"]  # ordem aplicada


def test_reorder_rejects_foreign_link():
    slug = "reorder-foreign"
    client.post(
        "/api/admin/communities", headers=AUTH,
        json={"name": "RF", "slug": slug},
    )
    s1 = client.post(
        f"/api/admin/communities/{slug}/sections", headers=AUTH, json={"title": "S1"}
    ).json()
    s2 = client.post(
        f"/api/admin/communities/{slug}/sections", headers=AUTH, json={"title": "S2"}
    ).json()
    link = client.post(
        f"/api/admin/communities/{slug}/links", headers=AUTH,
        json={"section_id": s1["id"], "type": "site", "title": "X", "url": "https://x.com"},
    ).json()
    # tentar reordenar na seção errada -> 409
    r = client.put(
        f"/api/admin/communities/{slug}/sections/{s2['id']}/links/reorder",
        headers=AUTH, json={"ordered_ids": [link["id"]]},
    )
    assert r.status_code == 409


def test_upload_image_and_use_as_featured_photo():
    # upload válido (PNG mínimo) -> retorna image_url (RF-007)
    png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00"
        b"\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    r = client.post(
        "/api/admin/uploads",
        headers=AUTH,
        files={"file": ("foto.png", png, "image/png")},
    )
    assert r.status_code == 201, r.text
    image_url = r.json()["image_url"]
    assert image_url.startswith("/api/media/")

    # a imagem é servida pela API em dev
    assert client.get(image_url).status_code == 200

    # usar como foto de destaque em um link
    client.post(
        "/api/admin/communities",
        headers=AUTH,
        json={"name": "Foto", "slug": "foto-flow"},
    )
    sec = client.post(
        "/api/admin/communities/foto-flow/sections", headers=AUTH, json={"title": "S"}
    ).json()
    link = client.post(
        "/api/admin/communities/foto-flow/links",
        headers=AUTH,
        json={
            "section_id": sec["id"], "type": "site", "title": "Com foto",
            "url": "https://x.com", "image_url": image_url,
        },
    ).json()
    assert link["image_url"] == image_url

    # aparece na página pública
    pub = client.get("/api/communities/foto-flow").json()
    assert pub["sections"][0]["links"][0]["image_url"] == image_url


def test_upload_rejects_invalid_type():
    r = client.post(
        "/api/admin/uploads",
        headers=AUTH,
        files={"file": ("a.txt", b"hello", "text/plain")},
    )
    assert r.status_code == 400


def test_upload_rejects_oversize():
    big = b"\x89PNG\r\n\x1a\n" + b"0" * (1024 * 1024 + 10)
    r = client.post(
        "/api/admin/uploads",
        headers=AUTH,
        files={"file": ("big.png", big, "image/png")},
    )
    assert r.status_code == 400
