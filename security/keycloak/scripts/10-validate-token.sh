#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/00-env.sh"

if [[ ! -f "${KC_TOKEN_FILE}" ]]; then
    echo "ERROR: Token file not found."
    echo "Run ./scripts/09-token-test.sh first."
    exit 1
fi

export ACCESS_TOKEN=$(
  python3 -c \
  "import json; print(json.load(open('${KC_TOKEN_FILE}'))['access_token'])"
)

echo "Access token loaded: ${#ACCESS_TOKEN} characters"
echo

python3 - <<'PY'
import os
import json
import base64
import sys

token = os.environ["ACCESS_TOKEN"]

header_b64, payload_b64, _ = token.split(".")

def decode(part):
    part += "=" * (-len(part) % 4)
    return json.loads(base64.urlsafe_b64decode(part))

header = decode(header_b64)
claims = decode(payload_b64)

safe_claims = {
    "alg": header.get("alg"),
    "kid": header.get("kid"),
    "iss": claims.get("iss"),
    "aud": claims.get("aud"),
    "azp": claims.get("azp"),
    "preferred_username": claims.get("preferred_username"),
    "realm_roles": claims.get("realm_access", {}).get("roles", [])
}

print("JWT claims:")
print(json.dumps(safe_claims, indent=2))
print()

aud = claims.get("aud", [])

if isinstance(aud, str):
    aud = [aud]

roles = claims.get("realm_access", {}).get("roles", [])

checks = [
    (
        "Algorithm is RS256",
        header.get("alg") == "RS256"
    ),
    (
        "Audience contains ai-platform-api",
        "ai-platform-api" in aud
    ),
    (
        "Authorized party is ai-platform-api",
        claims.get("azp") == "ai-platform-api"
    ),
    (
        "inference-client role exists",
        "inference-client" in roles
    ),
    (
        "Service-account identity",
        claims.get("preferred_username")
        == "service-account-ai-platform-api"
    )
]

for name, passed in checks:
    print(f"{'PASS' if passed else 'FAIL'}: {name}")

if not all(passed for _, passed in checks):
    sys.exit(1)

print()
print("PHASE 2K TOKEN CLAIMS: PASS")
PY
