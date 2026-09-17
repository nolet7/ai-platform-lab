#!/usr/bin/env bash
set -euo pipefail
MODEL_NAME="${1:-tax-document-classifier}"
MODEL_ALIAS="${2:-candidate}"
NAMESPACE="${3:-ml-platform}"
metadata="$(kubectl exec -i -n "$NAMESPACE" deployment/mlflow -c mlflow -- env MODEL_NAME="$MODEL_NAME" MODEL_ALIAS="$MODEL_ALIAS" python - <<'PY'
import os
import boto3
import mlflow
from mlflow import MlflowClient
name = os.environ["MODEL_NAME"]
alias = os.environ["MODEL_ALIAS"]
mlflow.set_tracking_uri("http://127.0.0.1:5000")
client = MlflowClient()
version = client.get_model_version_by_alias(name, alias)
model_id = version.source.rsplit("/", 1)[-1]
if not model_id.startswith("m-"):
    raise ValueError("Alias did not resolve to an immutable logged model ID")
logged_model = mlflow.get_logged_model(model_id)
location = logged_model.artifact_location
prefix = "mlflow-artifacts:/"
if not location or not location.startswith(prefix):
    raise ValueError("Logged model has no supported artifact location")
path = location[len(prefix):].strip("/")
if not path or ".." in path.split("/"):
    raise ValueError("Logged model artifact path is invalid")
s3 = boto3.client("s3", endpoint_url=os.environ["MLFLOW_S3_ENDPOINT_URL"])
bucket = "mlflow-artifacts"
s3.head_object(Bucket=bucket, Key=path + "/MLmodel")
objects = s3.list_objects_v2(Bucket=bucket, Prefix=path + "/")
if objects.get("KeyCount", 0) < 2:
    raise ValueError("Logged model artifacts are incomplete in MinIO")
run = client.get_run(version.run_id)
print(version.version)
print(version.run_id)
print(model_id)
print(location)
print(path)
print(run.data.tags.get("source.git.commit", "unknown"))
print(objects["KeyCount"])
PY
)"
mapfile -t fields <<< "$metadata"
if [[ ${#fields[@]} -ne 7 ]]; then
  echo "ERROR: incomplete model metadata" >&2
  exit 1
fi
printf 'export MODEL_NAME=%q\n' "$MODEL_NAME"
printf 'export MODEL_ALIAS=%q\n' "$MODEL_ALIAS"
printf 'export MODEL_VERSION=%q\n' "${fields[0]}"
printf 'export MODEL_RUN_ID=%q\n' "${fields[1]}"
printf 'export MODEL_ID=%q\n' "${fields[2]}"
printf 'export MODEL_ARTIFACT_LOCATION=%q\n' "${fields[3]}"
printf 'export MODEL_ARTIFACT_PATH=%q\n' "${fields[4]}"
printf 'export MODEL_SOURCE_GIT_SHA=%q\n' "${fields[5]}"
printf 'export MODEL_OBJECT_COUNT=%q\n' "${fields[6]}"
printf 'export KSERVE_STORAGE_URI=%q\n' "s3://mlflow-artifacts/${fields[4]}"
