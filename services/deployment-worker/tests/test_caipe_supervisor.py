import json
from unittest.mock import Mock, patch

import pytest

from app.supervisor import AgentObservationError, observe_argo, observe_crossplane


REQUEST = "bac9633d-8021-42cb-93cb-ea8d5847aeb3"
SHA = "a" * 40
APPLICATION = "tax-document-classifier-tax-ml-team-staging-serving"


def make_response(agent, result, request_id=REQUEST):
    response = Mock()
    response.json.return_value = {
        "jsonrpc": "2.0", "id": REQUEST,
        "result": {"task": {
            "id": "task-1", "status": {"state": "TASK_STATE_COMPLETED"},
            "artifacts": [{"name": "observation", "parts": [{"text": json.dumps({
                "request_id": request_id, "correlation_id": REQUEST,
                "agent": agent, "status": "completed", "result": result,
            })}]}],
        }},
    }
    return response


def test_argo_observation_routes_with_a2a_envelope(monkeypatch):
    monkeypatch.setenv("CAIPE_INTERNAL_TOKEN", "test-only-token")
    client = Mock()
    client.post.return_value = make_response("argo", {
        "application": APPLICATION, "expected_revision": SHA,
        "sync_status": "Synced", "health_status": "Healthy",
    })
    with patch("app.supervisor.httpx.Client") as factory:
        factory.return_value.__enter__.return_value = client
        result = observe_argo(APPLICATION, SHA, REQUEST)
    assert result["health_status"] == "Healthy"
    assert result["correlation_id"] == REQUEST
    args, kwargs = client.post.call_args
    assert args[0].endswith("caipe-argo-agent.ai-platform.svc.cluster.local:8000/rpc")
    assert kwargs["json"]["method"] == "SendMessage"
    assert kwargs["headers"]["A2A-Version"] == "1.0"
    assert kwargs["headers"]["Authorization"] == "Bearer test-only-token"


def test_rejects_wrong_crossplane_identity(monkeypatch):
    monkeypatch.setenv("CAIPE_INTERNAL_TOKEN", "test-only-token")
    client = Mock()
    client.post.return_value = make_response("crossplane", {
        "application": APPLICATION, "workspace": "another-workspace",
        "namespace": "ml-platform", "request_id": REQUEST,
    })
    with patch("app.supervisor.httpx.Client") as factory:
        factory.return_value.__enter__.return_value = client
        with pytest.raises(AgentObservationError):
            observe_crossplane(APPLICATION, "expected-workspace", "ml-platform", REQUEST)


def test_requires_internal_credential(monkeypatch):
    monkeypatch.delenv("CAIPE_INTERNAL_TOKEN", raising=False)
    with pytest.raises(AgentObservationError):
        observe_argo(APPLICATION, SHA, REQUEST)
