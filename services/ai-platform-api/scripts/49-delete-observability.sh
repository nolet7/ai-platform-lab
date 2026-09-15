#!/usr/bin/env bash
set -euo pipefail

echo
echo "Deleting application monitoring resources..."

kubectl delete \
  -k k8s/observability \
  --ignore-not-found=true

echo
echo "Removing monitoring stack..."

helm uninstall \
  kube-prometheus-stack \
  -n observability \
  --ignore-not-found

echo
echo "Deleting observability namespace..."

kubectl delete namespace \
  observability \
  --ignore-not-found=true

echo
echo "NOT deleted:"
echo "  ai-platform namespace"
echo "  FastAPI deployment"
echo "  Keycloak"
echo "  ingress-nginx"
echo "  Argo CD"
echo "  Kind cluster"
