#!/usr/bin/env bash
# Sobe o backend Community Link (dev, repositório em memória).
set -e
cd "$(dirname "$0")/backend"
source .venv/bin/activate
export CL_USE_IN_MEMORY_STORE=true
export CL_ADMIN_TOKEN=dev-admin-token-change-me
exec uvicorn app.main:app --port 8080
