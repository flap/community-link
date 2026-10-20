#!/usr/bin/env bash
# Sobe o backend Community Link (dev).
#
# A configuração vem de backend/.env (lido pelo pydantic-settings). Este script
# NÃO sobrescreve CL_AUTH_MODE, CL_SUPABASE_URL etc., para que o modo definido
# no .env (ex.: supabase) seja respeitado.
#
# Modo de desenvolvimento rápido (credencial fixa, sem Supabase):
#   AUTH=static ./run-backend.sh
# força CL_AUTH_MODE=static e um token fixo, ignorando o .env.
set -e
cd "$(dirname "$0")/backend"
source .venv/bin/activate

# Persistência em memória por padrão em dev; sobreponha no .env se quiser DynamoDB.
export CL_USE_IN_MEMORY_STORE="${CL_USE_IN_MEMORY_STORE:-true}"

if [ "${AUTH:-}" = "static" ]; then
  # Atalho dev: credencial fixa, ignora Supabase.
  export CL_AUTH_MODE=static
  export CL_ADMIN_TOKEN="${CL_ADMIN_TOKEN:-dev-admin-token-change-me}"
  echo "run-backend: modo de auth = static (credencial fixa de dev)"
else
  # Modo padrão: respeita backend/.env (ex.: CL_AUTH_MODE=supabase).
  if [ -f .env ] && grep -Eq '^CL_AUTH_MODE=supabase' .env; then
    echo "run-backend: modo de auth = supabase (de backend/.env)"
  else
    echo "run-backend: modo de auth = conforme backend/.env (padrão: static)"
  fi
fi

exec uvicorn app.main:app --port 8080
