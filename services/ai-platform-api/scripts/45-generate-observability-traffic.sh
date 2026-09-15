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
echo "Obtaining token..."

ACCESS_TOKEN=$(
  "${SCRIPT_DIR}/get-token.sh"
)

echo "Token loaded: ${#ACCESS_TOKEN} characters"

echo
echo "Generating health traffic..."

for i in $(seq 1 20)
do
  curl -kfsS \
    --resolve "${HOST}:443:${INGRESS_IP}" \
    "https://${HOST}/health/live" \
    >/dev/null
done

echo "Generating authenticated traffic..."

for i in $(seq 1 10)
do
  curl -kfsS \
    --resolve "${HOST}:443:${INGRESS_IP}" \
    "https://${HOST}/api/v1/whoami" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    >/dev/null
done

echo "Generating inference traffic..."

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
        "transaction_amount": 125.50,
        "state": "FL"
      }
    }' \
    >/dev/null
done

echo "Generating missing-token authentication failures..."

for i in $(seq 1 5)
do
  curl -ks \
    --resolve "${HOST}:443:${INGRESS_IP}" \
    "https://${HOST}/api/v1/whoami" \
    >/dev/null
done

echo "Generating invalid-token failures..."

for i in $(seq 1 5)
do
  curl -ks \
    --resolve "${HOST}:443:${INGRESS_IP}" \
    "https://${HOST}/api/v1/whoami" \
    -H "Authorization: Bearer invalid-token" \
    >/dev/null
done

echo "Generating RBAC denials..."

for i in $(seq 1 5)
do
  curl -ks \
    --resolve "${HOST}:443:${INGRESS_IP}" \
    "https://${HOST}/api/v1/admin/status" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    >/dev/null
done

echo
echo "Traffic generation complete."
