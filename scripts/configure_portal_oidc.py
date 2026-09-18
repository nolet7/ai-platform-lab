"""Idempotently configure the local Keycloak portal client.

Run with a temporary local port-forward on 19084. Reads the existing
Keycloak bootstrap Secret; never prints passwords or token material.
"""
import base64
import json
import os
import subprocess
import urllib.parse
import urllib.request

BASE = os.getenv("KEYCLOAK_ADMIN_URL", "http://127.0.0.1:19084")
REALM = "ai-platform"
REDIRECT = "https://api.ai-platform.local/portal/"
ORIGIN = "https://api.ai-platform.local"

def request(path, token=None, payload=None, method=None):
    headers = {}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req) as response:
        body = response.read()
        return json.loads(body) if body else None

secret = request_secret = json.loads(subprocess.check_output([
    "kubectl", "-n", "security", "get", "secret", "keycloak-bootstrap-admin", "-o", "json"
]))
data = secret["data"]
username = base64.b64decode(data["KC_BOOTSTRAP_ADMIN_USERNAME"]).decode()
password = base64.b64decode(data["KC_BOOTSTRAP_ADMIN_PASSWORD"]).decode()
form = urllib.parse.urlencode({
    "client_id": "admin-cli", "grant_type": "password",
    "username": username, "password": password,
}).encode()
req = urllib.request.Request(
    BASE + "/realms/master/protocol/openid-connect/token",
    data=form, headers={"Content-Type": "application/x-www-form-urlencoded"},
)
with urllib.request.urlopen(req) as response:
    token = json.load(response)["access_token"]

clients = request(f"/admin/realms/{REALM}/clients", token)
portal = next(c for c in clients if c["clientId"] == "ai-platform-portal")
cli = next(c for c in clients if c["clientId"] == "platform-cli")
portal.update({
    "publicClient": True,
    "standardFlowEnabled": True,
    "directAccessGrantsEnabled": False,
    "redirectUris": [REDIRECT],
    "webOrigins": [ORIGIN],
    "attributes": {
        **portal.get("attributes", {}),
        "pkce.code.challenge.method": "S256",
    },
})
request(
    f"/admin/realms/{REALM}/clients/{portal['id']}",
    token, portal, method="PUT",
)
existing = request(
    f"/admin/realms/{REALM}/clients/{portal['id']}/protocol-mappers/models", token
)
names = {mapper["name"] for mapper in existing}
source = request(
    f"/admin/realms/{REALM}/clients/{cli['id']}/protocol-mappers/models", token
)
for mapper in source:
    if mapper["name"] not in ("ai-platform-api-audience", "tenant-id"):
        continue
    if mapper["name"] in names:
        continue
    definition = {key: value for key, value in mapper.items() if key != "id"}
    request(
        f"/admin/realms/{REALM}/clients/{portal['id']}/protocol-mappers/models",
        token, definition, method="POST",
    )
print("Portal client configured: public PKCE, exact redirect, API audience, tenant claim")
