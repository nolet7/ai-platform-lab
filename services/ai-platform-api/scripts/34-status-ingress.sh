#!/usr/bin/env bash
set -euo pipefail

echo
echo "=========================================="
echo " Phase 2N - Ingress Status"
echo "=========================================="

INGRESS_POD=$(
  kubectl get pods \
    -n ingress-nginx \
    -l app.kubernetes.io/component=controller \
    -o jsonpath='{.items[0].metadata.name}'
)

INGRESS_NODE=$(
  kubectl get pod \
    "${INGRESS_POD}" \
    -n ingress-nginx \
    -o jsonpath='{.spec.nodeName}'
)

INGRESS_IP=$(
  docker inspect \
    -f '{{with index .NetworkSettings.Networks "kind"}}{{.IPAddress}}{{end}}' \
    "${INGRESS_NODE}"
)

echo "Ingress pod:  ${INGRESS_POD}"
echo "Ingress node: ${INGRESS_NODE}"
echo "Kind node IP: ${INGRESS_IP}"

echo
echo "Routes:"
echo "HTTP:"
echo "  http://api.ai-platform.local"
echo
echo "HTTPS:"
echo "  https://api.ai-platform.local"
echo

echo "Curl without /etc/hosts:"
echo
echo "curl --resolve api.ai-platform.local:443:${INGRESS_IP} \\"
echo "  -k https://api.ai-platform.local/health/live"

echo
echo "Ingress:"
kubectl get ingress \
  -n ai-platform \
  -o wide

echo
echo "Controller:"
kubectl get pods \
  -n ingress-nginx \
  -o wide

echo
echo "Backend Service:"
kubectl get endpoints \
  ai-platform-api \
  -n ai-platform
