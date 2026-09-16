#!/usr/bin/env bash
set -euo pipefail

echo
echo "=========================================="
echo " Phase 2P - Precheck"
echo "=========================================="

echo
echo "Existing observability:"
echo "13000 -> Grafana"
echo "19090 -> Prometheus"
echo
echo "Phase 2P:"
echo "13100 -> Loki"
echo "13200 -> Tempo"
echo "4317  -> OTLP gRPC inside Kubernetes"
echo "4318  -> OTLP HTTP inside Kubernetes"

echo
echo "API:"
kubectl get deployment \
  ai-platform-api \
  -n ai-platform

echo
echo "Ingress:"
kubectl get ingress \
  ai-platform-api \
  -n ai-platform

echo
echo "Observability namespace:"
kubectl get namespace \
  observability

echo
echo "Ingress controller ConfigMap:"
kubectl get configmap \
  ingress-nginx-controller \
  -n ingress-nginx

for PORT in 13100 13200
do

  if ss -ltn |
    grep -q ":${PORT} "
  then

    echo "ERROR: port ${PORT} already occupied"

    ss -ltnp |
      grep ":${PORT}" || true

    exit 1

  fi

  echo "PASS: port ${PORT} available"

done

echo
echo "=========================================="
echo " PHASE 2P PRECHECK: PASS"
echo "=========================================="
