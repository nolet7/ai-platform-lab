from unittest.mock import Mock, patch

import pytest

from app.argo_api import ArgoAPIError, inspect_application


SHA = "a" * 40
BASE = "https://argocd-server.argocd.svc.cluster.local:443"


def test_inspects_exact_application_and_revision():
    response = Mock()
    response.json.return_value = {
        "status": {
            "sync": {"revision": SHA, "status": "Synced"},
            "health": {"status": "Healthy"},
        }
    }
    client = Mock()
    client.get.return_value = response
    with patch("app.argo_api.httpx.Client") as factory:
        factory.return_value.__enter__.return_value = client
        result = inspect_application(
            "tax-classifier-dev",
            base_url=BASE,
            token="test-token",
            expected_revision=SHA,
            ca_bundle="/tmp/ca.crt",
        )
    assert result["revision_observed"] is True
    assert result["health_status"] == "Healthy"
    client.get.assert_called_once()
    assert client.get.call_args.args[0].endswith(
        "/api/v1/applications/tax-classifier-dev"
    )
    assert client.get.call_args.kwargs["params"] == {"refresh": "hard"}


@pytest.mark.parametrize("name", ["../admin", "a/b", "A"])
def test_rejects_invalid_application(name):
    with pytest.raises(ValueError):
        inspect_application(
            name, base_url=BASE, token="test", expected_revision=SHA, ca_bundle="/tmp/ca.crt"
        )


def test_requires_scoped_token():
    with pytest.raises(ArgoAPIError):
        inspect_application(
            "tax-classifier-dev", base_url=BASE, token="", expected_revision=SHA, ca_bundle="/tmp/ca.crt"
        )



def test_history_proves_commit_applied_after_branch_advances():
    response = Mock()
    response.json.return_value = {
        "status": {
            "sync": {"revision": "b" * 40, "status": "Synced"},
            "health": {"status": "Healthy"},
            "history": [{"revision": SHA}],
        }
    }
    client = Mock()
    client.get.return_value = response
    with patch("app.argo_api.httpx.Client") as factory:
        factory.return_value.__enter__.return_value = client
        result = inspect_application(
            "tax-classifier-dev", base_url=BASE, token="test-token",
            expected_revision=SHA, ca_bundle="/tmp/ca.crt",
        )
    assert result["revision_applied"] is True
    assert result["revision_observed"] is False
    assert result["observed_revision"] == "b" * 40
