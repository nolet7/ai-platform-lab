"""Create local demo requester/approver without changing existing users.

Requires Keycloak port-forward on localhost:19084. New passwords are written
only to /tmp/ai-platform-demo-credentials.txt for transfer outside Git.
"""
import base64
import json
import os
from pathlib import Path
import secrets
import subprocess
import urllib.parse
import urllib.request

BASE = os.getenv("KEYCLOAK_ADMIN_URL", "http://127.0.0.1:19084")
REALM = "ai-platform"

def call(path, token=None, payload=None, method=None):
    headers = {}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req) as response:
        content = response.read()
        return json.loads(content) if content else None

secret = json.loads(subprocess.check_output([
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

roles = {role["name"]: role for role in call(f"/admin/realms/{REALM}/roles", token)}
users = {user["username"]: user for user in call(f"/admin/realms/{REALM}/users?max=100", token)}
credentials = []
for name, role_names in (
    ("demo-requester", ("data-scientist", "viewer")),
    ("demo-approver", ("approver", "viewer")),
):
    user = users.get(name)
    if user is None:
        call(f"/admin/realms/{REALM}/users", token, {
            "username": name,
            "enabled": True,
            "attributes": {"tenant_id": ["tax-ml-team"]},
        }, method="POST")
        user = next(
            u for u in call(f"/admin/realms/{REALM}/users?username={name}&exact=true", token)
            if u["username"] == name
        )
        new_password = secrets.token_urlsafe(20)
        call(
            f"/admin/realms/{REALM}/users/{user['id']}/reset-password",
            token,
            {"type": "password", "value": new_password, "temporary": False},
            method="PUT",
        )
        credentials.append(f"{name}: {new_password}")
    user.update({
        "firstName": "Demo",
        "lastName": "Requester" if name == "demo-requester" else "Approver",
        "email": name + "@ai-platform.local",
        "emailVerified": True,
        "requiredActions": [],
        "attributes": {"tenant_id": ["tax-ml-team"]},
    })
    call(f"/admin/realms/{REALM}/users/{user['id']}", token, user, method="PUT")
    current = {
        role["name"] for role in call(
            f"/admin/realms/{REALM}/users/{user['id']}/role-mappings/realm", token
        )
    }
    missing = [roles[role] for role in role_names if role not in current]
    if missing:
        call(
            f"/admin/realms/{REALM}/users/{user['id']}/role-mappings/realm",
            token, missing, method="POST",
        )
    print(name, "ready; roles", ",".join(role_names))
if credentials:
    path = Path("/tmp/ai-platform-demo-credentials.txt")
    path.write_text("AI Platform local demo accounts\n" + "\n".join(credentials) + "\n")
    path.chmod(0o600)
    print("New credentials saved to temporary local file for Windows transfer")
