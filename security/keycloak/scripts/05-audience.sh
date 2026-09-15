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

MAPPER_EXISTS=$(
  kubectl exec \
    -n "${KC_NAMESPACE}" \
    "${KEYCLOAK_POD}" -- \
    /opt/keycloak/bin/kcadm.sh get \
    "clients/${CLIENT_UUID}/protocol-mappers/models" \
    -r "${KC_REALM}" |
  python3 -c '
import json,sys
data=json.load(sys.stdin)
print("yes" if any(x.get("name")=="ai-platform-api-audience" for x in data) else "no")
'
)

if [[ "${MAPPER_EXISTS}" == "yes" ]]; then

    echo "EXISTS: ai-platform-api-audience"

else

    kubectl exec \
      -n "${KC_NAMESPACE}" \
      "${KEYCLOAK_POD}" -- \
      /opt/keycloak/bin/kcadm.sh create \
      "clients/${CLIENT_UUID}/protocol-mappers/models" \
      -r "${KC_REALM}" \
      -s name=ai-platform-api-audience \
      -s protocol=openid-connect \
      -s protocolMapper=oidc-audience-mapper \
      -s 'config."included.client.audience"="ai-platform-api"' \
      -s 'config."id.token.claim"="false"' \
      -s 'config."access.token.claim"="true"'

    echo "CREATED: ai-platform-api-audience"

fi

echo
echo "Audience mapper:"

kubectl exec \
  -n "${KC_NAMESPACE}" \
  "${KEYCLOAK_POD}" -- \
  /opt/keycloak/bin/kcadm.sh get \
  "clients/${CLIENT_UUID}/protocol-mappers/models" \
  -r "${KC_REALM}" \
  --fields name,protocolMapper
