#!/usr/bin/env python3
"""Exercise the synthetic tax classifier through KServe's V2 API."""
import json
import socket
import subprocess
import sys
import time
import urllib.request

PORT = 18082
BASE = f"http://127.0.0.1:{PORT}"
MODEL = "tax-document-classifier"
EXAMPLES = {
    "W-2": "Form W-2 Wage and Tax Statement. Employer Example Co. Employee wages and federal income tax withheld.",
    "INVOICE": "INVOICE INV-1001. Bill from Example Consulting. Amount due $125.00. Payment terms net 30.",
    "RECEIPT": "RECEIPT R-1002. Thank you for your purchase at Corner Market. Total paid $42.50.",
}


def request(path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        BASE + path, data=data,
        headers={"Content-Type": "application/json"} if data else {},
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        body = response.read()
        return json.loads(body) if body else {"status": response.status}


def main():
    with socket.socket() as check:
        if check.connect_ex(("127.0.0.1", PORT)) == 0:
            raise RuntimeError(f"localhost port {PORT} is occupied")
    forward = subprocess.Popen(
        ["kubectl", "port-forward", "-n", "ml-platform",
         "svc/tax-document-classifier-predictor", f"{PORT}:80",
         "--address", "127.0.0.1"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(80):
            if forward.poll() is not None:
                raise RuntimeError("port-forward exited")
            try:
                with socket.create_connection(("127.0.0.1", PORT), timeout=0.2):
                    break
            except OSError:
                time.sleep(0.25)
        else:
            raise RuntimeError("port-forward did not become ready")
        print("server:", request("/v2/health/ready"))
        print("model:", request(f"/v2/models/{MODEL}/ready"))
        for expected, text in EXAMPLES.items():
            response = request(
                f"/v2/models/{MODEL}/infer",
                {"inputs": [{
                    "name": "text", "shape": [1],
                    "datatype": "BYTES", "data": [text],
                }]},
            )
            outputs = response.get("outputs", [])
            if not outputs or not outputs[0].get("data"):
                raise RuntimeError(f"no prediction for {expected}")
            actual = outputs[0]["data"][0]
            print(f"{expected}: {actual}")
            if actual != expected:
                raise RuntimeError(f"expected {expected}, got {actual}")
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
