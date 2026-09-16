#!/usr/bin/env bash

echo
echo "Telemetry:"
kubectl get pods \
  -n observability \
  -o wide

echo
echo "API:"
kubectl get pods \
  -n ai-platform \
  -l app.kubernetes.io/name=ai-platform-api \
  -o wide

echo
echo "Ingress OTel configuration:"

kubectl get configmap \
  ingress-nginx-controller \
  -n ingress-nginx \
  -o jsonpath='
enabled={.data.enable-opentelemetry}{"\n"}
collector={.data.otlp-collector-host}{"\n"}
service={.data.otel-service-name}{"\n"}
'

echo
echo "Ports:"
echo "13000 -> Grafana"
echo "19090 -> Prometheus"
echo "13100 -> Loki"
echo "13200 -> Tempo"
