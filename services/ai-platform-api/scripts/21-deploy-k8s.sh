#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.." &&
  pwd
)"

K8S_DIR="${PROJECT_DIR}/k8s"

echo
echo "=========================================="
echo " Phase 2M - Kubernetes Deployment"
echo "=========================================="

echo
echo "Checking Keycloak..."

kubectl get pods -n security

echo
echo "Discovering Keycloak Service..."

read KC_SERVICE KC_SERVICE_PORT < <(
  kubectl get svc -n security -o json |
  python3 -c '
import json
import sys

data = json.load(sys.stdin)

services = [
    svc
    for svc in data.get("items", [])
    if "keycloak" in svc["metadata"]["name"].lower()
]

if not services:
    raise SystemExit(
        "ERROR: No Keycloak-named Service found in namespace security"
    )

svc = services[0]

ports = svc.get("spec", {}).get("ports", [])

if not ports:
    raise SystemExit("ERROR: Keycloak Service has no ports")

selected = None

for port in ports:
    if (
        port.get("port") == 8080
        or port.get("targetPort") == 8080
    ):
        selected = port
        break

if selected is None:
    selected = ports[0]

print(
    svc["metadata"]["name"],
    selected["port"]
)
'
)

echo "Keycloak Service: ${KC_SERVICE}"
echo "Keycloak port:    ${KC_SERVICE_PORT}"

KEYCLOAK_JWKS_URL="http://${KC_SERVICE}.security.svc.cluster.local:${KC_SERVICE_PORT}/realms/ai-platform/protocol/openid-connect/certs"

echo
echo "Internal JWKS URL:"
echo "${KEYCLOAK_JWKS_URL}"

echo
echo "Applying Kubernetes resources..."

kubectl apply -k "${K8S_DIR}"

echo
echo "Updating runtime ConfigMap..."

kubectl create configmap ai-platform-api-config \
  -n ai-platform \
  --from-literal=APP_NAME="AI Platform API" \
  --from-literal=APP_ENV="kubernetes" \
  --from-literal=APP_HOST="0.0.0.0" \
  --from-literal=APP_PORT="8001" \
  --from-literal=KEYCLOAK_REALM="ai-platform" \
  --from-literal=KEYCLOAK_ISSUER="http://127.0.0.1:18080/realms/ai-platform" \
  --from-literal=KEYCLOAK_JWKS_URL="${KEYCLOAK_JWKS_URL}" \
  --from-literal=KEYCLOAK_AUDIENCE="ai-platform-api" \
  --from-literal=KEYCLOAK_ALGORITHM="RS256" \
  --dry-run=client \
  -o yaml |
kubectl apply -f -

echo
echo "Restarting deployment to consume ConfigMap..."

kubectl rollout restart \
  deployment/ai-platform-api \
  -n ai-platform

echo
echo "Waiting for rollout..."

kubectl rollout status \
  deployment/ai-platform-api \
  -n ai-platform \
  --timeout=180s

echo
echo "Deployment status:"

kubectl get pods \
  -n ai-platform \
  -o wide

echo
kubectl get svc \
  -n ai-platform

echo
echo "PHASE 2M KUBERNETES DEPLOYMENT: COMPLETE"
