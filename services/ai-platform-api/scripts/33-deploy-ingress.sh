#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.." &&
  pwd
)"

INGRESS_DIR="${PROJECT_DIR}/k8s/ingress"

echo
echo "=========================================="
echo " Phase 2N - Deploy Ingress"
echo "=========================================="

if ! kubectl get ingressclass nginx \
  >/dev/null 2>&1
then
    echo "ERROR: nginx IngressClass not found."
    echo "Run:"
    echo "./scripts/31-install-ingress-nginx.sh"
    exit 1
fi

if ! kubectl get secret ai-platform-api-tls \
  -n ai-platform >/dev/null 2>&1
then
    echo "ERROR: TLS secret not found."
    echo "Run:"
    echo "Wait for cert-manager Certificate/ai-platform-api-tls to become Ready."
    exit 1
fi

echo
echo "Validating manifests..."

kubectl kustomize "${INGRESS_DIR}" \
  >/tmp/phase2n-rendered.yaml

kubectl apply \
  -k "${INGRESS_DIR}"

echo
echo "Waiting briefly for NGINX configuration..."

sleep 5

echo
echo "Ingress:"

kubectl get ingress \
  -n ai-platform \
  -o wide

echo
echo "Ingress details:"

kubectl describe ingress \
  ai-platform-api \
  -n ai-platform

echo
echo "NetworkPolicy:"

kubectl get networkpolicy \
  allow-ingress-nginx-to-ai-platform-api \
  -n ai-platform

echo
echo "=========================================="
echo " PHASE 2N INGRESS DEPLOYED"
echo "=========================================="
