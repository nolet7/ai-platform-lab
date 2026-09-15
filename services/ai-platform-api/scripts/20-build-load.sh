#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.." &&
  pwd
)"

KIND_CLUSTER="ai-platform"
IMAGE="ai-platform-api:phase-2m"

echo
echo "=========================================="
echo " Phase 2M - Build FastAPI Container"
echo "=========================================="
echo "Cluster: ${KIND_CLUSTER}"
echo "Image:   ${IMAGE}"
echo

if ! kind get clusters | grep -qx "${KIND_CLUSTER}"; then
    echo "ERROR: Kind cluster '${KIND_CLUSTER}' not found."
    exit 1
fi

echo "Building image..."

docker build \
  -t "${IMAGE}" \
  "${PROJECT_DIR}"

echo
echo "Loading image into Kind..."

kind load docker-image \
  "${IMAGE}" \
  --name "${KIND_CLUSTER}"

echo
echo "Verifying image inside Kind nodes..."

for NODE in $(kind get nodes --name "${KIND_CLUSTER}"); do
    echo
    echo "Node: ${NODE}"

    docker exec "${NODE}" \
      crictl images |
      grep ai-platform-api || true
done

echo
echo "IMAGE BUILD + KIND LOAD: COMPLETE"
