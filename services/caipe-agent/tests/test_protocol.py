import os

os.environ.setdefault("CAIPE_AGENT_KIND", "argo")
os.environ.setdefault("CAIPE_INTERNAL_TOKEN", "test-only-token")

from starlette.testclient import TestClient
import pytest

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as session:
        yield session


def test_card_and_health_are_public(client):
    assert client.get("/health").json() == {"status": "ok", "agent": "argo"}
    card = client.get("/.well-known/agent-card.json")
    assert card.status_code == 200
    assert card.json()["supportedInterfaces"][0]["protocolBinding"] == "JSONRPC"


def test_a2a_and_mcp_require_internal_token(client):
    assert client.post("/rpc", json={}).status_code == 401
    assert client.post("/mcp/", json={}).status_code == 401
    authorized = client.post(
        "/rpc", headers={"Authorization": "Bearer test-only-token", "A2A-Version": "1.0"},
        json={"jsonrpc": "2.0", "id": "bad", "method": "NoSuchMethod"},
    )
    assert authorized.status_code == 200
    assert authorized.json()["error"]["code"] != 0
