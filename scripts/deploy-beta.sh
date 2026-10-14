#!/usr/bin/env bash
#
# deploy-beta.sh — deploy Community Link to the beta environment (AWS SAM).
#
# Idempotent / re-runnable: every mutation flows through `sam deploy`,
# `aws ssm put-parameter --overwrite`, `aws s3 sync --delete`, or a CloudFront
# invalidation — there is NO out-of-band `update-function-configuration`.
#
# Usage:
#   ./scripts/deploy-beta.sh          # normal deploy (stable ConfigVersion)
#   ./scripts/deploy-beta.sh --roll   # force a cold-start roll (fresh ConfigVersion)
#
# Guards: aborts unless the caller is AWS account 390686807269 in us-east-1.
# Secrets (Supabase anon key, etc.) are never echoed to stdout.

set -euo pipefail

# --- Constants -------------------------------------------------------------
readonly EXPECTED_ACCOUNT="390686807269"
readonly REGION="us-east-1"
readonly STACK_NAME="community-link-beta"
readonly CONFIG_SSM_PATH="/community-link/beta/backend"
readonly FRONTEND_SSM_PATH="/community-link/beta/frontend"
readonly MEDIA_BASE_URL="/media"

export AWS_REGION="$REGION"
export AWS_DEFAULT_REGION="$REGION"

# Run from the worktree/repo root (parent of this script's dir).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

# --- Flags -----------------------------------------------------------------
ROLL=false
for arg in "$@"; do
  case "$arg" in
    --roll) ROLL=true ;;
    *) echo "Unknown argument: $arg" >&2; exit 2 ;;
  esac
done

# --- 1. Account guard ------------------------------------------------------
echo "==> Verifying AWS caller identity..."
ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
if [[ "$ACCOUNT" != "$EXPECTED_ACCOUNT" ]]; then
  echo "ERROR: expected AWS account $EXPECTED_ACCOUNT but got '$ACCOUNT'. Aborting." >&2
  exit 1
fi
echo "    account $ACCOUNT, region $REGION — OK"

# --- 2. Ensure social providers are disabled (empty, not absent) -----------
# An ABSENT VITE_SUPABASE_PROVIDERS defaults to google,github in supabase.js;
# an EMPTY value yields zero social buttons. Create/overwrite it empty.
echo "==> Ensuring $FRONTEND_SSM_PATH/VITE_SUPABASE_PROVIDERS is empty..."
aws ssm put-parameter \
  --name "$FRONTEND_SSM_PATH/VITE_SUPABASE_PROVIDERS" \
  --value " " \
  --type String \
  --overwrite >/dev/null
# Note: SSM rejects a truly empty string, so a single space is stored; the
# frontend's .split(',').map(trim).filter(Boolean) drops it -> no providers.

# --- 3. Resolve ConfigVersion ----------------------------------------------
# Default: re-pass the stack's current ConfigVersion unchanged (empty changeset
# on a no-op re-run). --roll: fresh time-based value to force new containers.
resolve_config_version() {
  if [[ "$ROLL" == "true" ]]; then
    date +%s
    return
  fi
  local current
  current="$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Parameters[?ParameterKey=='ConfigVersion'].ParameterValue | [0]" \
    --output text 2>/dev/null || true)"
  if [[ -z "$current" || "$current" == "None" ]]; then
    echo "0"
  else
    echo "$current"
  fi
}
CONFIG_VERSION="$(resolve_config_version)"
echo "==> ConfigVersion=$CONFIG_VERSION (roll=$ROLL)"

# --- 4. sam build ----------------------------------------------------------
echo "==> sam build..."
sam build

# --- 5. First deploy pass (CorsOrigins=*) ----------------------------------
echo "==> sam deploy (pass 1: CorsOrigins=*)..."
sam deploy \
  --config-env beta \
  --no-fail-on-empty-changeset \
  --resolve-s3 \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    "Stage=beta" \
    "ConfigSsmPath=$CONFIG_SSM_PATH" \
    "MediaBaseUrl=$MEDIA_BASE_URL" \
    "ConfigVersion=$CONFIG_VERSION" \
    "CorsOrigins=*"

# --- 6. Read stack outputs -------------------------------------------------
echo "==> Reading stack outputs..."
get_output() {
  aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue | [0]" \
    --output text
}
SPA_BUCKET="$(get_output FrontendBucketName)"
MEDIA_BUCKET="$(get_output MediaBucketName)"
CF_DOMAIN="$(get_output CloudFrontDomain)"
CF_DIST_ID="$(get_output CloudFrontDistributionId)"
HTTP_API_URL="$(get_output HttpApiUrl)"
TABLE_NAME="$(get_output TableName)"
echo "    SPA_BUCKET=$SPA_BUCKET"
echo "    MEDIA_BUCKET=$MEDIA_BUCKET"
echo "    CF_DOMAIN=$CF_DOMAIN"
echo "    CF_DIST_ID=$CF_DIST_ID"
echo "    HTTP_API_URL=$HTTP_API_URL"
echo "    TABLE_NAME=$TABLE_NAME"

# --- 7. Second deploy pass (CorsOrigins=https://<cf-domain>) ----------------
echo "==> sam deploy (pass 2: CorsOrigins=https://$CF_DOMAIN)..."
sam deploy \
  --config-env beta \
  --no-fail-on-empty-changeset \
  --resolve-s3 \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    "Stage=beta" \
    "ConfigSsmPath=$CONFIG_SSM_PATH" \
    "MediaBaseUrl=$MEDIA_BASE_URL" \
    "ConfigVersion=$CONFIG_VERSION" \
    "CorsOrigins=https://$CF_DOMAIN"

# --- 8. Build + upload the frontend ----------------------------------------
echo "==> Building frontend with VITE_* from $FRONTEND_SSM_PATH (values not echoed)..."
# Export VITE_* from SSM without printing values. `set +x` keeps the loop quiet.
set +x
while IFS=$'\t' read -r name value; do
  [[ -z "$name" ]] && continue
  key="${name##*/}"            # last path segment -> VITE_* var name
  export "$key=$value"
done < <(aws ssm get-parameters-by-path \
            --path "$FRONTEND_SSM_PATH" \
            --recursive \
            --with-decryption \
            --query "Parameters[].[Name,Value]" \
            --output text)

(
  cd frontend
  npm ci
  npm run build
)

echo "==> Syncing frontend/dist -> s3://$SPA_BUCKET ..."
aws s3 sync frontend/dist/ "s3://$SPA_BUCKET/" --delete

echo "==> Creating CloudFront invalidation (/*)..."
aws cloudfront create-invalidation \
  --distribution-id "$CF_DIST_ID" \
  --paths '/*' >/dev/null

# --- 9. Smoke check --------------------------------------------------------
echo ""
echo "============================================================"
echo " Beta deploy complete."
echo "   CloudFront URL : https://$CF_DOMAIN"
echo "   HTTP API URL   : $HTTP_API_URL"
echo "   DynamoDB table : $TABLE_NAME"
echo "============================================================"
echo "==> Health check: https://$CF_DOMAIN/api/health"
curl -s "https://$CF_DOMAIN/api/health" || echo "(health check failed — CloudFront may still be propagating)"
echo ""
