#!/usr/bin/env python3
"""Validate live MLflow candidate lineage and immutable MinIO artifacts."""

import argparse
import json
import re
import subprocess
import sys


REMOTE = r"""
import json
import os
import re
import sys

import boto3
import mlflow
from mlflow import MlflowClient

name, alias, minimum = sys.argv[1], sys.argv[2], float(sys.argv[3])
mlflow.set_tracking_uri("http://127.0.0.1:5000")
client = MlflowClient()
version = client.get_model_version_by_alias(name, alias)
if version.status != "READY":
    raise ValueError("Registry version is not ready")
if version.tags.get("validation-status") != "candidate":
    raise ValueError("Registry candidate validation tag is missing")
model_id = version.source.removeprefix("models:/")
if not re.fullmatch(r"m-[a-f0-9]{32}", model_id):
    raise ValueError("Version source is not an immutable logged model ID")
logged = mlflow.get_logged_model(model_id)
if logged.source_run_id != version.run_id:
    raise ValueError("Logged model and registry run IDs differ")
location = logged.artifact_location
prefix = "mlflow-artifacts:/"
if not location or not location.startswith(prefix):
    raise ValueError("Unsupported or empty artifact location")
path = location[len(prefix):].strip("/")
if not re.fullmatch(r"[0-9]+/models/" + re.escape(model_id) + r"/artifacts", path):
    raise ValueError("Artifact path does not match immutable model ID")
run = client.get_run(version.run_id)
source_sha = run.data.tags.get("source.git.commit", "")
if not re.fullmatch(r"[a-f0-9]{40}", source_sha):
    raise ValueError("Source Git SHA is missing")
if version.tags.get("source-git-commit") != source_sha:
    raise ValueError("Registry and run source commits differ")
dataset = run.data.tags.get("dataset.version", "")
if not dataset or dataset != run.data.params.get("dataset_version"):
    raise ValueError("Run dataset lineage is incomplete")
if version.tags.get("dataset-version") != dataset:
    raise ValueError("Registry and run dataset versions differ")
score = run.data.metrics.get("macro_f1")
if score is None or not 0 <= score <= 1 or score < minimum:
    raise ValueError("Macro F1 does not meet validation threshold")
s3 = boto3.client("s3", endpoint_url=os.environ["MLFLOW_S3_ENDPOINT_URL"])
s3.head_object(Bucket="mlflow-artifacts", Key=path + "/MLmodel")
objects = s3.list_objects_v2(
    Bucket="mlflow-artifacts", Prefix=path + "/", MaxKeys=1000
)
if objects.get("KeyCount", 0) < 2:
    raise ValueError("Model artifact prefix is incomplete")
print(json.dumps({
    "model_name": name,
    "alias": alias,
    "model_version": version.version,
    "model_id": model_id,
    "run_id": version.run_id,
    "source_git_sha": source_sha,
    "dataset_version": dataset,
    "dataset_type": run.data.tags.get("dataset.type", "unknown"),
    "macro_f1": score,
    "artifact_count": objects["KeyCount"],
    "storage_uri": "s3://mlflow-artifacts/" + path,
    "validation": "passed",
}, sort_keys=True))
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="tax-document-classifier")
    parser.add_argument("--alias", default="candidate")
    parser.add_argument("--namespace", default="ml-platform")
    parser.add_argument("--min-macro-f1", type=float, default=0.8)
    args = parser.parse_args()
    if not 0 <= args.min_macro_f1 <= 1:
        parser.error("--min-macro-f1 must be between 0 and 1")
    for field in (args.model, args.alias, args.namespace):
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,62}", field):
            parser.error("model, alias, and namespace must be DNS labels")
    command = [
        "kubectl", "exec", "-i", "-n", args.namespace,
        "deployment/mlflow", "-c", "mlflow", "--", "python", "-",
        args.model, args.alias, str(args.min_macro_f1),
    ]
    result = subprocess.run(
        command, input=REMOTE, text=True, capture_output=True, check=False
    )
    if result.returncode:
        print("Candidate validation failed in MLflow pod", file=sys.stderr)
        return 1
    try:
        evidence = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("Candidate validator returned invalid evidence", file=sys.stderr)
        return 1
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
