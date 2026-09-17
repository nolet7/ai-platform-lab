#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
if [[ "$(kubectl config current-context)" != kind-ai-platform ]]; then
  echo "ERROR: expected Kubernetes context kind-ai-platform" >&2
  exit 1
fi
image=ai-platform-tax-classifier-mlserver:1.7.1-mlflow3.16.0-r3
archive="$(mktemp /tmp/tax-classifier-mlserver.XXXXXX.tar)"
trap 'rm -f "$archive"' EXIT
docker build -t "$image" services/tax-document-classifier/serving
docker image save --platform linux/amd64 --output "$archive" "$image"
kind load image-archive "$archive" --name ai-platform \
  --nodes ai-platform-worker,ai-platform-worker2
