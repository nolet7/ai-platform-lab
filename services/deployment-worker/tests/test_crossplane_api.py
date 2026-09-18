import json
from unittest.mock import Mock, patch

import pytest

from app.argo_api import ArgoAPIError, inspect_workspace

BASE = "https://argocd-server.argocd.svc.cluster.local:443"
REQUEST_ID = "bac9633d-8021-42cb-93cb-ea8d5847aeb3"
APP = "tax-document-classifier-tax-ml-team-staging-serving"
WORKSPACE = "tax-document-classifier-tax-ml-team-staging"


def test_reads_verified_workspace_status():
    response = Mock()
    response.json.return_value = {"manifest": json.dumps({
        "kind": "ModelWorkspace",
        "metadata": {
            "name": WORKSPACE,
            "namespace": "ml-platform",
            "annotations": {"ai-platform.io/request-id": REQUEST_ID},
        },
        "status": {
            "conditions": [{"type": "Ready", "status": "True"}, {"type": "Synced", "status": "True"}],
            "pvcName": WORKSPACE + "-data",
            "storagePhase": "Bound",
            "initJobName": WORKSPACE + "-init",
        },
    })}
    client = Mock()
    client.get.return_value = response
    with patch("app.argo_api.httpx.Client") as factory:
        factory.return_value.__enter__.return_value = client
        result = inspect_workspace(APP, WORKSPACE, "ml-platform", REQUEST_ID,
                                   base_url=BASE, token="scoped", ca_bundle="/tmp/ca.crt")
    assert result["ready"] is True
    assert result["storage_phase"] == "Bound"
    assert client.get.call_args.kwargs["params"]["kind"] == "ModelWorkspace"


def test_rejects_workspace_from_other_request():
    response = Mock()
    response.json.return_value = {"manifest": json.dumps({
        "kind": "ModelWorkspace",
        "metadata": {"name": WORKSPACE, "namespace": "ml-platform", "annotations": {
            "ai-platform.io/request-id": "00000000-0000-0000-0000-000000000000"}},
    })}
    client = Mock()
    client.get.return_value = response
    with patch("app.argo_api.httpx.Client") as factory:
        factory.return_value.__enter__.return_value = client
        with pytest.raises(ArgoAPIError):
            inspect_workspace(APP, WORKSPACE, "ml-platform", REQUEST_ID,
                              base_url=BASE, token="scoped", ca_bundle="/tmp/ca.crt")


@pytest.mark.parametrize("workspace,namespace", [("../escape", "ml-platform"), (WORKSPACE, "security")])
def test_rejects_unsafe_resource_target(workspace, namespace):
    with pytest.raises(ValueError):
        inspect_workspace(APP, workspace, namespace, REQUEST_ID,
                          base_url=BASE, token="scoped", ca_bundle="/tmp/ca.crt")
