#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/00-env.sh"

echo "Port allocation:"
echo "  8080  -> Argo CD"
echo "  18080 -> Keycloak"
echo

if ss -ltn | grep -q ":${KC_LOCAL_PORT} "; then

    echo "Port ${KC_LOCAL_PORT} is already listening."

    if curl -fsS \
      "${KC_DISCOVERY_ENDPOINT}" \
      >/dev/null 2>&1
    then
        echo "Existing Keycloak forward appears healthy."
        exit 0
    fi

    echo "ERROR: Port ${KC_LOCAL_PORT} is occupied by another process."
    ss -ltnp | grep ":${KC_LOCAL_PORT}" || true
    exit 1
fi

kubectl port-forward \
  -n "${KC_NAMESPACE}" \
  "${KEYCLOAK_POD}" \
  "${KC_LOCAL_PORT}:${KC_CONTAINER_PORT}" \
  >"${KC_PF_LOG}" 2>&1 &

KC_PF_PID=$!

echo "${KC_PF_PID}" > "${KC_PF_PID_FILE}"

sleep 2

if ! kill -0 "${KC_PF_PID}" 2>/dev/null; then
    echo "ERROR: Keycloak port-forward failed."
    cat "${KC_PF_LOG}"
    exit 1
fi

echo "Keycloak port-forward PID: ${KC_PF_PID}"
cat "${KC_PF_LOG}"

echo
echo "Testing OIDC discovery..."

curl -fsS "${KC_DISCOVERY_ENDPOINT}" |
python3 -c '
import json,sys

d=json.load(sys.stdin)

print("issuer:", d["issuer"])
print("token_endpoint:", d["token_endpoint"])
print("jwks_uri:", d["jwks_uri"])
'
