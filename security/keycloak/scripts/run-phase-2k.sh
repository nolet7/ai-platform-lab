#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo
echo "=============================================="
echo " AI PLATFORM - PHASE 2K"
echo " Keycloak OIDC + RBAC Configuration"
echo "=============================================="
echo

bash "${SCRIPT_DIR}/01-admin-login.sh"

echo
echo "========== REALM =========="
bash "${SCRIPT_DIR}/02-realm.sh"

echo
echo "========== RBAC =========="
bash "${SCRIPT_DIR}/03-rbac.sh"

echo
echo "========== OIDC CLIENT =========="
bash "${SCRIPT_DIR}/04-client.sh"

echo
echo "========== AUDIENCE =========="
bash "${SCRIPT_DIR}/05-audience.sh"

echo
echo "========== SERVICE ACCOUNT =========="
bash "${SCRIPT_DIR}/06-service-account.sh"

echo
echo "========== PORT FORWARD =========="
bash "${SCRIPT_DIR}/08-port-forward.sh"

echo
echo "========== CLIENT CREDENTIALS =========="
bash "${SCRIPT_DIR}/09-token-test.sh"

echo
echo "========== JWT VALIDATION =========="
bash "${SCRIPT_DIR}/10-validate-token.sh"

echo
echo "========== JWKS =========="
bash "${SCRIPT_DIR}/11-jwks-test.sh"

echo
echo "=============================================="
echo " PHASE 2K COMPLETE"
echo "=============================================="
echo
echo "Realm:       ai-platform"
echo "Client:      ai-platform-api"
echo "Identity:    service-account-ai-platform-api"
echo "Role:        inference-client"
echo "Algorithm:   RS256"
echo "Keycloak:    http://127.0.0.1:18080"
echo
echo "Port inventory:"
echo "  8080  -> Argo CD"
echo "  18080 -> Keycloak"
echo "=============================================="
