#!/usr/bin/env bash
set -euo pipefail

HOST="api.ai-platform.local"

CERT="/tmp/ai-platform-api.crt"
KEY="/tmp/ai-platform-api.key"
CONFIG="/tmp/ai-platform-api-openssl.cnf"

echo
echo "=========================================="
echo " Phase 2N - TLS Certificate"
echo "=========================================="

cat > "${CONFIG}" <<CONF
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = req_ext

[dn]
CN = ${HOST}
O = AI Platform Lab

[req_ext]
subjectAltName = @alt_names

[alt_names]
DNS.1 = ${HOST}
CONF

echo "Generating self-signed certificate..."

openssl req \
  -x509 \
  -nodes \
  -days 365 \
  -newkey rsa:2048 \
  -keyout "${KEY}" \
  -out "${CERT}" \
  -config "${CONFIG}" \
  -extensions req_ext

echo
echo "Creating Kubernetes TLS Secret..."

kubectl create secret tls \
  ai-platform-api-tls \
  -n ai-platform \
  --cert="${CERT}" \
  --key="${KEY}" \
  --dry-run=client \
  -o yaml |
kubectl apply -f -

echo
echo "TLS Secret:"

kubectl get secret \
  ai-platform-api-tls \
  -n ai-platform

echo
echo "Certificate subject/SAN:"

openssl x509 \
  -in "${CERT}" \
  -noout \
  -subject \
  -issuer \
  -dates \
  -ext subjectAltName

echo
echo "TLS certificate configuration complete."
