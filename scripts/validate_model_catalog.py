#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

NAME = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z")
required = {
    "name", "display_name", "description", "model_format", "runtime",
    "service_account", "storage_secret", "environments",
}
path = Path(sys.argv[1] if len(sys.argv) > 1 else "platform/model-catalog.json")
models = json.loads(path.read_text()).get("models", [])
assert models, "catalog must contain at least one model"
names = set()
for model in models:
    assert required <= model.keys(), f"missing fields for {model.get('name')}"
    assert NAME.fullmatch(model["name"]), f"invalid model name {model['name']}"
    assert model["name"] not in names, f"duplicate model {model['name']}"
    assert model["model_format"] == "mlflow", "only MLflow is supported"
    assert model["runtime"] == "kserve-mlserver", "unsupported runtime"
    assert set(model["environments"]) <= {"dev", "staging"}
    names.add(model["name"])
print(f"Validated {len(models)} model catalog entries")
