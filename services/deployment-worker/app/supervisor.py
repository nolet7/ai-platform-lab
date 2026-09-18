"""CAIPE supervisor routes approved requests to purpose-specific A2A agents."""

import json
import os
from uuid import UUID, uuid4

import httpx


AGENTS = {
    "argo": "http://caipe-argo-agent.ai-platform.svc.cluster.local:8000/rpc",
    "crossplane": "http://caipe-crossplane-agent.ai-platform.svc.cluster.local:8000/rpc",
}


class AgentObservationError(RuntimeError):
    pass


def _send(agent: str, request_id: str, arguments: dict) -> dict:
    """Send an idempotent read task and validate the A2A response envelope."""
    request_id = str(UUID(request_id))
    correlation_id = request_id
    token = os.getenv("CAIPE_INTERNAL_TOKEN", "")
    if not token:
        raise AgentObservationError("CAIPE internal authorization is not configured")
    payload = {"request_id": request_id, "correlation_id": correlation_id, **arguments}
    envelope = {
        "jsonrpc": "2.0",
        "id": correlation_id,
        "method": "SendMessage",
        "params": {"message": {
            "messageId": str(uuid4()),
            "role": "ROLE_USER",
            "parts": [{"text": json.dumps(payload)}],
        }},
    }
    try:
        with httpx.Client(timeout=25.0) as client:
            response = client.post(
                AGENTS[agent], json=envelope,
                headers={"Authorization": f"Bearer {token}", "A2A-Version": "1.0"},
            )
            response.raise_for_status()
            body = response.json()
        if body.get("jsonrpc") != "2.0" or body.get("id") != correlation_id:
            raise ValueError("Invalid A2A envelope")
        task = body["result"]["task"]
        if task["status"]["state"] != "TASK_STATE_COMPLETED":
            raise ValueError("Agent task did not complete")
        artifacts = task["artifacts"]
        if len(artifacts) != 1 or artifacts[0]["name"] != "observation":
            raise ValueError("Agent observation artifact missing")
        artifact = json.loads(artifacts[0]["parts"][0]["text"])
        if (
            artifact.get("request_id") != request_id
            or artifact.get("correlation_id") != correlation_id
            or artifact.get("agent") != agent
            or artifact.get("status") != "completed"
            or not isinstance(artifact.get("result"), dict)
        ):
            raise ValueError("Agent artifact identity mismatch")
        result = artifact["result"]
        if result.get("application") != arguments["application"]:
            raise ValueError("Agent Application identity mismatch")
        return {**result, "correlation_id": correlation_id}
    except (httpx.HTTPError, ValueError, KeyError, TypeError, IndexError) as error:
        raise AgentObservationError(f"{agent} observation unavailable") from error


def observe_argo(application: str, expected_revision: str, request_id: str) -> dict:
    result = _send("argo", request_id, {
        "application": application, "expected_revision": expected_revision,
    })
    if result.get("expected_revision") != expected_revision:
        raise AgentObservationError("Argo agent revision mismatch")
    return result


def observe_crossplane(application: str, workspace: str, namespace: str, request_id: str) -> dict:
    result = _send("crossplane", request_id, {
        "application": application, "workspace": workspace,
        "namespace": namespace,
    })
    if (
        result.get("workspace") != workspace
        or result.get("namespace") != namespace
        or result.get("request_id") != request_id
    ):
        raise AgentObservationError("Crossplane agent identity mismatch")
    return result
