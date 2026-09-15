#!/usr/bin/env bash
set -euo pipefail

echo
echo "=========================================="
echo " Phase 2O - Observability Precheck"
echo "=========================================="

echo
echo "Port inventory:"
echo "80/443 -> ingress-nginx"
echo "8001   -> Local Phase 2L API"
echo "8080   -> Argo CD"
echo "18080  -> Keycloak"
echo "18081  -> FREE"
echo "13000  -> Grafana (Phase 2O)"
echo "19090  -> Prometheus (Phase 2O)"
echo "9091   -> Internal FastAPI metrics"

echo
echo "Checking commands..."

for CMD in \
  kubectl \
  docker \
  kind \
  helm \
  openssl \
  python3 \
  curl
do
    if ! command -v "${CMD}" >/dev/null 2>&1
    then
        echo "ERROR: ${CMD} not found"
        exit 1
    fi

    echo "PASS: ${CMD}"
done

echo
echo "Checking Kubernetes..."

kubectl get nodes

echo
echo "Checking API deployment..."

kubectl get deployment \
  ai-platform-api \
  -n ai-platform

echo
echo "Checking ingress..."

kubectl get ingress \
  ai-platform-api \
  -n ai-platform

echo
echo "Checking Phase 2O local ports..."

for PORT in 13000 19090
do
    if ss -ltn |
      grep -q ":${PORT} "
    then
        echo "ERROR: Port ${PORT} already occupied"

        ss -ltnp |
          grep ":${PORT}" || true

        exit 1
    fi

    echo "PASS: ${PORT} available"
done

echo
echo "=========================================="
echo " PHASE 2O PRECHECK: PASS"
echo "=========================================="
