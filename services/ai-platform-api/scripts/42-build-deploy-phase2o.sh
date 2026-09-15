#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.." &&
  pwd
)"

IMAGE="ai-platform-api:phase-2o-v2"
CLUSTER="ai-platform"

echo
echo "=========================================="
echo " Phase 2O - Build Instrumented API"
echo "=========================================="

docker build \
  -t "${IMAGE}" \
  "${PROJECT_DIR}"

echo
echo "Loading image into Kind..."

kind load docker-image \
  "${IMAGE}" \
  --name "${CLUSTER}"

echo
echo "Deploying Phase 2O overlay..."

kubectl apply \
  -k "${PROJECT_DIR}/k8s/overlays/phase-2o"

echo
echo "Waiting for rollout..."

kubectl rollout status \
  deployment/ai-platform-api \
  -n ai-platform \
  --timeout=240s

echo
echo "Pods:"

kubectl get pods \
  -n ai-platform \
  -l app.kubernetes.io/name=ai-platform-api \
  -o wide

echo
echo "Service ports:"

kubectl get svc \
  ai-platform-api \
  -n ai-platform

echo
echo "=========================================="
echo " PHASE 2O API DEPLOYED"
echo "=========================================="
