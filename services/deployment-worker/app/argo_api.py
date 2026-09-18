"""Narrow Argo CD REST client for deployment reconciliation."""

import re

import httpx

APPLICATION_NAME = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z")


class ArgoAPIError(RuntimeError):
    pass


def inspect_application(
    application: str,
    *,
    base_url: str,
    token: str,
    expected_revision: str,
    ca_bundle: str,
) -> dict:
    """Request a hard refresh and return the observed Argo state."""
    if not APPLICATION_NAME.fullmatch(application):
        raise ValueError("Invalid Argo application name")
    if not re.fullmatch(r"[a-f0-9]{40}", expected_revision):
        raise ValueError("Expected revision must be a Git commit SHA")
    if not token:
        raise ArgoAPIError("Argo API token is not configured")
    if base_url != "https://argocd-server.argocd.svc.cluster.local:443":
        raise ArgoAPIError("Argo API endpoint is not the in-cluster service")
    try:
        with httpx.Client(timeout=10.0, verify=ca_bundle) as client:
            response = client.get(
                f"{base_url.rstrip('/')}/api/v1/applications/{application}",
                params={"refresh": "hard"},
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            app = response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise ArgoAPIError("Argo application inspection failed") from error
    status = app.get("status", {})
    sync = status.get("sync", {})
    health = status.get("health", {})
    revision = sync.get("revision")
    history_revisions = {
        item.get("revision") for item in status.get("history", [])
        if isinstance(item, dict)
    }
    revision_current = revision == expected_revision
    return {
        "application": application,
        "observed_revision": revision,
        "expected_revision": expected_revision,
        "revision_observed": revision_current,
        "revision_applied": revision_current or expected_revision in history_revisions,
        "sync_status": sync.get("status", "Unknown"),
        "health_status": health.get("status", "Unknown"),
        "application_url": f"https://argocd.ai-platform.local/applications/{application}",
    }
