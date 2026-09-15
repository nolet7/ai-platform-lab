#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/00-env.sh"

SERVICE_ACCOUNT="service-account-${KC_CLIENT_ID}"

CLIENT_UUID=$(
  kubectl exec \
    -n "${KC_NAMESPACE}" \
    "${KEYCLOAK_POD}" -- \
    /opt/keycloak/bin/kcadm.sh get clients \
    -r "${KC_REALM}" \
    -q "clientId=${KC_CLIENT_ID}" |
  python3 -c 'import json,sys; print(json.load(sys.stdin)[0]["id"])'
)

echo "Service account:"

kubectl exec \
  -n "${KC_NAMESPACE}" \
  "${KEYCLOAK_POD}" -- \
  /opt/keycloak/bin/kcadm.sh get \
  "clients/${CLIENT_UUID}/service-account-user" \
  -r "${KC_REALM}" \
  --fields id,username,enabled

HAS_ROLE=$(
  kubectl exec \
    -n "${KC_NAMESPACE}" \
    "${KEYCLOAK_POD}" -- \
    /opt/keycloak/bin/kcadm.sh get-roles \
    -r "${KC_REALM}" \
    --uusername "${SERVICE_ACCOUNT}" |
  python3 -c '
import json,sys
data=json.load(sys.stdin)
print("yes" if any(x.get("name")=="inference-client" for x in data) else "no")
'
)

if [[ "${HAS_ROLE}" == "yes" ]]; then

    echo "EXISTS: inference-client assignment"

else

    kubectl exec \
      -n "${KC_NAMESPACE}" \
      "${KEYCLOAK_POD}" -- \
      /opt/keycloak/bin/kcadm.sh add-roles \
      -r "${KC_REALM}" \
      --uusername "${SERVICE_ACCOUNT}" \
      --rolename inference-client

    echo "ASSIGNED: inference-client"

fi

echo
echo "Service-account roles:"

kubectl exec \
  -n "${KC_NAMESPACE}" \
  "${KEYCLOAK_POD}" -- \
  /opt/keycloak/bin/kcadm.sh get-roles \
  -r "${KC_REALM}" \
  --uusername "${SERVICE_ACCOUNT}"
