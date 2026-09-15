#!/usr/bin/env bash

export KC_NAMESPACE="security"

export KC_REALM="ai-platform"
export KC_CLIENT_ID="ai-platform-api"

export KC_ADMIN_SECRET="keycloak-bootstrap-admin"

# IMPORTANT PORT ALLOCATION
#
# 8080  = Argo CD
# 18080 = Keycloak
#
export KC_LOCAL_PORT="18080"
export KC_CONTAINER_PORT="8080"

export KC_BASE_URL="http://127.0.0.1:${KC_LOCAL_PORT}"
export KC_REALM_URL="${KC_BASE_URL}/realms/${KC_REALM}"

export KC_TOKEN_ENDPOINT="${KC_REALM_URL}/protocol/openid-connect/token"
export KC_JWKS_ENDPOINT="${KC_REALM_URL}/protocol/openid-connect/certs"
export KC_DISCOVERY_ENDPOINT="${KC_REALM_URL}/.well-known/openid-configuration"

export KC_TOKEN_FILE="/tmp/ai-platform-token.json"
export KC_PF_LOG="/tmp/keycloak-port-forward-${KC_LOCAL_PORT}.log"
export KC_PF_PID_FILE="/tmp/keycloak-port-forward-${KC_LOCAL_PORT}.pid"

export KEYCLOAK_POD=$(
  kubectl get pods \
    -n "${KC_NAMESPACE}" \
    -o name |
  grep '^pod/keycloak-' |
  head -n 1 |
  cut -d/ -f2
)

if [[ -z "${KEYCLOAK_POD}" ]]; then
    echo "ERROR: Keycloak pod not found."
    return 1 2>/dev/null || exit 1
fi

echo "=========================================="
echo " AI Platform Keycloak Environment"
echo "=========================================="
echo "Namespace:      ${KC_NAMESPACE}"
echo "Realm:          ${KC_REALM}"
echo "Client:         ${KC_CLIENT_ID}"
echo "Keycloak pod:   ${KEYCLOAK_POD}"
echo "Local port:     ${KC_LOCAL_PORT}"
echo "Keycloak URL:   ${KC_BASE_URL}"
echo
echo "Reserved:"
echo "  8080  -> Argo CD"
echo "  18080 -> Keycloak"
echo "=========================================="
