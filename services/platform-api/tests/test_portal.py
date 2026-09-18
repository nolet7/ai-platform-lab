import os
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://x:x@localhost/test")

from fastapi.testclient import TestClient
from sqlalchemy.dialects import postgresql

from app.database import get_db
from app.main import app
from app.repository import list_deployments
from app.security import Principal, get_current_principal


def test_portal_assets_and_csp():
    client = TestClient(app)
    response = client.get("/portal/")
    assert response.status_code == 200
    assert "code_challenge_method" in client.get("/portal/assets/app.js").text
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


def test_list_query_scopes_to_tenant():
    db = Mock()
    db.scalars.return_value = []
    principal = Principal(subject="u", username="alice", tenant_id="tax-ml-team", roles=["viewer"])
    list_deployments(db, principal, 10)
    sql = str(db.scalars.call_args.args[0].compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    ))
    assert "deployment_requests.tenant_id = 'tax-ml-team'" in sql
    assert "LIMIT 10" in sql


def test_list_endpoint_returns_db_records():
    principal = Principal(subject="u", username="alice", tenant_id="tax-ml-team", roles=["viewer"])
    app.dependency_overrides[get_current_principal] = lambda: principal
    app.dependency_overrides[get_db] = lambda: Mock()
    record = SimpleNamespace(
        request_id=uuid4(), status="pending_approval", execution_status="not_started",
        execution_message=None, tenant_id="tax-ml-team", model_name="tax-document-classifier",
        model_version="1", environment="dev", requested_by="alice",
        decision_by=None, decision_reason=None,
    )
    try:
        with patch("app.main.list_deployments", return_value=[record]):
            response = TestClient(app).get("/deployments")
        assert response.status_code == 200
        assert response.json()[0]["model_name"] == "tax-document-classifier"
    finally:
        app.dependency_overrides.clear()
