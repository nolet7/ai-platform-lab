#!/usr/bin/env bash
set -euo pipefail

echo
echo "=========================================="
echo " PHASE 2O OBSERVABILITY TEST"
echo "=========================================="

echo
echo "1. Checking API pods..."

kubectl get pods \
  -n ai-platform \
  -l app.kubernetes.io/name=ai-platform-api

echo
echo "2. Checking metrics port..."

kubectl get svc \
  ai-platform-api \
  -n ai-platform \
  -o jsonpath='{range .spec.ports[*]}{.name}={.port}{"\n"}{end}'

echo
echo "3. Checking ServiceMonitor..."

kubectl get servicemonitor \
  ai-platform-api \
  -n ai-platform

echo
echo "4. Checking Prometheus target..."

RESULT=$(
  curl -sG \
    http://127.0.0.1:19090/api/v1/query \
    --data-urlencode \
    'query=up{namespace="ai-platform",service="ai-platform-api"}'
)

python3 - <<PY
import json

data = json.loads('''${RESULT}''')

results = data["data"]["result"]

if not results:
    raise SystemExit(
        "FAIL: Prometheus has no AI Platform API targets"
    )

values = [
    float(x["value"][1])
    for x in results
]

print("Target values:", values)

if not all(v == 1 for v in values):
    raise SystemExit(
        "FAIL: One or more targets are down"
    )

print("PASS: Prometheus scraping AI Platform API")
PY

echo
echo "5. Checking request metric..."

curl -sG \
  http://127.0.0.1:19090/api/v1/query \
  --data-urlencode \
  'query=sum(ai_platform_http_requests_total{namespace="ai-platform"})' |
python3 -c '
import json,sys

data=json.load(sys.stdin)
result=data["data"]["result"]

if not result:
    raise SystemExit(
        "FAIL: request metric missing"
    )

print(
    "Request count:",
    result[0]["value"][1]
)

print(
    "PASS: request metric available"
)
'

echo
echo "6. Checking authentication metric..."

curl -sG \
  http://127.0.0.1:19090/api/v1/query \
  --data-urlencode \
  'query=sum(ai_platform_auth_failures_total{namespace="ai-platform"})' |
python3 -c '
import json,sys

data=json.load(sys.stdin)
result=data["data"]["result"]

if not result:
    raise SystemExit(
        "FAIL: auth metric missing"
    )

print(
    "Authentication failures:",
    result[0]["value"][1]
)

print(
    "PASS: auth metric available"
)
'

echo
echo "7. Checking RBAC metric..."

curl -sG \
  http://127.0.0.1:19090/api/v1/query \
  --data-urlencode \
  'query=sum(ai_platform_rbac_denials_total{namespace="ai-platform"})' |
python3 -c '
import json,sys

data=json.load(sys.stdin)
result=data["data"]["result"]

if not result:
    raise SystemExit(
        "FAIL: RBAC metric missing"
    )

print(
    "RBAC denials:",
    result[0]["value"][1]
)

print(
    "PASS: RBAC metric available"
)
'

echo
echo "8. Checking Prometheus alert rules..."

kubectl get prometheusrule \
  ai-platform-api \
  -n ai-platform

echo
echo "PASS: alert rules installed"

echo
echo "9. Checking Grafana dashboard..."

GRAFANA_USER=$(
  kubectl get secret \
    grafana-admin \
    -n observability \
    -o jsonpath='{.data.admin-user}' |
  base64 -d
)

GRAFANA_PASSWORD=$(
  kubectl get secret \
    grafana-admin \
    -n observability \
    -o jsonpath='{.data.admin-password}' |
  base64 -d
)

DASHBOARD_RESULT=$(
  curl -fsS \
    -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
    --get \
    http://127.0.0.1:13000/api/search \
    --data-urlencode \
    'query=AI Platform API'
)

python3 - <<PY
import json

data=json.loads('''${DASHBOARD_RESULT}''')

if not any(
    x.get("uid") == "ai-platform-api"
    for x in data
):
    raise SystemExit(
        "FAIL: Grafana dashboard not loaded"
    )

print(
    "PASS: Grafana dashboard loaded"
)
PY

unset GRAFANA_PASSWORD

echo
echo "10. Checking structured logs..."

LOGS=$(
  kubectl logs \
    -n ai-platform \
    -l app.kubernetes.io/name=ai-platform-api \
    --tail=100
)

if ! grep -q '"event":"http_request"' <<< "${LOGS}"
then
    echo "FAIL: structured request logs missing"
    exit 1
fi

echo "PASS: JSON structured logs available"

echo
echo "=========================================="
echo " PHASE 2O OBSERVABILITY TEST: PASS"
echo "=========================================="
