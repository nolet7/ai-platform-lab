#!/usr/bin/env bash
set -euo pipefail

LOCAL_PORT="18081"
REMOTE_PORT="8001"

LOG_FILE="/tmp/ai-platform-api-k8s-port-forward.log"
PID_FILE="/tmp/ai-platform-api-k8s-port-forward.pid"

echo
echo "Port inventory:"
echo "  8080   -> Argo CD"
echo "  18080  -> Keycloak"
echo "  8001   -> Local Phase 2L FastAPI"
echo "  18081  -> Phase 2M Kubernetes FastAPI"
echo

if ss -ltn | grep -q ":${LOCAL_PORT} "; then

    echo "Port ${LOCAL_PORT} already listening."

    if curl -fsS \
      "http://127.0.0.1:${LOCAL_PORT}/health/live" \
      >/dev/null 2>&1
    then
        echo "Existing Phase 2M port-forward is healthy."
        exit 0
    fi

    echo "ERROR: ${LOCAL_PORT} is occupied by another process."

    ss -ltnp |
      grep ":${LOCAL_PORT}" || true

    exit 1
fi

kubectl port-forward \
  -n ai-platform \
  service/ai-platform-api \
  "${LOCAL_PORT}:${REMOTE_PORT}" \
  >"${LOG_FILE}" 2>&1 &

PID=$!

echo "${PID}" > "${PID_FILE}"

sleep 2

if ! kill -0 "${PID}" 2>/dev/null; then
    echo "ERROR: Port-forward failed."
    cat "${LOG_FILE}"
    exit 1
fi

echo "PID: ${PID}"

cat "${LOG_FILE}"

echo
echo "Testing API..."

curl -fsS \
  "http://127.0.0.1:${LOCAL_PORT}/health/live"

echo
echo
echo "Phase 2M API:"
echo "http://127.0.0.1:${LOCAL_PORT}"
