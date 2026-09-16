#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(
  cd "$(dirname "${BASH_SOURCE[0]}")" &&
  pwd
)"

HOST="api.ai-platform.local"


INGRESS_POD=$(
  kubectl get pods \
    -n ingress-nginx \
    -l app.kubernetes.io/component=controller \
    -o jsonpath='{.items[0].metadata.name}'
)


INGRESS_NODE=$(
  kubectl get pod \
    "${INGRESS_POD}" \
    -n ingress-nginx \
    -o jsonpath='{.spec.nodeName}'
)


INGRESS_IP=$(
  docker inspect \
    -f '{{with index .NetworkSettings.Networks "kind"}}{{.IPAddress}}{{end}}' \
    "${INGRESS_NODE}"
)


echo "Ingress IP: ${INGRESS_IP}"

echo
echo "Restarting API to clear JWKS cache..."

kubectl rollout restart \
  deployment/ai-platform-api \
  -n ai-platform

kubectl rollout status \
  deployment/ai-platform-api \
  -n ai-platform \
  --timeout=240s


echo
echo "Obtaining Keycloak token..."

ACCESS_TOKEN=$(
  "${SCRIPT_DIR}/get-token.sh"
)


echo "Token loaded: ${#ACCESS_TOKEN} characters"

echo
echo "Generating traced requests..."


for i in $(seq 1 10)
do

  curl -kfsS \
    --resolve "${HOST}:443:${INGRESS_IP}" \
    "https://${HOST}/api/v1/whoami" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    >/dev/null

done


for i in $(seq 1 10)
do

  curl -kfsS \
    --resolve "${HOST}:443:${INGRESS_IP}" \
    -X POST \
    "https://${HOST}/api/v1/inference" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{
      "model_name": "tax-classifier-v1",
      "input_data": {
        "transaction_amount": 999.50,
        "state": "FL",
        "source": "phase-2p"
      }
    }' \
    >/dev/null

done


echo
echo "Capturing one trace ID..."

curl -kisS \
  --resolve "${HOST}:443:${INGRESS_IP}" \
  "https://${HOST}/api/v1/whoami" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  | grep -i '^x-trace-id:' || true


echo
echo "Phase 2P traced traffic complete."
