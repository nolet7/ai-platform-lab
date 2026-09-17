"""Resolve an approved numeric MLflow model version to immutable lineage."""

import json
import re
import urllib.parse
import urllib.request


MODEL_ID = re.compile(r"m-[a-f0-9]{32}\Z")
RUN_ID = re.compile(r"[a-f0-9]{32}\Z")
GIT_SHA = re.compile(r"[a-f0-9]{40}\Z")
VERSION = re.compile(r"[1-9][0-9]*\Z")
NAME = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z")


class ModelResolutionError(ValueError):
    pass


def fetch_json(base_url, path, params):
    url = (
        base_url.rstrip("/")
        + "/api/2.0/mlflow/"
        + path
        + "?"
        + urllib.parse.urlencode(params)
    )
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return json.load(response)
    except Exception as error:
        raise ModelResolutionError(
            "MLflow registry lookup failed"
        ) from error


def _values(items):
    return {item["key"]: item["value"] for item in items}


def resolve_model_version(name, version, base_url, get_json=fetch_json):
    if not isinstance(name, str) or not NAME.fullmatch(name):
        raise ModelResolutionError("Model name must be a DNS label")
    if not isinstance(version, str) or not VERSION.fullmatch(version):
        raise ModelResolutionError("Model version must be a positive integer")

    params = {"name": name, "version": version}
    record = get_json(
        base_url, "model-versions/get", params
    )["model_version"]
    if (
        record.get("name") != name
        or record.get("version") != version
        or record.get("status") != "READY"
    ):
        raise ModelResolutionError("Model version is not READY")
    source = record.get("source", "")
    if not source.startswith("models:/"):
        raise ModelResolutionError("Model source is not immutable")
    model_id = source[len("models:/"):]
    if not MODEL_ID.fullmatch(model_id):
        raise ModelResolutionError("Model ID is invalid")
    run_id = record.get("run_id", "")
    if not RUN_ID.fullmatch(run_id):
        raise ModelResolutionError("Run ID is invalid")

    artifact_uri = get_json(
        base_url, "model-versions/get-download-uri", params
    )["artifact_uri"]
    match = re.fullmatch(
        r"mlflow-artifacts:/([0-9]+)/models/"
        + re.escape(model_id)
        + r"/artifacts",
        artifact_uri,
    )
    if not match:
        raise ModelResolutionError(
            "Artifact URI does not match immutable model ID"
        )

    tags = _values(record.get("tags", []))
    run = get_json(
        base_url, "runs/get", {"run_id": run_id}
    )["run"]
    if run.get("info", {}).get("run_id") != run_id:
        raise ModelResolutionError("Run ID mismatch")
    data = run.get("data", {})
    run_tags = _values(data.get("tags", []))
    params_data = _values(data.get("params", []))
    metrics = _values(data.get("metrics", []))
    source_sha = run_tags.get("source.git.commit", "")
    dataset = run_tags.get("dataset.version", "")
    if not GIT_SHA.fullmatch(source_sha):
        raise ModelResolutionError("Source Git SHA is missing")
    if tags.get("source-git-commit") != source_sha:
        raise ModelResolutionError("Registry source Git SHA mismatch")
    if (
        not dataset
        or tags.get("dataset-version") != dataset
        or params_data.get("dataset_version") != dataset
    ):
        raise ModelResolutionError("Dataset lineage mismatch")
    try:
        macro_f1 = float(metrics["macro_f1"])
    except (KeyError, TypeError, ValueError) as error:
        raise ModelResolutionError("Macro F1 is missing") from error
    if not 0 <= macro_f1 <= 1:
        raise ModelResolutionError("Macro F1 is invalid")

    return {
        "model_name": name,
        "model_version": version,
        "model_id": model_id,
        "run_id": run_id,
        "source_git_sha": source_sha,
        "dataset_version": dataset,
        "dataset_type": run_tags.get("dataset.type", "unknown"),
        "macro_f1": macro_f1,
        "artifact_uri": artifact_uri,
        "storage_uri": "s3://mlflow-artifacts/"
        + match.group(1)
        + "/models/"
        + model_id
        + "/artifacts",
    }
