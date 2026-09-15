#!/usr/bin/env bash
set -euo pipefail

echo
echo "=========================================="
echo " Phase 2N - Precheck"
echo "=========================================="

echo
echo "Port inventory:"
echo "8080   -> Argo CD"
echo "18080  -> Keycloak"
echo "8001   -> Local Phase 2L FastAPI"
echo "18081  -> Phase 2M Kubernetes API forward"
echo
echo "Phase 2N uses Kind node IP ports 80/443."
echo "No additional WSL local port is allocated."

echo
echo "1. Checking cluster..."

kubectl cluster-info >/dev/null

echo "PASS: Kubernetes reachable"

echo
echo "2. Checking nodes..."

kubectl get nodes

echo
echo "3. Checking ai-platform namespace..."

kubectl get namespace ai-platform >/dev/null

echo "PASS: ai-platform namespace exists"

echo
echo "4. Checking deployment..."

kubectl get deployment ai-platform-api \
  -n ai-platform >/dev/null

echo "PASS: ai-platform-api deployment exists"

echo
echo "5. Checking Service..."

kubectl get service ai-platform-api \
  -n ai-platform >/dev/null

echo "PASS: ai-platform-api Service exists"

echo
echo "6. Checking pods..."

NOT_READY=$(
  kubectl get pods \
    -n ai-platform \
    -l app.kubernetes.io/name=ai-platform-api \
    --no-headers |
  grep -v '1/1.*Running' || true
)

if [[ -n "${NOT_READY}" ]]; then
    echo "ERROR: Some API pods are not ready:"
    echo "${NOT_READY}"
    exit 1
fi

echo "PASS: API pods ready"

echo
echo "7. Existing ingress-nginx?"

if kubectl get namespace ingress-nginx \
  >/dev/null 2>&1
then
    echo "INFO: ingress-nginx namespace already exists."
else
    echo "INFO: ingress-nginx not installed yet."
fi

echo
echo "=========================================="
echo " PHASE 2N PRECHECK: PASS"
echo "=========================================="
