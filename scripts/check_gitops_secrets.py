#!/usr/bin/env python3
"""Validate GitOps YAML and reject inline Kubernetes Secret payloads."""

from pathlib import Path
import sys

import yaml


def main() -> int:
    count = 0
    for directory in (Path("gitops"), Path("observability")):
        for path in sorted(directory.rglob("*.yaml")):
            try:
                documents = list(yaml.safe_load_all(path.read_text()))
            except yaml.YAMLError as exc:
                print(f"Invalid YAML: {path}: {exc}", file=sys.stderr)
                return 1
            for document in documents:
                if not isinstance(document, dict):
                    continue
                count += 1
                if document.get("kind") != "Secret":
                    continue
                if any(document.get(field) for field in ("data", "stringData", "binaryData")):
                    name = document.get("metadata", {}).get("name", "<unnamed>")
                    print(f"Inline Secret payload forbidden: {path}: {name}", file=sys.stderr)
                    return 1
    print(f"Validated {count} GitOps YAML documents; no inline Secret payloads.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())