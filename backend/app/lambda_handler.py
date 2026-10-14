"""AWS Lambda entry point: load SSM config into os.environ, apply beta overrides,
reset config/repository/storage caches, then wrap FastAPI with Mangum.

This module is the SAM ``Handler`` (``app.lambda_handler.handler``). The cold-start
sequence runs once per container, at module import, BEFORE ``app.main`` is imported,
so that pydantic-settings and the repository/storage selectors read the final env.
"""

from __future__ import annotations

import os


def load_ssm_into_environ(env: dict[str, str] | None = None) -> None:
    """Load ``/community-link/beta/backend/*`` params into the process environment.

    Uses ``setdefault`` so values the SAM template set explicitly always win over SSM.
    No-op when ``CONFIG_SSM_PATH`` is unset (local/dev reuse). Logs success/failure to
    stdout for CloudWatch; a boto3/KMS error is fatal at cold start (propagated).
    """
    target = os.environ if env is None else env
    path = target.get("CONFIG_SSM_PATH")  # e.g. "/community-link/beta/backend"
    if not path:
        return
    import boto3

    ssm = boto3.client("ssm", region_name=target.get("AWS_REGION", "us-east-1"))
    paginator = ssm.get_paginator("get_parameters_by_path")
    count = 0
    try:
        for page in paginator.paginate(Path=path, Recursive=True, WithDecryption=True):
            for p in page["Parameters"]:
                name = p["Name"].rsplit("/", 1)[-1]  # strip path prefix -> CL_* var name
                target.setdefault(name, p["Value"])
                count += 1
    except Exception:  # noqa: BLE001 - log then re-raise; fatal at cold start
        print(f"[lambda_handler] SSM load FAILED for path {path!r}", flush=True)
        raise
    print(f"[lambda_handler] SSM load OK: {count} params from {path!r}", flush=True)


def apply_beta_overrides(env: dict[str, str] | None = None) -> None:
    """Force the beta-critical settings. Gated on ``CONFIG_SSM_PATH`` (the beta signal),
    so importing this module locally without ``CONFIG_SSM_PATH`` is a true no-op.
    """
    target = os.environ if env is None else env
    if not target.get("CONFIG_SSM_PATH"):
        return  # local/dev reuse: do nothing
    target["CL_USE_IN_MEMORY_STORE"] = "false"  # MUST win over the SSM default "true"
    # Fail LOUD if the media bucket wiring is missing: without CL_S3_BUCKET,
    # get_storage() silently falls back to LocalStorage on the Lambda's read-only
    # filesystem, losing/erroring uploads with no obvious cause. In beta the
    # template always sets MEDIA_BUCKET (= !Ref MediaBucket), so a missing value
    # is a misconfiguration, not a valid state — raise at cold start.
    media_bucket = target.get("MEDIA_BUCKET")
    if not media_bucket:
        raise RuntimeError(
            "MEDIA_BUCKET env var is required in beta (CONFIG_SSM_PATH is set) "
            "but is empty/unset; CL_S3_BUCKET cannot be derived and uploads would "
            "silently fall back to local storage. Check the SAM template's "
            "Environment.Variables.MEDIA_BUCKET."
        )
    target["CL_S3_BUCKET"] = media_bucket
    # CL_MEDIA_BASE_URL and CL_CORS_ORIGINS come from the CFN-pinned env vars
    # (DECISION 6); do not setdefault/override them here.


def reset_caches() -> None:
    """Make the cold-start reset SYMMETRIC: clear the lru_cache AND the two
    module-level singletons that actually decide in-memory-vs-DynamoDB and
    local-vs-S3. Belt-and-suspenders in case a prior import warmed them.
    """
    import app.config as _cfg

    _cfg.get_settings.cache_clear()
    import app.repository as _repo

    _repo._repository = None
    import app.storage as _stor

    _stor._storage = None


# ---- Cold-start sequence (runs once per container, at module import) --------
load_ssm_into_environ()  # 1) SSM -> os.environ (setdefault; template wins)
apply_beta_overrides()  # 2) force beta-critical values (gated on CONFIG_SSM_PATH)
reset_caches()  # 3) clear settings lru_cache + repository/storage globals

from app.main import app  # noqa: E402  (import AFTER env + caches are final)
from mangum import Mangum  # noqa: E402

handler = Mangum(app, lifespan="off")
