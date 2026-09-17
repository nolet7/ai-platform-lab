#!/usr/bin/env python3
"""Bootstrap an external, model-scoped MinIO credential for KServe.

The Kubernetes Secret is intentionally created outside Git: credentials are
runtime state. GitOps owns the ServiceAccount and InferenceService references.
"""
import base64
import json
import os
import re
import secrets
import shlex
import socket
import subprocess
import sys
import time

NAMESPACE = "ml-platform"
SECRET_NAME = "tax-classifier-s3"
PORT = 19000
MC_IMAGE = "quay.io/minio/mc@sha256:a7fe349ef4bd8521fb8497f55c6042871b2ae640607cf99d9bede5e9bdf11727"


def run(args, *, input_text=None, env=None):
    result = subprocess.run(
        args, input=input_text, text=True, capture_output=True, env=env,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(f"{args[0]} failed: {result.stderr.strip()[:500]}")
    return result.stdout


def resolve_path():
    output = run(["bash", "scripts/ml-platform/resolve-tax-classifier-model.sh"])
    values = {}
    for line in output.splitlines():
        key, value = line.removeprefix("export ").split("=", 1)
        values[key] = shlex.split(value)[0]
    path = values["MODEL_ARTIFACT_PATH"]
    if not re.fullmatch(r"[0-9]+/models/m-[a-zA-Z0-9]+/artifacts", path):
        raise RuntimeError("Unexpected artifact path; refusing to grant S3 access")
    return path


def main():
    existing = run(
        ["kubectl", "get", "secret", SECRET_NAME, "-n", NAMESPACE,
         "--ignore-not-found", "-o", "name"]
    )
    path = resolve_path()
    with socket.socket() as check:
        if check.connect_ex(("127.0.0.1", PORT)) == 0:
            raise RuntimeError(f"localhost port {PORT} is occupied")
    root = json.loads(run(
        ["kubectl", "get", "secret", "minio-credentials", "-n", NAMESPACE, "-o", "json"]
    ))["data"]
    root_user = base64.b64decode(root["MINIO_ROOT_USER"]).decode()
    root_password = base64.b64decode(root["MINIO_ROOT_PASSWORD"]).decode()
    if existing.strip():
        current = json.loads(run(["kubectl", "get", "secret", SECRET_NAME,
                                  "-n", NAMESPACE, "-o", "json"]))
        access_key = base64.b64decode(current["data"]["AWS_ACCESS_KEY_ID"]).decode()
        secret_key = base64.b64decode(current["data"]["AWS_SECRET_ACCESS_KEY"]).decode()
    else:
        access_key = "tax-classifier-serving"
        secret_key = secrets.token_urlsafe(36)
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["s3:ListBucket"],
                "Resource": ["arn:aws:s3:::mlflow-artifacts"],
            },
            {
                "Effect": "Allow",
                "Action": ["s3:GetObject"],
                "Resource": ["arn:aws:s3:::mlflow-artifacts/" + path + "/*"],
            },
        ],
    }
    forward = subprocess.Popen(
        ["kubectl", "port-forward", "-n", NAMESPACE, "svc/minio",
         f"{PORT}:9000", "--address", "127.0.0.1"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(40):
            if forward.poll() is not None:
                raise RuntimeError("MinIO port-forward exited")
            try:
                with socket.create_connection(("127.0.0.1", PORT), timeout=0.2):
                    break
            except OSError:
                time.sleep(0.25)
        else:
            raise RuntimeError("MinIO port-forward did not become ready")
        env = os.environ.copy()
        env.update({
            "ROOT_USER": root_user,
            "ROOT_PASSWORD": root_password,
            "SERVING_USER": access_key,
            "SERVING_PASSWORD": secret_key,
        })
        script = (
            "set -eu; "
            "cat > /tmp/policy.json; "
            "mc alias set root http://127.0.0.1:19000 \"$ROOT_USER\" \"$ROOT_PASSWORD\" >/dev/null; "
            "mc admin policy create root tax-classifier-artifact-readonly /tmp/policy.json >/dev/null; "
            "mc admin user add root \"$SERVING_USER\" \"$SERVING_PASSWORD\" >/dev/null; "
            "mc admin policy attach root tax-classifier-artifact-readonly --user \"$SERVING_USER\" >/dev/null; "
            "mc alias set serving http://127.0.0.1:19000 \"$SERVING_USER\" \"$SERVING_PASSWORD\" >/dev/null; "
            f"mc cat serving/mlflow-artifacts/{path}/MLmodel > /dev/null"
        )
        run(
            ["docker", "run", "--rm", "--network", "host", "-i",
             "--entrypoint", "/bin/sh", "-e", "ROOT_USER", "-e", "ROOT_PASSWORD",
             "-e", "SERVING_USER", "-e", "SERVING_PASSWORD", MC_IMAGE,
             "-c", script],
            input_text=json.dumps(policy), env=env,
        )
        secret = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": SECRET_NAME,
                "namespace": NAMESPACE,
                "annotations": {
                    "serving.kserve.io/s3-endpoint": "minio.ml-platform.svc.cluster.local:9000",
                    "serving.kserve.io/s3-usehttps": "0",
                    "serving.kserve.io/s3-region": "us-east-1",
                    "serving.kserve.io/s3-useanoncredential": "false",
                },
            },
            "type": "Opaque",
            "data": {
                "AWS_ACCESS_KEY_ID": base64.b64encode(access_key.encode()).decode(),
                "AWS_SECRET_ACCESS_KEY": base64.b64encode(secret_key.encode()).decode(),
            },
        }
        if existing.strip():
            secret["metadata"]["resourceVersion"] = current["metadata"]["resourceVersion"]
            operation = "replace"
        else:
            operation = "create"
        run(["kubectl", operation, "-f", "-"], input_text=json.dumps(secret))
        print("Configured scoped KServe S3 Secret; artifact read verified")
    finally:
        forward.terminate()
        try:
            forward.wait(timeout=5)
        except subprocess.TimeoutExpired:
            forward.kill()
            forward.wait()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
