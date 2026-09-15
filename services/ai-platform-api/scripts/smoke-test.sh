#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(
  cd "$(dirname "${BASH_SOURCE[0]}")" &&
  pwd
)"

API_URL="http://127.0.0.1:8001"

echo
echo "======================================"
echo " PHASE 2L SMOKE TEST"
echo "======================================"

echo
echo "1. Liveness:"
curl -fsS "${API_URL}/health/live"
echo

echo
echo "2. Readiness:"
curl -fsS "${API_URL}/health/ready"
echo

echo
echo "3. Protected endpoint WITHOUT token:"
HTTP_CODE=$(
  curl -s \
    -o /tmp/phase2l-no-token.json \
    -w "%{http_code}" \
    "${API_URL}/api/v1/whoami"
)

echo "HTTP status: ${HTTP_CODE}"

if [[ "${HTTP_CODE}" != "401" ]]; then
    echo "FAIL: Expected HTTP 401"
    exit 1
fi

echo "PASS: unauthenticated request rejected"

echo
echo "4. Obtaining OAuth2 access token..."

ACCESS_TOKEN=$(
  "${SCRIPT_DIR}/get-token.sh"
)

echo "Token acquired: ${#ACCESS_TOKEN} characters"

echo
echo "5. Calling authenticated /whoami:"

curl -fsS \
  "${API_URL}/api/v1/whoami" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" |
python3 -m json.tool

echo
echo "6. Calling RBAC-protected inference endpoint:"

HTTP_CODE=$(
  curl -sS \
    -o /tmp/phase2l-inference.json \
    -w "%{http_code}" \
    -X POST \
    "${API_URL}/api/v1/inference" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{
      "model_name": "tax-classifier-v1",
      "input_data": {
        "transaction_amount": 125.50,
        "state": "FL"
      }
    }'
)

echo "HTTP status: ${HTTP_CODE}"

python3 -m json.tool \
  /tmp/phase2l-inference.json

if [[ "${HTTP_CODE}" != "200" ]]; then
    echo
    echo "FAIL: inference authorization failed"
    exit 1
fi

echo
echo "======================================"
echo " PHASE 2L SECURITY TEST: PASS"
echo "======================================"
