#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/00-env.sh"

export KC_ADMIN_USER=$(
  kubectl get secret "${KC_ADMIN_SECRET}" \
    -n "${KC_NAMESPACE}" \
    -o jsonpath='{.data.KC_BOOTSTRAP_ADMIN_USERNAME}' |
  base64 -d
)

export KC_ADMIN_PASSWORD=$(
  kubectl get secret "${KC_ADMIN_SECRET}" \
    -n "${KC_NAMESPACE}" \
    -o jsonpath='{.data.KC_BOOTSTRAP_ADMIN_PASSWORD}' |
  base64 -d
)

echo "Admin user: ${KC_ADMIN_USER}"
echo "Password loaded: ${#KC_ADMIN_PASSWORD} characters"

kubectl exec \
  -n "${KC_NAMESPACE}" \
  "${KEYCLOAK_POD}" -- \
  /opt/keycloak/bin/kcadm.sh config credentials \
  --server http://localhost:8080 \
  --realm master \
  --user "${KC_ADMIN_USER}" \
  --password "${KC_ADMIN_PASSWORD}"

echo
echo "Keycloak administrative authentication successful."
