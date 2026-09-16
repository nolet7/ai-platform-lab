#!/usr/bin/env bash
set -euo pipefail

echo
echo "=========================================="
echo " PHASE 2P LOGGING + TRACING TEST"
echo "=========================================="

echo
echo "1. Backend pods..."

for APP in \
  loki \
  tempo \
  otel-collector \
  alloy
do

  READY=$(
    kubectl get deployment \
      "${APP}" \
      -n observability \
      -o jsonpath='{.status.readyReplicas}'
  )

  echo "${APP}: ready=${READY:-0}"

  if [[ "${READY:-0}" -lt 1 ]]; then
    echo "FAIL: ${APP} not ready"
    exit 1
  fi
done

echo
echo "PASS: telemetry backends ready"

echo
echo "2. Loki..."

curl -fsS \
  http://127.0.0.1:13100/ready

echo
echo "PASS: Loki ready"

echo
echo "3. Tempo..."

curl -fsS \
  http://127.0.0.1:13200/ready

echo
echo "PASS: Tempo ready"

echo
echo "4. Checking centralized FastAPI logs..."

curl -fsSG \
  http://127.0.0.1:13100/loki/api/v1/query_range \
  --data-urlencode \
  'query={namespace="ai-platform",container="ai-platform-api"} |= "http_request"' \
  --data-urlencode 'limit=10' \
| python3 -c '
import json
import sys

data = json.load(sys.stdin)

streams = (
    data.get("data", {})
        .get("result", [])
)

if not streams:
    raise SystemExit(
        "FAIL: FastAPI logs not found in Loki"
    )

count = sum(
    len(stream.get("values", []))
    for stream in streams
)

print(
    f"PASS: FastAPI logs found in Loki ({count} entries)"
)
'

echo
echo "5. Checking FastAPI traces..."

TRACE_ID=$(
  curl -fsSG \
    http://127.0.0.1:13200/api/search \
    --data-urlencode \
    'tags=service.name=ai-platform-api' \
  | python3 -c '
import json
import sys

data = json.load(sys.stdin)

traces = data.get("traces", [])

if not traces:
    raise SystemExit(
        "FAIL: FastAPI traces not found"
    )

print(
    traces[0]["traceID"]
)
'
)

echo "Trace ID: ${TRACE_ID}"
echo "PASS: FastAPI trace found"

echo
echo "6. Checking distributed trace..."

curl -fsS \
  "http://127.0.0.1:13200/api/traces/${TRACE_ID}" \
| python3 -c '
import json
import sys

data = json.load(sys.stdin)

text = json.dumps(data)

if "ai-platform-api" not in text:
    raise SystemExit(
        "FAIL: FastAPI service missing from trace"
    )

print(
    "PASS: FastAPI exists in distributed trace"
)

if "ingress-nginx" in text:
    print(
        "PASS: ingress-nginx and FastAPI are correlated"
    )
else:
    print(
        "WARN: ingress-nginx span not present in selected trace"
    )
'

echo
echo "7. Checking trace ID in Loki logs..."

curl -fsSG \
  http://127.0.0.1:13100/loki/api/v1/query_range \
  --data-urlencode \
  "query={namespace=\"ai-platform\",container=\"ai-platform-api\"} |= \"${TRACE_ID}\"" \
  --data-urlencode 'limit=20' \
| python3 -c '
import json
import sys

data = json.load(sys.stdin)

results = (
    data.get("data", {})
        .get("result", [])
)

if not results:
    raise SystemExit(
        "FAIL: trace/log correlation not found"
    )

count = sum(
    len(stream.get("values", []))
    for stream in results
)

print(
    f"PASS: trace_id correlated between Tempo and Loki ({count} log entries)"
)
'

echo
echo "8. Grafana data sources..."

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

for DS_UID in loki tempo
do

  curl -fsS \
    -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
    "http://127.0.0.1:13000/api/datasources/uid/${DS_UID}" \
    >/dev/null

  echo "PASS: Grafana datasource ${DS_UID}"

done

unset GRAFANA_PASSWORD

echo
echo "=========================================="
echo " PHASE 2P LOGGING + TRACING TEST: PASS"
echo "=========================================="
