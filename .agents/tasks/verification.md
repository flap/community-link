# Verification — AWS SAM Beta Deployment (Community Link)

First iteration (no `review.json` present). All work done in the worktree
`/Users/pimenta/community/pastel/.worktrees/beta-sam-deploy` on branch
`beta-sam-deploy`. This file records exactly what was run and the results so the
reviewer can read it without re-running.

## Environment

- SAM CLI: `1.153.1` (installed, on PATH). `sam validate`, `sam validate --lint`, `sam build` all run successfully.
- AWS CLI: `aws-cli/2.32.22` (installed). No live deploy performed (per instructions — the deploy script is created but NOT run here).
- cfn-lint (bundled with SAM): `1.43.4`; a fresh `cfn-lint 1.57.2` was also installed into the backend venv for diagnosis.
- Python: fresh venv created at `backend/.venv` (gitignored) from `backend/requirements.txt` + `pytest`. Interpreter is Python 3.14 in this environment (the Lambda runtime is `python3.12`; tests run locally only).

## 1. `sam validate --lint` on template.yaml — PASS

Command (from worktree root):

```
sam validate --lint
```

Result:

```
/Users/pimenta/community/pastel/.worktrees/beta-sam-deploy/template.yaml is a valid SAM Template
```

Note on a fix made during verification: the design (`design.md`) specified the
SAM transform as `AWS::Serverless-2016-10-09`, which is **incorrect** — that date
is the CloudFormation *template format* version, not the SAM transform macro.
cfn-lint rejected it (`E3038`/`E3006`/`E3724 Globals requires the serverless
transform 'AWS::Serverless-2016-10-31'`). The template uses the correct macro
`Transform: AWS::Serverless-2016-10-31`; with that, `--lint` passes clean.

The implicit `ServerlessHttpApi` logical id is not recognized by cfn-lint, so an
**explicit** `AWS::Serverless::HttpApi` resource (`HttpApi`, `StageName: $default`)
is declared and referenced by the Lambda event (`ApiId: !Ref HttpApi`), the
CloudFront API origin, and the `HttpApiUrl` output. Functionally equivalent to
the implicit API and lint-clean.

## 2. Backend tests — PASS (24 passed)

Fresh venv:

```
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install pytest
```

Full suite (design's exact env):

```
cd backend
CL_USE_IN_MEMORY_STORE=true CL_ADMIN_TOKEN=test-token .venv/bin/python -m pytest -q
```

Result:

```
24 passed, 2 warnings in 0.31s
```

The 2 warnings are pre-existing and unrelated to these changes (a Starlette
TestClient/httpx deprecation and an HMAC-key-length warning in an auth test).

New tests in `backend/tests/test_lambda_handler.py` (8, all pass):
- `load_ssm_into_environ` maps the last path segment to the env var name and honors `setdefault` (pre-set/template value wins over SSM).
- `load_ssm_into_environ` is a no-op without `CONFIG_SSM_PATH`.
- `apply_beta_overrides` forces `CL_USE_IN_MEMORY_STORE="false"` + `CL_S3_BUCKET=MEDIA_BUCKET` when beta, and does NOT touch `CL_MEDIA_BASE_URL`/`CL_CORS_ORIGINS`.
- `apply_beta_overrides` no-op without `CONFIG_SSM_PATH`.
- `apply_beta_overrides` raises `RuntimeError` when `MEDIA_BUCKET` is missing/empty (fail-loud).
- `reset_caches` clears the `get_settings` lru_cache AND the `repository._repository` / `storage._storage` globals.
- Import-order guard: importing `app.config` does not transitively import `app.repository`/`app.storage`.
- `S3Storage.save()` (mocked boto3) calls `put_object` with the right Bucket/Key(`links/<uuid>.<ext>`)/ContentType and returns the relative `/media/links/<uuid>.<ext>` URL.

Gated no-op sanity (step 2 of the plan):

```
CL_USE_IN_MEMORY_STORE=true CL_ADMIN_TOKEN=test-token .venv/bin/python -c \
  "import app.lambda_handler as h; d={}; h.apply_beta_overrides(d); assert d=={}, d; print('gated no-op OK')"
# -> gated no-op OK
```

## 3. `sam build` — PASS

```
sam build
```

Result: `Build Succeeded`, artifacts in `.aws-sam/build` (gitignored, not committed).

Bundle checks:
- `mangum` present: `.aws-sam/build/ApiFunction/mangum` + `mangum-0.22.0.dist-info` (pinned `mangum>=0.19.0` in requirements.txt).
- `app/lambda_handler.py` present in the bundle.
- No secret `.env` in the bundle: `find .aws-sam/build -name ".env"` → empty. (Only `.env.example`, the project's placeholder template with NO real secrets, is present.)

### `.samignore` limitation (honest note — NOT satisfied as the design assumed)

The design added a `.samignore` to exclude `backend/.env`, `__pycache__`, `*.pyc`,
and `backend/tests/` from the Lambda bundle. **SAM CLI 1.153.1 does not implement
`.samignore` for the Python `CopySource` build workflow** (the string `samignore`
does not appear anywhere in this SAM version's source). As a result:

- `backend/tests/` **does** ship inside `.aws-sam/build/ApiFunction/tests/`. This is build bloat, not a security problem (the test files carry no secrets). (Third-party packages like `annotated_types`/`certifi` also ship their own `test_*.py`, which is normal.)
- `.env.example` ships. It is a placeholder with no secrets.

The **security-critical invariant the design actually cared about — that no
secret-bearing `.env` is ever packaged — holds**: no `backend/.env` exists in the
worktree, and pydantic-settings reads env vars with higher precedence than a
`.env` file regardless. The `.samignore` file is kept (it is harmless, documents
intent, and is honored by newer SAM versions), but this environment does not
enforce it, so the test-exclusion claim is explicitly NOT made here.

## 4. Frontend build — PASS; signup affordance removed

```
cd frontend
npm ci
npm run build   # -> dist/ produced, built in ~350ms
grep -rl "signUp\|Criar conta" dist/assets/ || echo "no signup affordance in build"
# -> no signup affordance in build
```

`LoginView.vue` had the signup mode (`supabase.auth.signUp`), the "Criar conta"
link, and the `mode === 'signup'` template branches removed; only email/password
login + password reset remain. Social buttons are config-driven via
`VITE_SUPABASE_PROVIDERS` (the deploy script sets it empty in SSM so no social
buttons render — see §deploy script step 2).

## 5. Deploy script — syntax validated (NOT executed)

```
bash -n scripts/deploy-beta.sh   # -> syntax OK
```

- Account guard: aborts with `exit 1` unless `aws sts get-caller-identity` == `390686807269`.
- Region: `export AWS_REGION=us-east-1` (+ `AWS_DEFAULT_REGION`).
- Flow: ensure empty `VITE_SUPABASE_PROVIDERS` in SSM → resolve `ConfigVersion` (stable by default, `--roll` for a forced cold start) → `sam build` → `sam deploy` pass 1 (`CorsOrigins=*`) → read outputs → `sam deploy` pass 2 (`CorsOrigins=https://<cf-domain>`) → `npm ci && npm run build` with `VITE_*` from SSM (`--with-decryption`, values never echoed; the export loop runs under `set +x`) → `aws s3 sync dist/ --delete` → CloudFront invalidation `/*` → health smoke check.
- Idempotent: every mutation flows through `sam deploy` / `put-parameter --overwrite` / `s3 sync --delete` / invalidation. No `update-function-configuration`.
- `shellcheck` is not installed in this environment (non-blocking per the plan); `bash -n` passed.
- NOTE: SSM rejects a truly empty String value, so the script stores a single space `" "` for `VITE_SUPABASE_PROVIDERS`; the frontend's `.split(',').map(trim).filter(Boolean)` drops it → zero social providers, same effect as empty.

## 6. `.gitignore` ignores `.aws-sam/` — PASS

`.gitignore` already contained `# AWS SAM build` + `.aws-sam/` (a duplicate bare
`.aws-sam` line was removed, leaving the canonical `.aws-sam/`). Confirmed:
`git check-ignore .aws-sam frontend/dist frontend/node_modules backend/.venv`
lists all four, so no build artifacts are tracked.

## Not performed (requires live AWS — out of scope for this step)

Per instructions, the actual `sam deploy` was NOT run. Plan step 13 (live
post-deploy verification: CloudFront/API health, SPA fallback incl. dotted slugs,
DynamoDB-backed write, end-to-end `/media/*` fetch, CloudWatch cold-start logs,
login page has no social buttons/signup, DynamoDB table-name collision check) is
deferred to the operator running `./scripts/deploy-beta.sh` with credentials for
account 390686807269.

## DynamoDB schema confirmation

`backend/app/dynamo_repository.py` uses only `PK`/`SK`: `get_item`, `put_item`,
`query` on `PK` with `begins_with(SK, …)`, and one `scan` with a
`FilterExpression` (`list_communities`). No `IndexName` / GSI / LSI usage. The
template's table therefore defines PK(S) HASH + SK(S) RANGE only, PAY_PER_REQUEST,
no secondary indexes — matching the repository exactly.
