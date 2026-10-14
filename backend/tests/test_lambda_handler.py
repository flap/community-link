"""Testes das funções puras do ``lambda_handler`` e da mudança do ``S3Storage``.

As funções ``load_ssm_into_environ`` / ``apply_beta_overrides`` recebem um dict
``env`` para serem testadas sem tocar em ``os.environ`` nem importar ``app.main``.
"""

import os
import sys

os.environ.setdefault("CL_USE_IN_MEMORY_STORE", "true")
os.environ.setdefault("CL_ADMIN_TOKEN", "test-token")

import pytest  # noqa: E402

from app import lambda_handler as lh  # noqa: E402
from app.config import Settings  # noqa: E402
from app.storage import S3Storage  # noqa: E402


# -- load_ssm_into_environ --------------------------------------------------
class _FakePaginator:
    def __init__(self, pages):
        self._pages = pages

    def paginate(self, **kwargs):  # noqa: D401, ANN001, ANN003
        assert kwargs["Path"] == "/community-link/beta/backend"
        assert kwargs["Recursive"] is True
        assert kwargs["WithDecryption"] is True
        yield from self._pages


class _FakeSSM:
    def __init__(self, pages):
        self._pages = pages

    def get_paginator(self, name):  # noqa: ANN001
        assert name == "get_parameters_by_path"
        return _FakePaginator(self._pages)


def test_load_ssm_into_environ_maps_last_segment_and_setdefault(monkeypatch):
    pages = [
        {
            "Parameters": [
                {"Name": "/community-link/beta/backend/CL_DYNAMODB_TABLE", "Value": "community-link"},
                {"Name": "/community-link/beta/backend/CL_AUTH_MODE", "Value": "supabase"},
                {"Name": "/community-link/beta/backend/CL_USE_IN_MEMORY_STORE", "Value": "true"},
            ]
        }
    ]
    fake_boto3 = type("B", (), {"client": staticmethod(lambda *a, **k: _FakeSSM(pages))})
    monkeypatch.setitem(sys.modules, "boto3", fake_boto3)

    env = {
        "CONFIG_SSM_PATH": "/community-link/beta/backend",
        # pre-set value must WIN over SSM (setdefault semantics / template wins)
        "CL_DYNAMODB_TABLE": "preset-table",
    }
    lh.load_ssm_into_environ(env)

    assert env["CL_DYNAMODB_TABLE"] == "preset-table"  # setdefault: template value wins
    assert env["CL_AUTH_MODE"] == "supabase"
    assert env["CL_USE_IN_MEMORY_STORE"] == "true"


def test_load_ssm_into_environ_noop_without_path():
    env = {}
    lh.load_ssm_into_environ(env)
    assert env == {}


# -- apply_beta_overrides ---------------------------------------------------
def test_apply_beta_overrides_forces_values_when_beta():
    env = {"CONFIG_SSM_PATH": "/community-link/beta/backend", "MEDIA_BUCKET": "my-media-bucket"}
    lh.apply_beta_overrides(env)
    assert env["CL_USE_IN_MEMORY_STORE"] == "false"
    assert env["CL_S3_BUCKET"] == "my-media-bucket"
    # must NOT touch these — owned by the CFN env vars
    assert "CL_MEDIA_BASE_URL" not in env
    assert "CL_CORS_ORIGINS" not in env


def test_apply_beta_overrides_noop_without_config_ssm_path():
    env = {}
    lh.apply_beta_overrides(env)
    assert env == {}


def test_apply_beta_overrides_raises_when_media_bucket_missing():
    env = {"CONFIG_SSM_PATH": "/community-link/beta/backend"}
    with pytest.raises(RuntimeError, match="MEDIA_BUCKET"):
        lh.apply_beta_overrides(env)

    env2 = {"CONFIG_SSM_PATH": "/community-link/beta/backend", "MEDIA_BUCKET": ""}
    with pytest.raises(RuntimeError, match="MEDIA_BUCKET"):
        lh.apply_beta_overrides(env2)


# -- reset_caches -----------------------------------------------------------
def test_reset_caches_clears_all_three():
    import app.config as cfg
    import app.repository as repo
    import app.storage as stor

    # warm the lru_cache and the two module-level singletons with sentinels
    cfg.get_settings()
    repo._repository = object()
    stor._storage = object()

    lh.reset_caches()

    assert repo._repository is None
    assert stor._storage is None
    # lru_cache cleared → a fresh call returns a brand-new Settings instance
    assert cfg.get_settings.cache_info().currsize == 0


def test_importing_config_does_not_import_repository_or_storage():
    # Import-order guard (finding 1 rationale): a clean container that imports
    # app.config must NOT transitively import repository/storage, so env is
    # finalized before those selectors run.
    for mod in ("app.config", "app.repository", "app.storage"):
        sys.modules.pop(mod, None)
    import app.config  # noqa: F401

    assert "app.repository" not in sys.modules
    assert "app.storage" not in sys.modules


# -- S3Storage.save ---------------------------------------------------------
class _FakeS3Client:
    def __init__(self):
        self.calls = []

    def put_object(self, **kwargs):  # noqa: ANN003
        self.calls.append(kwargs)


def test_s3_storage_save_returns_relative_media_url(monkeypatch):
    fake_client = _FakeS3Client()
    fake_boto3 = type("B", (), {"client": staticmethod(lambda *a, **k: fake_client)})
    monkeypatch.setitem(sys.modules, "boto3", fake_boto3)

    settings = Settings(
        s3_bucket="my-media-bucket",
        media_base_url="/media",
        aws_region="us-east-1",
    )
    storage = S3Storage(settings)
    content = b"\x89PNG\r\n\x1a\n" + b"0" * 32
    url = storage.save(content, "image/png")

    # put_object called with the right bucket/key/content-type
    assert len(fake_client.calls) == 1
    call = fake_client.calls[0]
    assert call["Bucket"] == "my-media-bucket"
    assert call["Key"].startswith("links/")
    assert call["Key"].endswith(".png")
    assert call["ContentType"] == "image/png"
    assert call["Body"] == content

    # returned URL is the CloudFront-relative /media/links/<uuid>.png form
    assert url.startswith("/media/links/")
    assert url.endswith(".png")
    assert url == f"/media/{call['Key']}"
