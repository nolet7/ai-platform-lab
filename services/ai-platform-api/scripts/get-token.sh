#!/usr/bin/env bash
set -euo pipefail

KC_NAMESPACE="security"
KC_REALM="ai-platform"
KC_CLIENT_ID="ai-platform-api"

KC_URL="http://127.0.0.1:18080"

KC_ADMIN_SECRET="keycloak-bootstrap-admin"

KEYCLOAK_POD=$(
  kubectl get pods \
    -n "${KC_NAMESPACE}" \
    -o name |
  grep '^pod/keycloak-' |
  head -n 1 |
  cut -d/ -f2
)

if [[ -z "${KEYCLOAK_POD}" ]]; then
    echo "ERROR: Keycloak pod not found." >&2
    exit 1
fi


# Verify the host Keycloak port-forward is running.
if ! curl -fsS \
  "${KC_URL}/realms/${KC_REALM}/.well-known/openid-configuration" \
  >/dev/null 2>&1
then
    echo "ERROR: Keycloak is not reachable on ${KC_URL}" >&2
    echo "Start the Keycloak port-forward first:" >&2
    echo "cd ~/ai-platform-lab/security/keycloak" >&2
    echo "./scripts/08-port-forward.sh" >&2
    exit 1
fi


# Refresh Keycloak admin authentication every time.
KC_ADMIN_USER=$(
  kubectl get secret \
    "${KC_ADMIN_SECRET}" \
    -n "${KC_NAMESPACE}" \
    -o jsonpath='{.data.KC_BOOTSTRAP_ADMIN_USERNAME}' |
  base64 -d
)

KC_ADMIN_PASSWORD=$(
  kubectl get secret \
    "${KC_ADMIN_SECRET}" \
    -n "${KC_NAMESPACE}" \
    -o jsonpath='{.data.KC_BOOTSTRAP_ADMIN_PASSWORD}' |
  base64 -d
)


kubectl exec \
  -n "${KC_NAMESPACE}" \
  "${KEYCLOAK_POD}" -- \
  /opt/keycloak/bin/kcadm.sh config credentials \
  --server http://localhost:8080 \
  --realm master \
  --user "${KC_ADMIN_USER}" \
  --password "${KC_ADMIN_PASSWORD}" \
  >/dev/null


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

if not data:
    raise SystemExit("Client not found")

print(data[0]["id"])
'
)


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

data=json.load(sys.stdin)

token=data.get("access_token")

if not token:
    raise SystemExit("Access token missing")

print(token)
'
)


# stdout intentionally contains ONLY the token,
# because other scripts capture this command.
printf '%s' "${ACCESS_TOKEN}"
