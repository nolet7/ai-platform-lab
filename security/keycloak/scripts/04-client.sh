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
  python3 -c '
import json,sys
data=json.load(sys.stdin)
print(data[0]["id"] if data else "")
'
)

if [[ -z "${CLIENT_UUID}" ]]; then

    echo "Creating ${KC_CLIENT_ID}..."

    kubectl exec \
      -n "${KC_NAMESPACE}" \
      "${KEYCLOAK_POD}" -- \
      /opt/keycloak/bin/kcadm.sh create clients \
      -r "${KC_REALM}" \
      -s "clientId=${KC_CLIENT_ID}" \
      -s 'name=AI Platform API' \
      -s enabled=true \
      -s protocol=openid-connect \
      -s publicClient=false \
      -s bearerOnly=false \
      -s clientAuthenticatorType=client-secret \
      -s serviceAccountsEnabled=true \
      -s standardFlowEnabled=false \
      -s directAccessGrantsEnabled=false

    CLIENT_UUID=$(
      kubectl exec \
        -n "${KC_NAMESPACE}" \
        "${KEYCLOAK_POD}" -- \
        /opt/keycloak/bin/kcadm.sh get clients \
        -r "${KC_REALM}" \
        -q "clientId=${KC_CLIENT_ID}" |
      python3 -c '
import json,sys
print(json.load(sys.stdin)[0]["id"])
'
    )
fi

echo "Client UUID: ${CLIENT_UUID}"

kubectl exec \
  -n "${KC_NAMESPACE}" \
  "${KEYCLOAK_POD}" -- \
  /opt/keycloak/bin/kcadm.sh update \
  "clients/${CLIENT_UUID}" \
  -r "${KC_REALM}" \
  -s enabled=true \
  -s publicClient=false \
  -s bearerOnly=false \
  -s clientAuthenticatorType=client-secret \
  -s serviceAccountsEnabled=true \
  -s standardFlowEnabled=false \
  -s directAccessGrantsEnabled=false

echo
echo "Client configuration:"

kubectl exec \
  -n "${KC_NAMESPACE}" \
  "${KEYCLOAK_POD}" -- \
  /opt/keycloak/bin/kcadm.sh get \
  "clients/${CLIENT_UUID}" \
  -r "${KC_REALM}" \
  --fields \
clientId,enabled,publicClient,bearerOnly,serviceAccountsEnabled,standardFlowEnabled,directAccessGrantsEnabled,clientAuthenticatorType
