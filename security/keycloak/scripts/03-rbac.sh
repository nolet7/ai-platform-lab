#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/00-env.sh"

ROLES=(
  "platform-admin"
  "ml-engineer"
  "data-scientist"
  "inference-client"
)

for ROLE in "${ROLES[@]}"; do

    if kubectl exec \
      -n "${KC_NAMESPACE}" \
      "${KEYCLOAK_POD}" -- \
      /opt/keycloak/bin/kcadm.sh get "roles/${ROLE}" \
      -r "${KC_REALM}" \
      >/dev/null 2>&1
    then
        echo "EXISTS: ${ROLE}"

    else

        kubectl exec \
          -n "${KC_NAMESPACE}" \
          "${KEYCLOAK_POD}" -- \
          /opt/keycloak/bin/kcadm.sh create roles \
          -r "${KC_REALM}" \
          -s "name=${ROLE}"

        echo "CREATED: ${ROLE}"
    fi

done

echo
echo "Realm roles:"
kubectl exec \
  -n "${KC_NAMESPACE}" \
  "${KEYCLOAK_POD}" -- \
  /opt/keycloak/bin/kcadm.sh get roles \
  -r "${KC_REALM}" \
  --fields name
