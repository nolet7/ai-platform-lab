import os
import sys
import unittest
from pathlib import Path
from types import ModuleType
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", "postgresql://unused/unused")
os.environ.setdefault("REDIS_PASSWORD", "unused")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.modules.setdefault("httpx", ModuleType("httpx"))

from app.gitops_writer import GitOpsPublishError, render_gitops_files


class GitOpsWriterTests(unittest.TestCase):
    def setUp(self):
        self.payload = {
            "environment": "staging",
            "model_name": "tax-document-classifier",
            "model_version": "1",
            "tenant_id": "team-ml",
            "request_id": str(uuid4()),
        }

    def test_valid_payload_renders_expected_paths(self):
        files, metadata = render_gitops_files(self.payload)
        self.assertEqual(metadata["application"], "tax-document-classifier-staging")
        self.assertTrue(all(path.startswith("gitops/") for path in files))
        self.assertIn("MODEL_VERSION", files["gitops/workloads/tax-document-classifier/base/deployment.yaml"])

    def test_rejects_yaml_injection(self):
        for field, value in (
            ("model_name", "model\nkind: Secret"),
            ("model_version", "1\n  privileged: true"),
            ("tenant_id", "team\nadmin: true"),
        ):
            with self.subTest(field=field):
                payload = {**self.payload, field: value}
                with self.assertRaises(GitOpsPublishError):
                    render_gitops_files(payload)

    def test_rejects_path_and_invalid_request_id(self):
        for field, value in (
            ("model_name", "../escape"),
            ("tenant_id", "Team With Spaces"),
            ("request_id", "invalid"),
        ):
            with self.subTest(field=field):
                payload = {**self.payload, field: value}
                with self.assertRaises(GitOpsPublishError):
                    render_gitops_files(payload)


if __name__ == "__main__":
    unittest.main()
