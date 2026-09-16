#!/usr/bin/env bash
set -euo pipefail

DIR="$HOME/ai-platform-lab/observability/phase-2p"

echo
echo "Deploying Loki, Tempo, Collector and Alloy..."

kubectl apply \
  -k "${DIR}"

echo
echo "Waiting for Loki..."

kubectl rollout status \
  deployment/loki \
  -n observability \
  --timeout=240s

echo
echo "Waiting for Tempo..."

kubectl rollout status \
  deployment/tempo \
  -n observability \
  --timeout=240s

echo
echo "Waiting for OTel Collector..."

kubectl rollout status \
  deployment/otel-collector \
  -n observability \
  --timeout=240s

echo
echo "Waiting for Alloy..."

kubectl rollout status \
  deployment/alloy \
  -n observability \
  --timeout=240s

echo
kubectl get pods \
  -n observability \
  -o wide

echo
echo "PHASE 2P TELEMETRY BACKENDS READY"
