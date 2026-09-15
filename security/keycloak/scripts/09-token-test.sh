#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/00-env.sh"

CLIENT_UUID=$(
  kubectl exec \
    -n "${KC_NAMESPACE}" \
    "${KEYCLOAK_POD}" -- \
    /opt/keycloak/bin/kcadm.sh get clients \
    -r "${KC_REALM}" \
    -q "clientId=${KC_CLIENT_ID}" |
  python3 -c 'import json,sys; print(json.load(sys.stdin)[0]["id"])'
)

CLIENT_SECRET=$(
  kubectl exec \
    -n "${KC_NAMESPACE}" \
    "${KEYCLOAK_POD}" -- \
    /opt/keycloak/bin/kcadm.sh get \
    "clients/${CLIENT_UUID}/client-secret" \
    -r "${KC_REALM}" |
  python3 -c 'import json,sys; print(json.load(sys.stdin)["value"])'
)

if ! curl -fsS "${KC_DISCOVERY_ENDPOINT}" >/dev/null; then
    echo "ERROR: Keycloak is not reachable on ${KC_BASE_URL}"
    echo "Run:"
    echo "  ./scripts/08-port-forward.sh"
    exit 1
fi

HTTP_CODE=$(
  curl -sS \
    -o "${KC_TOKEN_FILE}" \
    -w "%{http_code}" \
    -X POST \
    -u "${KC_CLIENT_ID}:${CLIENT_SECRET}" \
    "${KC_TOKEN_ENDPOINT}" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d grant_type=client_credentials
)

echo "HTTP status: ${HTTP_CODE}"

python3 - <<PY
import json
from pathlib import Path

p = Path("${KC_TOKEN_FILE}")

print("Response size:", p.stat().st_size, "bytes")

data = json.loads(p.read_text())

if "access_token" in data:
    print("TOKEN REQUEST: SUCCESS")
    print("token_type:", data.get("token_type"))
    print("expires_in:", data.get("expires_in"))
    print("scope:", data.get("scope"))
    print("access_token length:", len(data["access_token"]))
else:
    print("TOKEN REQUEST: FAILED")
    print(json.dumps(data, indent=2))
    raise SystemExit(1)
PY
