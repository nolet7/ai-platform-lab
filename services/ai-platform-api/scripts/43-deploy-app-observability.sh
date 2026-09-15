#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.." &&
  pwd
)"

echo
echo "=========================================="
echo " Deploying AI Platform Observability"
echo "=========================================="

if ! kubectl get crd \
  servicemonitors.monitoring.coreos.com \
  >/dev/null 2>&1
then
    echo "ERROR: ServiceMonitor CRD missing."
    echo "Run ./scripts/41-install-monitoring-stack.sh"
    exit 1
fi

kubectl apply \
  -k "${PROJECT_DIR}/k8s/observability"

echo
echo "ServiceMonitor:"

kubectl get servicemonitor \
  ai-platform-api \
  -n ai-platform

echo
echo "PrometheusRule:"

kubectl get prometheusrule \
  ai-platform-api \
  -n ai-platform

echo
echo "Dashboard ConfigMap:"

kubectl get configmap \
  ai-platform-api-dashboard \
  -n ai-platform

echo
echo "NetworkPolicy:"

kubectl get networkpolicy \
  allow-prometheus-to-ai-platform-api \
  -n ai-platform

echo
echo "=========================================="
echo " APP OBSERVABILITY DEPLOYED"
echo "=========================================="
