#!/usr/bin/env bash
set -euo pipefail

echo
echo "Deleting Phase 2N application ingress resources..."

kubectl delete \
  -k k8s/ingress \
  --ignore-not-found=true

echo
echo "Phase 2N application ingress deleted."
echo
echo "NOT deleted:"
echo "  ai-platform-api Deployment"
echo "  ai-platform-api Service"
echo "  Keycloak"
echo "  Argo CD"
echo "  Kind cluster"
echo "  ingress-nginx controller"
