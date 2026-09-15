#!/usr/bin/env bash
set -euo pipefail

VERSION="controller-v1.15.1"

MANIFEST_URL="https://raw.githubusercontent.com/kubernetes/ingress-nginx/${VERSION}/deploy/static/provider/kind/deploy.yaml"

echo
echo "=========================================="
echo " Installing ingress-nginx"
echo "=========================================="
echo "Version: ${VERSION}"
echo

if kubectl get deployment ingress-nginx-controller \
  -n ingress-nginx >/dev/null 2>&1
then
    echo "ingress-nginx controller already exists."
else

    echo "Installing official ingress-nginx Kind manifest..."

    kubectl apply -f "${MANIFEST_URL}"

fi

echo
echo "Waiting for admission jobs..."

kubectl wait \
  --namespace ingress-nginx \
  --for=condition=complete \
  job/ingress-nginx-admission-create \
  --timeout=180s \
  2>/dev/null || true

kubectl wait \
  --namespace ingress-nginx \
  --for=condition=complete \
  job/ingress-nginx-admission-patch \
  --timeout=180s \
  2>/dev/null || true

echo
echo "Waiting for controller..."

kubectl wait \
  --namespace ingress-nginx \
  --for=condition=Ready \
  pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=240s

echo
echo "Controller pods:"

kubectl get pods \
  -n ingress-nginx \
  -o wide

echo
echo "IngressClass:"

kubectl get ingressclass nginx

echo
echo "=========================================="
echo " ingress-nginx READY"
echo "=========================================="
