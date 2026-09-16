#!/usr/bin/env bash
set -euo pipefail

kubectl delete \
  -k "$HOME/ai-platform-lab/observability/phase-2p" \
  --ignore-not-found=true


kubectl annotate ingress \
  ai-platform-api \
  -n ai-platform \
  nginx.ingress.kubernetes.io/enable-opentelemetry- \
  nginx.ingress.kubernetes.io/opentelemetry-trust-incoming-span- \
  2>/dev/null || true


kubectl patch configmap \
  ingress-nginx-controller \
  -n ingress-nginx \
  --type merge \
  -p '{
    "data": {
      "enable-opentelemetry": "false"
    }
  }'


echo
echo "Phase 2P telemetry resources removed."
echo
echo "Phase 2O Prometheus/Grafana retained."
echo "Keycloak retained."
echo "Ingress retained."
