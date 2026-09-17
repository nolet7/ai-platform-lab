import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.model_registry import ModelResolutionError, resolve_model_version

MODEL_ID = "m-" + "a" * 32
RUN_ID = "b" * 32
SHA = "c" * 40


def fixture(base, path, params):
    if path == "model-versions/get":
        return {"model_version": {
            "name": "tax-document-classifier", "version": "1",
            "status": "READY", "source": "models:/" + MODEL_ID,
            "run_id": RUN_ID,
            "tags": [
                {"key": "source-git-commit", "value": SHA},
                {"key": "dataset-version", "value": "synthetic-demo-v1"},
            ],
        }}
    if path == "model-versions/get-download-uri":
        return {"artifact_uri": (
            "mlflow-artifacts:/2/models/" + MODEL_ID + "/artifacts"
        )}
    if path == "runs/get":
        return {"run": {
            "info": {"run_id": RUN_ID},
            "data": {
                "tags": [
                    {"key": "source.git.commit", "value": SHA},
                    {"key": "dataset.version", "value": "synthetic-demo-v1"},
                    {"key": "dataset.type", "value": "synthetic-demo"},
                ],
                "params": [
                    {"key": "dataset_version", "value": "synthetic-demo-v1"}
                ],
                "metrics": [{"key": "macro_f1", "value": 1.0}],
            },
        }}
    raise AssertionError(path)


class ModelRegistryTests(unittest.TestCase):
    def test_resolves_immutable_uri(self):
        result = resolve_model_version(
            "tax-document-classifier", "1", "http://mlflow", fixture
        )
        self.assertEqual(result["model_id"], MODEL_ID)
        self.assertEqual(
            result["storage_uri"],
            "s3://mlflow-artifacts/2/models/" + MODEL_ID + "/artifacts",
        )

    def test_rejects_alias_or_invalid_version(self):
        for version in ("candidate", "0", "1\nkind: Secret"):
            with self.subTest(version=version):
                with self.assertRaises(ModelResolutionError):
                    resolve_model_version(
                        "tax-document-classifier", version,
                        "http://mlflow", fixture
                    )

    def test_rejects_artifact_mismatch(self):
        def wrong_uri(base, path, params):
            result = fixture(base, path, params)
            if path.endswith("get-download-uri"):
                result["artifact_uri"] = "mlflow-artifacts:/2/models/m-wrong/artifacts"
            return result
        with self.assertRaises(ModelResolutionError):
            resolve_model_version(
                "tax-document-classifier", "1", "http://mlflow", wrong_uri
            )

    def test_rejects_lineage_mismatch(self):
        def wrong_sha(base, path, params):
            result = fixture(base, path, params)
            if path == "runs/get":
                result["run"]["data"]["tags"][0]["value"] = "d" * 40
            return result
        with self.assertRaises(ModelResolutionError):
            resolve_model_version(
                "tax-document-classifier", "1", "http://mlflow", wrong_sha
            )


if __name__ == "__main__":
    unittest.main()
