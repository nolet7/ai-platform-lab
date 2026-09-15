#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/00-env.sh"

export CLIENT_UUID=$(
  kubectl exec \
    -n "${KC_NAMESPACE}" \
    "${KEYCLOAK_POD}" -- \
    /opt/keycloak/bin/kcadm.sh get clients \
    -r "${KC_REALM}" \
    -q "clientId=${KC_CLIENT_ID}" |
  python3 -c 'import json,sys; print(json.load(sys.stdin)[0]["id"])'
)

export CLIENT_SECRET=$(
  kubectl exec \
    -n "${KC_NAMESPACE}" \
    "${KEYCLOAK_POD}" -- \
    /opt/keycloak/bin/kcadm.sh get \
    "clients/${CLIENT_UUID}/client-secret" \
    -r "${KC_REALM}" |
  python3 -c 'import json,sys; print(json.load(sys.stdin)["value"])'
)

echo "CLIENT_UUID=${CLIENT_UUID}"
echo "Client secret loaded: ${#CLIENT_SECRET} characters"
echo "Secret value intentionally not displayed."
