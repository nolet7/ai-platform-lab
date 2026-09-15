#!/usr/bin/env bash

echo
echo "=========================================="
echo " PHASE 2O STATUS"
echo "=========================================="

echo
echo "Monitoring pods:"
kubectl get pods \
  -n observability \
  -o wide

echo
echo "AI Platform pods:"
kubectl get pods \
  -n ai-platform \
  -o wide

echo
echo "ServiceMonitor:"
kubectl get servicemonitors \
  -n ai-platform

echo
echo "PrometheusRule:"
kubectl get prometheusrules \
  -n ai-platform

echo
echo "NetworkPolicies:"
kubectl get networkpolicy \
  -n ai-platform

echo
echo "Dashboard:"
kubectl get configmap \
  ai-platform-api-dashboard \
  -n ai-platform

echo
echo "Recent API logs:"
kubectl logs \
  -n ai-platform \
  -l app.kubernetes.io/name=ai-platform-api \
  --tail=20

echo
echo "Ports:"
echo "8080   -> Argo CD"
echo "18080  -> Keycloak"
echo "13000  -> Grafana"
echo "19090  -> Prometheus"
echo "9091   -> Internal API metrics"
