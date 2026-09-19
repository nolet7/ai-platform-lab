"""Read and validate the declarative model onboarding catalog."""
import json
import os
from pathlib import Path


def catalog_path():
    configured = os.getenv("MODEL_CATALOG_PATH")
    if configured:
        return Path(configured)
    packaged = Path("/app/model-catalog.json")
    if packaged.exists():
        return packaged
    return Path(__file__).resolve().parents[3] / "platform" / "model-catalog.json"


def load_model_catalog():
    document = json.loads(catalog_path().read_text())
    if document.get("schema_version") != "1.0":
        raise RuntimeError("Unsupported model catalog schema")
    models = document.get("models")
    if not isinstance(models, list) or not models:
        raise RuntimeError("Model catalog must contain models")
    catalog = {item["name"]: item for item in models}
    if len(catalog) != len(models):
        raise RuntimeError("Model catalog names must be unique")
    return catalog


def get_model_config(name):
    return load_model_catalog().get(name)
