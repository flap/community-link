"""Testes do modo ``supabase`` (RF-019, RF-021, RF-022, RN-006, RN-007).

Usa tokens HS256 assinados com um segredo de teste — mesmo formato de claims
emitido pelo Supabase Auth (``sub``, ``email``, ``aud``, ``iss``, ``exp``).
"""

import os
import time

os.environ.setdefault("CL_USE_IN_MEMORY_STORE", "true")

import jwt  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.config import Settings, get_settings  # noqa: E402
from app.main import app  # noqa: E402

SUPABASE_URL = "https://test-project.supabase.co"
SECRET = "super-secret-jwt-for-tests-only-0123456789"


def _settings() -> Settings:
    return Settings(
        auth_mode="supabase",
        supabase_url=SUPABASE_URL,
        supabase_jwt_secret=SECRET,
        use_in_memory_store=True,
    )


@pytest.fixture(autouse=True)
def supabase_mode():
    app.dependency_overrides[get_settings] = _settings
    yield
    app.dependency_overrides.pop(get_settings, None)


client = TestClient(app)


def token(sub: str, email: str, *, exp_delta: int = 3600, secret: str = SECRET, aud="authenticated"):
    now = int(time.time())
    claims = {
        "sub": sub,
        "email": email,
        "aud": aud,
        "iss": f"{SUPABASE_URL}/auth/v1",
        "iat": now,
        "exp": now + exp_delta,
        "role": "authenticated",
    }
    return jwt.encode(claims, secret, algorithm="HS256")


def auth(t: str) -> dict:
    return {"Authorization": f"Bearer {t}"}


ALICE = token("user-alice", "alice@example.com")
BOB = token("user-bob", "bob@example.com")


def test_missing_or_invalid_token_is_401():
    assert client.get("/api/admin/me").status_code == 401
    assert client.get("/api/admin/me", headers=auth("abc.def.ghi")).status_code == 401
    # assinatura inválida
    forged = token("x", "x@example.com", secret="wrong-secret")
    assert client.get("/api/admin/me", headers=auth(forged)).status_code == 401
    # expirado
    expired = token("x", "x@example.com", exp_delta=-10)
    assert client.get("/api/admin/me", headers=auth(expired)).status_code == 401
    # audiência errada
    bad_aud = token("x", "x@example.com", aud="anon")
    assert client.get("/api/admin/me", headers=auth(bad_aud)).status_code == 401


def test_me_returns_identity_from_token():
    r = client.get("/api/admin/me", headers=auth(ALICE))
    assert r.status_code == 200
    assert r.json() == {"sub": "user-alice", "email": "alice@example.com", "auth_mode": "supabase"}


def test_creator_becomes_admin_and_others_get_403():
    slug = "alice-community"
    r = client.post(
        "/api/admin/communities", headers=auth(ALICE),
        json={"name": "Alice", "slug": slug},
    )
    assert r.status_code == 201

    # Alice vê a comunidade; Bob não
    assert [c["slug"] for c in client.get("/api/admin/communities", headers=auth(ALICE)).json()] == [slug]
    assert client.get("/api/admin/communities", headers=auth(BOB)).json() == []

    # Bob não pode editar nem ler seções
    assert client.patch(
        f"/api/admin/communities/{slug}", headers=auth(BOB), json={"name": "Hack"}
    ).status_code == 403
    assert client.get(f"/api/admin/communities/{slug}/sections", headers=auth(BOB)).status_code == 403

    # Página pública segue aberta
    assert client.get(f"/api/communities/{slug}").status_code == 200

    # Alice aparece como admin
    admins = client.get(f"/api/admin/communities/{slug}/admins", headers=auth(ALICE)).json()
    assert [a["sub"] for a in admins["admins"]] == ["user-alice"]


def test_invite_by_email_promotes_on_first_access():
    slug = "shared-community"
    client.post("/api/admin/communities", headers=auth(ALICE), json={"name": "S", "slug": slug})

    # Alice convida Bob por e-mail (com maiúsculas para testar normalização)
    r = client.post(
        f"/api/admin/communities/{slug}/admins", headers=auth(ALICE),
        json={"email": "Bob@Example.com"},
    )
    assert r.status_code == 201
    assert r.json()["invites"][0]["email"] == "bob@example.com"

    # Bob ainda não está na lista de admins, mas o primeiro acesso efetiva o convite
    r = client.post(
        f"/api/admin/communities/{slug}/sections", headers=auth(BOB),
        json={"title": "Criada pelo Bob"},
    )
    assert r.status_code == 201

    admins = client.get(f"/api/admin/communities/{slug}/admins", headers=auth(ALICE)).json()
    assert sorted(a["sub"] for a in admins["admins"]) == ["user-alice", "user-bob"]
    assert admins["invites"] == []

    # Bob agora vê a comunidade na sua lista
    assert slug in [c["slug"] for c in client.get("/api/admin/communities", headers=auth(BOB)).json()]

    # convidar quem já é admin -> 409
    assert client.post(
        f"/api/admin/communities/{slug}/admins", headers=auth(ALICE),
        json={"email": "bob@example.com"},
    ).status_code == 409


def test_cannot_remove_last_admin_but_can_remove_others():
    slug = "last-admin"
    client.post("/api/admin/communities", headers=auth(ALICE), json={"name": "L", "slug": slug})

    # último admin -> 409 (RN-007)
    assert client.delete(
        f"/api/admin/communities/{slug}/admins/user-alice", headers=auth(ALICE)
    ).status_code == 409

    # adiciona Bob via convite + acesso, depois remove Alice
    client.post(f"/api/admin/communities/{slug}/admins", headers=auth(ALICE), json={"email": "bob@example.com"})
    client.get(f"/api/admin/communities/{slug}/sections", headers=auth(BOB))
    assert client.delete(
        f"/api/admin/communities/{slug}/admins/user-alice", headers=auth(BOB)
    ).status_code == 204
    # Alice perdeu acesso
    assert client.get(f"/api/admin/communities/{slug}/sections", headers=auth(ALICE)).status_code == 403


def test_remove_pending_invite():
    slug = "invite-cleanup"
    client.post("/api/admin/communities", headers=auth(ALICE), json={"name": "I", "slug": slug})
    client.post(f"/api/admin/communities/{slug}/admins", headers=auth(ALICE), json={"email": "c@example.com"})
    assert client.delete(
        f"/api/admin/communities/{slug}/invites/c@example.com", headers=auth(ALICE)
    ).status_code == 204
    assert client.get(f"/api/admin/communities/{slug}/admins", headers=auth(ALICE)).json()["invites"] == []
