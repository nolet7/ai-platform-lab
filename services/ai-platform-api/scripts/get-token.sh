#!/usr/bin/env bash
set -euo pipefail

KC_NAMESPACE="security"
KC_REALM="ai-platform"
KC_CLIENT_ID="ai-platform-api"

KC_URL="http://127.0.0.1:18080"

KEYCLOAK_POD=$(
  kubectl get pods \
    -n "${KC_NAMESPACE}" \
    -o name |
  grep '^pod/keycloak-' |
  head -n 1 |
  cut -d/ -f2
)

if [[ -z "${KEYCLOAK_POD}" ]]; then
    echo "ERROR: Keycloak pod not found."
    exit 1
fi

CLIENT_UUID=$(
  kubectl exec \
    -n "${KC_NAMESPACE}" \
    "${KEYCLOAK_POD}" -- \
    /opt/keycloak/bin/kcadm.sh get clients \
    -r "${KC_REALM}" \
    -q "clientId=${KC_CLIENT_ID}" |
  python3 -c '
import json,sys
data=json.load(sys.stdin)
print(data[0]["id"] if data else "")
'
)

if [[ -z "${CLIENT_UUID}" ]]; then
    echo "ERROR: ai-platform-api client not found."
    exit 1
fi

CLIENT_SECRET=$(
  kubectl exec \
    -n "${KC_NAMESPACE}" \
    "${KEYCLOAK_POD}" -- \
    /opt/keycloak/bin/kcadm.sh get \
    "clients/${CLIENT_UUID}/client-secret" \
    -r "${KC_REALM}" |
  python3 -c '
import json,sys
print(json.load(sys.stdin)["value"])
'
)

TOKEN_RESPONSE=$(
  curl -fsS \
    -X POST \
    -u "${KC_CLIENT_ID}:${CLIENT_SECRET}" \
    "${KC_URL}/realms/${KC_REALM}/protocol/openid-connect/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d grant_type=client_credentials
)

ACCESS_TOKEN=$(
  printf '%s' "${TOKEN_RESPONSE}" |
  python3 -c '
import json,sys
print(json.load(sys.stdin)["access_token"])
'
)

if [[ -z "${ACCESS_TOKEN}" ]]; then
    echo "ERROR: Token was not returned."
    exit 1
fi

printf '%s' "${ACCESS_TOKEN}"
