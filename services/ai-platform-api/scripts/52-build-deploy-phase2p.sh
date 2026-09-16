#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.." &&
  pwd
)"

IMAGE="ai-platform-api:phase-2p-v2"
CLUSTER="ai-platform"

echo
echo "Building ${IMAGE}..."

docker build \
  --no-cache \
  -t "${IMAGE}" \
  "${PROJECT_DIR}"

echo
echo "Loading image into Kind..."

kind load docker-image \
  "${IMAGE}" \
  --name "${CLUSTER}"

echo
echo "Applying Phase 2P overlay..."

kubectl apply \
  -k "${PROJECT_DIR}/k8s/overlays/phase-2p"

echo
echo "Waiting for rollout..."

kubectl rollout status \
  deployment/ai-platform-api \
  -n ai-platform \
  --timeout=240s

kubectl get pods \
  -n ai-platform \
  -l app.kubernetes.io/name=ai-platform-api \
  -o wide

echo
echo "PHASE 2P API DEPLOYED"
