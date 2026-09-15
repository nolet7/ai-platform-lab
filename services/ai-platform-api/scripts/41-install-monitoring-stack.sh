#!/usr/bin/env bash
set -euo pipefail

VALUES_FILE="$HOME/ai-platform-lab/observability/kube-prometheus-stack/values.yaml"

RELEASE="kube-prometheus-stack"
NAMESPACE="observability"
CHART_VERSION="90.0.0"

echo
echo "=========================================="
echo " Installing kube-prometheus-stack"
echo "=========================================="
echo "Chart version: ${CHART_VERSION}"

kubectl create namespace \
  "${NAMESPACE}" \
  --dry-run=client \
  -o yaml |
kubectl apply -f -

if ! kubectl get secret \
  grafana-admin \
  -n "${NAMESPACE}" \
  >/dev/null 2>&1
then

    GRAFANA_PASSWORD=$(
      openssl rand \
        -base64 32 |
      tr -d '\n'
    )

    kubectl create secret generic \
      grafana-admin \
      -n "${NAMESPACE}" \
      --from-literal=admin-user=admin \
      --from-literal=admin-password="${GRAFANA_PASSWORD}"

    unset GRAFANA_PASSWORD

    echo "Created Grafana admin Secret."
else
    echo "Grafana admin Secret already exists."
fi

helm upgrade \
  --install \
  "${RELEASE}" \
  oci://ghcr.io/prometheus-community/charts/kube-prometheus-stack \
  --version "${CHART_VERSION}" \
  --namespace "${NAMESPACE}" \
  --values "${VALUES_FILE}" \
  --wait \
  --timeout 10m

echo
echo "Monitoring pods:"

kubectl get pods \
  -n "${NAMESPACE}" \
  -o wide

echo
echo "Services:"

kubectl get svc \
  -n "${NAMESPACE}"

echo
echo "Grafana username: admin"
echo
echo "Retrieve Grafana password with:"
echo
echo "kubectl get secret grafana-admin -n observability -o jsonpath='{.data.admin-password}' | base64 -d; echo"

echo
echo "=========================================="
echo " MONITORING STACK READY"
echo "=========================================="
