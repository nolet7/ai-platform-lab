#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/00-env.sh"

if kubectl exec \
  -n "${KC_NAMESPACE}" \
  "${KEYCLOAK_POD}" -- \
  /opt/keycloak/bin/kcadm.sh get "realms/${KC_REALM}" \
  >/dev/null 2>&1
then
    echo "EXISTS: realm ${KC_REALM}"
else
    kubectl exec \
      -n "${KC_NAMESPACE}" \
      "${KEYCLOAK_POD}" -- \
      /opt/keycloak/bin/kcadm.sh create realms \
      -s "realm=${KC_REALM}" \
      -s enabled=true \
      -s 'displayName=AI Platform'

    echo "CREATED: realm ${KC_REALM}"
fi

kubectl exec \
  -n "${KC_NAMESPACE}" \
  "${KEYCLOAK_POD}" -- \
  /opt/keycloak/bin/kcadm.sh get "realms/${KC_REALM}" \
  --fields realm,enabled,defaultSignatureAlgorithm,sslRequired
