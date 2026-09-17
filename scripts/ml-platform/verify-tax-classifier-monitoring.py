#!/usr/bin/env python3
"""Verify the live tax classifier Prometheus scrape and alert rules."""

import json
import socket
import subprocess
import sys
import time
import urllib.parse
import urllib.request

PORT = 19090
ALERTS = {
    "TaxClassifierServingDown",
    "TaxClassifierHighInferenceErrorRate",
    "TaxClassifierHighInferenceLatency",
    "TaxClassifierPredictorRestarted",
}


def read_json(base, path):
    with urllib.request.urlopen(base + path, timeout=5) as response:
        return json.load(response)


def query(base, expression):
    path = "/api/v1/query?" + urllib.parse.urlencode({"query": expression})
    result = read_json(base, path)
    if result.get("status") != "success":
        raise RuntimeError("Prometheus query failed")
    return result["data"]["result"]


def main():
    with socket.socket() as check:
        check.bind(("127.0.0.1", PORT))
    forward = subprocess.Popen(
        ["kubectl", "-n", "observability", "port-forward",
         "service/kube-prometheus-stack-prometheus", f"{PORT}:9090",
         "--address", "127.0.0.1"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        base = f"http://127.0.0.1:{PORT}"
        for _ in range(40):
            if forward.poll() is not None:
                raise RuntimeError("Prometheus port-forward exited")
            try:
                urllib.request.urlopen(base + "/-/ready", timeout=1)
                break
            except Exception:
                time.sleep(0.5)
        else:
            raise RuntimeError("Prometheus did not become ready")

        target = query(
            base,
            'up{namespace="ml-platform",'
            'pod=~"tax-document-classifier-predictor-.*",'
            'job="ml-platform/tax-classifier-mlserver"}',
        )
        if len(target) != 1 or target[0]["value"][1] != "1":
            raise RuntimeError("Classifier PodMonitor target is not up=1")
        print("scrape:", target[0]["metric"]["pod"], "up=1")

        series = query(
            base,
            'model_infer_request_success_total{namespace="ml-platform",'
            'model="tax-document-classifier"}',
        )
        if not series:
            raise RuntimeError("Inference success metric is absent")
        print("inference success metric:", series[0]["value"][1])

        groups = read_json(base, "/api/v1/rules")["data"]["groups"]
        loaded = {
            rule["name"]
            for group in groups
            for rule in group["rules"]
            if rule.get("name") in ALERTS
        }
        missing = ALERTS - loaded
        if missing:
            raise RuntimeError("Missing alert rules: " + ", ".join(sorted(missing)))
        print("alert rules:", ", ".join(sorted(loaded)))
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
    except Exception as error:
        print("ERROR:", error, file=sys.stderr)
        raise SystemExit(1)
