#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.." &&
  pwd
)"

cd "${PROJECT_DIR}"

if [[ ! -d ".venv" ]]; then
    echo "ERROR: Python virtual environment does not exist."
    echo "Create it with:"
    echo "  python3 -m venv .venv"
    exit 1
fi

source .venv/bin/activate

echo "========================================"
echo " AI Platform API - Phase 2L"
echo "========================================"
echo "FastAPI:  http://127.0.0.1:8001"
echo "Swagger:  http://127.0.0.1:8001/docs"
echo
echo "Port inventory:"
echo "8080   -> Argo CD"
echo "18080  -> Keycloak"
echo "8001   -> AI Platform API"
echo "========================================"

exec uvicorn app.main:app \
  --host 127.0.0.1 \
  --port 8001 \
  --reload
