#!/usr/bin/env bash
set -euo pipefail

echo "API TLS is managed by cert-manager via gitops/platform-edge/api.yaml." >&2
echo "Wait for Certificate/ai-platform-api-tls in namespace ai-platform." >&2
exit 1
