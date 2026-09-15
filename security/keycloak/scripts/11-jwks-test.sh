#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/00-env.sh"

echo "Testing JWKS:"
echo "${KC_JWKS_ENDPOINT}"
echo

curl -fsS "${KC_JWKS_ENDPOINT}" |
python3 -c '
import sys
import json

data=json.load(sys.stdin)

keys=data.get("keys", [])

print("JWKS keys:", len(keys))

found_rsa=False

for key in keys:
    print(
        "kid =", key.get("kid"),
        "| kty =", key.get("kty"),
        "| alg =", key.get("alg"),
        "| use =", key.get("use")
    )

    if (
        key.get("kty") == "RSA"
        and key.get("alg") == "RS256"
        and key.get("use") == "sig"
    ):
        found_rsa=True

if not found_rsa:
    raise SystemExit("FAIL: RS256 signing key not found")

print()
print("PASS: Keycloak RS256 JWKS signing key available")
'
