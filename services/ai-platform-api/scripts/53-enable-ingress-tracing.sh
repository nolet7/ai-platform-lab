#!/usr/bin/env bash
set -euo pipefail

echo
echo "Enabling OpenTelemetry in ingress-nginx..."

kubectl patch configmap \
  ingress-nginx-controller \
  -n ingress-nginx \
  --type merge \
  -p '{
    "data": {
      "enable-opentelemetry": "true",
      "opentelemetry-trust-incoming-span": "true",
      "otlp-collector-host": "otel-collector.observability.svc.cluster.local",
      "otlp-collector-port": "4317",
      "otel-service-name": "ingress-nginx",
      "otel-sampler": "AlwaysOn",
      "otel-sampler-ratio": "1.0",
      "otel-sampler-parent-based": "true"
    }
  }'

kubectl annotate ingress \
  ai-platform-api \
  -n ai-platform \
  nginx.ingress.kubernetes.io/enable-opentelemetry="true" \
  nginx.ingress.kubernetes.io/opentelemetry-trust-incoming-span="true" \
  --overwrite

echo
echo "Restarting ingress controller..."

kubectl rollout restart \
  deployment/ingress-nginx-controller \
  -n ingress-nginx

kubectl rollout status \
  deployment/ingress-nginx-controller \
  -n ingress-nginx \
  --timeout=240s

echo
echo "Ingress OpenTelemetry enabled."
