#!/usr/bin/env bash
# Empacota o backend FastAPI (Mangum) para o AWS Lambda em python3.12/linux-x86_64.
#
# Produz infra/artifacts/backend.zip com:
#   - app/ (pacote do backend; handler em app/lambda_handler.py na raiz do zip)
#   - dependências de runtime (mangum, fastapi, boto3, pydantic*, PyJWT[crypto], ...)
#     instaladas com wheels manylinux2014_x86_64 / cp312 (NÃO as do host macOS/arm64).
#
# EXCLUI: backend/.env, backend/media/, __pycache__, *.pyc, tests/ — nada de segredos.
#
# O Terraform referencia o zip pronto via lambda_package_path + filebase64sha256,
# portanto este script DEVE rodar antes de `terraform plan`/`apply`.
set -euo pipefail

# Raiz do repo = dois níveis acima deste script (infra/scripts/ -> repo root).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

BACKEND_DIR="${REPO_ROOT}/backend"
ARTIFACTS_DIR="${REPO_ROOT}/infra/artifacts"
BUILD_DIR="${ARTIFACTS_DIR}/build"
ZIP_PATH="${ARTIFACTS_DIR}/backend.zip"

PY_VERSION="3.12"
PLATFORM="manylinux2014_x86_64"

echo "[build] repo root       : ${REPO_ROOT}"
echo "[build] backend         : ${BACKEND_DIR}"
echo "[build] build dir       : ${BUILD_DIR}"
echo "[build] zip destino     : ${ZIP_PATH}"
echo "[build] runtime alvo    : python${PY_VERSION} / ${PLATFORM}"

if [[ ! -d "${BACKEND_DIR}/app" ]]; then
  echo "[build] ERRO: ${BACKEND_DIR}/app não encontrado." >&2
  exit 1
fi
if [[ ! -f "${BACKEND_DIR}/requirements.txt" ]]; then
  echo "[build] ERRO: ${BACKEND_DIR}/requirements.txt não encontrado." >&2
  exit 1
fi

# Build limpo a cada execução (determinístico).
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"

# 1) Dependências de runtime com wheels da plataforma Lambda (não do host).
echo "[build] instalando dependências (wheels ${PLATFORM} / cp312)..."
python3 -m pip install \
  --target "${BUILD_DIR}" \
  --platform "${PLATFORM}" \
  --implementation cp \
  --python-version "${PY_VERSION}" \
  --only-binary=:all: \
  --upgrade \
  -r "${BACKEND_DIR}/requirements.txt"

# 2) Código do backend: copia backend/app -> build/app (handler na raiz do zip).
echo "[build] copiando pacote app/ ..."
cp -R "${BACKEND_DIR}/app" "${BUILD_DIR}/app"

# 3) Remover o que NÃO pode ir para o pacote (segredos, mídia local, caches, testes).
echo "[build] removendo artefatos indesejados (segredos/caches/testes)..."
rm -f  "${BUILD_DIR}/app/.env" 2>/dev/null || true
rm -rf "${BUILD_DIR}/app/media" 2>/dev/null || true
find "${BUILD_DIR}" -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
find "${BUILD_DIR}" -type d -name "*.dist-info" -prune -exec rm -rf {} + 2>/dev/null || true
find "${BUILD_DIR}" -type d -name "tests" -prune -exec rm -rf {} + 2>/dev/null || true
find "${BUILD_DIR}" -type f -name "*.pyc" -delete 2>/dev/null || true

# Sanidade: o handler precisa existir na raiz do zip.
if [[ ! -f "${BUILD_DIR}/app/lambda_handler.py" ]]; then
  echo "[build] ERRO: app/lambda_handler.py ausente no build." >&2
  exit 1
fi

# 4) Zipar o CONTEÚDO do build (raiz do zip = conteúdo; app/ no topo).
echo "[build] compactando ${ZIP_PATH} ..."
rm -f "${ZIP_PATH}"
( cd "${BUILD_DIR}" && zip -r -q -X "${ZIP_PATH}" . )

echo "[build] OK."
echo "[build] zip: ${ZIP_PATH} ($(du -h "${ZIP_PATH}" | cut -f1))"
