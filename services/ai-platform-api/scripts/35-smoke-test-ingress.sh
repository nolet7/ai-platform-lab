#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(
  cd "$(dirname "${BASH_SOURCE[0]}")" &&
  pwd
)"

HOST="api.ai-platform.local"

echo
echo "=========================================="
echo " PHASE 2N INGRESS SECURITY TEST"
echo "=========================================="

echo
echo "Port inventory:"
echo "8080   -> Argo CD"
echo "18080  -> Keycloak"
echo "8001   -> local Phase 2L API"
echo "18081  -> old Phase 2M API port-forward"
echo
echo "Phase 2N uses Kind node IP ports 80/443."
echo "No new local port-forward."

echo
echo "1. Finding ingress controller..."

INGRESS_POD=$(
  kubectl get pods \
    -n ingress-nginx \
    -l app.kubernetes.io/component=controller \
    -o jsonpath='{.items[0].metadata.name}'
)

if [[ -z "${INGRESS_POD}" ]]; then
    echo "FAIL: ingress controller pod not found"
    exit 1
fi

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

if [[ -z "${INGRESS_IP}" ]]; then
    echo "FAIL: Unable to determine Kind node IP"
    exit 1
fi

echo "Ingress pod:  ${INGRESS_POD}"
echo "Ingress node: ${INGRESS_NODE}"
echo "Ingress IP:   ${INGRESS_IP}"

echo
echo "2. Testing HTTP -> HTTPS redirect..."

HTTP_CODE=$(
  curl -s \
    -o /dev/null \
    -w "%{http_code}" \
    --resolve "${HOST}:80:${INGRESS_IP}" \
    "http://${HOST}/health/live"
)

echo "HTTP status: ${HTTP_CODE}"

if [[ "${HTTP_CODE}" != "308" \
   && "${HTTP_CODE}" != "301" \
   && "${HTTP_CODE}" != "302" ]]
then
    echo "FAIL: HTTP was not redirected to HTTPS"
    exit 1
fi

echo "PASS: HTTP redirects to HTTPS"

echo
echo "3. Testing HTTPS liveness..."

curl -kfsS \
  --resolve "${HOST}:443:${INGRESS_IP}" \
  "https://${HOST}/health/live" |
python3 -m json.tool

echo "PASS: HTTPS liveness"

echo
echo "4. Testing HTTPS readiness..."

curl -kfsS \
  --resolve "${HOST}:443:${INGRESS_IP}" \
  "https://${HOST}/health/ready" |
python3 -m json.tool

echo "PASS: HTTPS readiness"

echo
echo "5. Testing protected endpoint WITHOUT token..."

HTTP_CODE=$(
  curl -ks \
    -o /tmp/phase2n-no-token.json \
    -w "%{http_code}" \
    --resolve "${HOST}:443:${INGRESS_IP}" \
    "https://${HOST}/api/v1/whoami"
)

echo "HTTP status: ${HTTP_CODE}"

if [[ "${HTTP_CODE}" != "401" ]]; then
    echo "FAIL: Expected HTTP 401"
    cat /tmp/phase2n-no-token.json
    exit 1
fi

echo "PASS: unauthenticated request rejected"

echo
echo "6. Checking Keycloak..."

if ! curl -fsS \
  "http://127.0.0.1:18080/realms/ai-platform/.well-known/openid-configuration" \
  >/dev/null 2>&1
then

    echo "ERROR: Keycloak port-forward on 18080 is not running."
    echo
    echo "Start it with:"
    echo "cd ~/ai-platform-lab/security/keycloak"
    echo "./scripts/08-port-forward.sh"
    exit 1
fi

echo "PASS: Keycloak reachable"

echo
echo "7. Obtaining OAuth2 access token..."

ACCESS_TOKEN=$(
  "${SCRIPT_DIR}/get-token.sh"
)

echo "Token acquired: ${#ACCESS_TOKEN} characters"

echo
echo "8. Testing authenticated /whoami through Ingress..."

HTTP_CODE=$(
  curl -ksS \
    -o /tmp/phase2n-whoami.json \
    -w "%{http_code}" \
    --resolve "${HOST}:443:${INGRESS_IP}" \
    "https://${HOST}/api/v1/whoami" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}"
)

echo "HTTP status: ${HTTP_CODE}"

python3 -m json.tool \
  /tmp/phase2n-whoami.json

if [[ "${HTTP_CODE}" != "200" ]]; then
    echo "FAIL: JWT request through ingress failed"
    exit 1
fi

echo "PASS: JWT validated through ingress"

echo
echo "9. Testing RBAC inference through HTTPS Ingress..."

HTTP_CODE=$(
  curl -ksS \
    -o /tmp/phase2n-inference.json \
    -w "%{http_code}" \
    --resolve "${HOST}:443:${INGRESS_IP}" \
    -X POST \
    "https://${HOST}/api/v1/inference" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{
      "model_name": "tax-classifier-v1",
      "input_data": {
        "transaction_amount": 725.25,
        "state": "FL",
        "product_category": "software"
      }
    }'
)

echo "HTTP status: ${HTTP_CODE}"

python3 -m json.tool \
  /tmp/phase2n-inference.json

if [[ "${HTTP_CODE}" != "200" ]]; then
    echo "FAIL: inference request failed"
    exit 1
fi

echo "PASS: inference-client authorized through ingress"

echo
echo "10. Checking TLS certificate..."

echo |
openssl s_client \
  -connect "${INGRESS_IP}:443" \
  -servername "${HOST}" \
  2>/dev/null |
openssl x509 \
  -noout \
  -subject \
  -issuer \
  -dates

echo
echo "=========================================="
echo " PHASE 2N INGRESS SECURITY TEST: PASS"
echo "=========================================="
