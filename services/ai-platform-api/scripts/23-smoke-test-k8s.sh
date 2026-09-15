#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(
  cd "$(dirname "${BASH_SOURCE[0]}")" &&
  pwd
)"

API_URL="http://127.0.0.1:18081"

echo
echo "=========================================="
echo " PHASE 2M KUBERNETES SECURITY TEST"
echo "=========================================="

echo
echo "Port inventory:"
echo "8080   -> Argo CD"
echo "18080  -> Keycloak"
echo "8001   -> Local Phase 2L API"
echo "18081  -> Kubernetes Phase 2M API"

echo
echo "1. Checking Keycloak host port-forward..."

if ! curl -fsS \
  "http://127.0.0.1:18080/realms/ai-platform/.well-known/openid-configuration" \
  >/dev/null
then
    echo "ERROR: Keycloak is not reachable on port 18080."
    exit 1
fi

echo "PASS: Keycloak reachable"

echo
echo "2. Checking Kubernetes API..."

if ! curl -fsS \
  "${API_URL}/health/live" \
  >/dev/null 2>&1
then
    echo "Starting Phase 2M port-forward..."

    "${SCRIPT_DIR}/22-port-forward-k8s.sh"

    sleep 2
fi

echo
echo "3. Liveness"

curl -fsS \
  "${API_URL}/health/live" |
python3 -m json.tool

echo
echo "PASS: liveness"

echo
echo "4. Readiness"

curl -fsS \
  "${API_URL}/health/ready" |
python3 -m json.tool

echo
echo "PASS: readiness"

echo
echo "5. Protected endpoint WITHOUT token"

HTTP_CODE=$(
  curl -s \
    -o /tmp/phase2m-no-token.json \
    -w "%{http_code}" \
    "${API_URL}/api/v1/whoami"
)

echo "HTTP status: ${HTTP_CODE}"

if [[ "${HTTP_CODE}" != "401" ]]; then
    echo "FAIL: Expected HTTP 401"
    cat /tmp/phase2m-no-token.json
    exit 1
fi

echo "PASS: unauthenticated request rejected"

echo
echo "6. Acquiring OAuth2 Client Credentials token"

ACCESS_TOKEN=$(
  "${SCRIPT_DIR}/get-token.sh"
)

echo "Token acquired: ${#ACCESS_TOKEN} characters"

echo
echo "7. Testing JWT inside Kubernetes"

HTTP_CODE=$(
  curl -sS \
    -o /tmp/phase2m-whoami.json \
    -w "%{http_code}" \
    "${API_URL}/api/v1/whoami" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}"
)

echo "HTTP status: ${HTTP_CODE}"

python3 -m json.tool \
  /tmp/phase2m-whoami.json

if [[ "${HTTP_CODE}" != "200" ]]; then
    echo "FAIL: JWT validation inside Kubernetes failed"
    exit 1
fi

echo
echo "PASS: JWT validated inside Kubernetes"

echo
echo "8. Testing inference-client RBAC"

HTTP_CODE=$(
  curl -sS \
    -o /tmp/phase2m-inference.json \
    -w "%{http_code}" \
    -X POST \
    "${API_URL}/api/v1/inference" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{
      "model_name": "tax-classifier-v1",
      "input_data": {
        "transaction_amount": 425.75,
        "state": "FL",
        "product_category": "software"
      }
    }'
)

echo "HTTP status: ${HTTP_CODE}"

python3 -m json.tool \
  /tmp/phase2m-inference.json

if [[ "${HTTP_CODE}" != "200" ]]; then
    echo "FAIL: Kubernetes inference authorization failed"
    exit 1
fi

echo
echo "PASS: inference-client authorized"

echo
echo "=========================================="
echo " PHASE 2M SECURITY TEST: PASS"
echo "=========================================="
