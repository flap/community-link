"""Testes básicos da API (Fase 1) usando o repositório em memória."""

import os

os.environ.setdefault("CL_USE_IN_MEMORY_STORE", "true")
os.environ.setdefault("CL_ADMIN_TOKEN", "test-token")

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
