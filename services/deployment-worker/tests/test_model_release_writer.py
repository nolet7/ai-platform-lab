import os
import sys
import unittest
from pathlib import Path
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", "postgresql://unused/unused")
os.environ.setdefault("REDIS_PASSWORD", "unused")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.model_release_writer import ModelReleaseError, render_model_release_files

MODEL_ID = "m-" + "a" * 32
REFERENCE = {
    "model_name": "tax-document-classifier",
    "model_version": "1",
    "model_id": MODEL_ID,
    "run_id": "b" * 32,
    "source_git_sha": "c" * 40,
    "dataset_version": "synthetic-demo-v1",
    "storage_uri": "s3://mlflow-artifacts/2/models/" + MODEL_ID + "/artifacts",
}


class ModelReleaseWriterTests(unittest.TestCase):
    def setUp(self):
        self.payload = {
            "tenant_id": "tax-ml-team",
            "model_name": "tax-document-classifier",
            "model_version": "1",
            "environment": "staging",
            "request_id": str(uuid4()),
            "model_reference": REFERENCE,
        }

    def test_renders_pinned_kserve_release(self):
        files, metadata = render_model_release_files(self.payload)
        self.assertEqual(metadata["namespace"], "ml-platform")
        self.assertEqual(metadata["model_id"], MODEL_ID)
        self.assertEqual(len(files), 5)
        workspace = next(v for k, v in files.items() if k.endswith("/workspace.yaml"))
        self.assertIn("kind: ModelWorkspace", workspace)
        self.assertIn("name: model-workspace-local", workspace)
        self.assertIn(self.payload["request_id"], workspace)
        manifest = next(v for k, v in files.items() if k.endswith("/inferenceservice.yaml"))
        self.assertIn("kind: InferenceService", manifest)
        self.assertIn("name: tax-document-classifier-tax-ml-team-stg", manifest)
        self.assertEqual(metadata["workload"], "tax-document-classifier-tax-ml-team-stg")
        self.assertEqual(metadata["workspace"], "tax-document-classifier-tax-ml-team-staging")
        self.assertIn(REFERENCE["storage_uri"], manifest)
        self.assertIn(REFERENCE["source_git_sha"], manifest)
        self.assertNotIn("@candidate", manifest)

    def test_blocks_direct_production(self):
        payload = {**self.payload, "environment": "prod"}
        with self.assertRaises(ModelReleaseError):
            render_model_release_files(payload)

    def test_rejects_mismatched_reference(self):
        payload = {**self.payload, "model_reference": {
            **REFERENCE, "storage_uri": "s3://mlflow-artifacts/2/models/m-wrong/artifacts"
        }}
        with self.assertRaises(ModelReleaseError):
            render_model_release_files(payload)


if __name__ == "__main__":
    unittest.main()
