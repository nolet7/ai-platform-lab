#!/usr/bin/env bash
set -euo pipefail

echo "Deleting Phase 2M ai-platform namespace..."

kubectl delete namespace ai-platform \
  --ignore-not-found=true

echo
echo "Phase 2M Kubernetes resources deleted."
echo
echo "NOT deleted:"
echo "  security namespace / Keycloak"
echo "  argocd namespace / Argo CD"
echo "  Kind cluster"
