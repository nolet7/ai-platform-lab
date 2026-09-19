"""Offline qualification; implement the project functions in train.py first."""
import json
from pathlib import Path
import joblib
import yaml
from train import load_training_data, build_and_evaluate

params = yaml.safe_load(Path("params.yaml").read_text())
model, macro_f1 = build_and_evaluate(load_training_data())
if not params["minimum_macro_f1"] <= macro_f1 <= 1:
    raise ValueError("Model failed the macro F1 quality gate")
Path("models").mkdir(exist_ok=True)
Path("reports").mkdir(exist_ok=True)
joblib.dump(model, "models/model.joblib")
Path("reports/metrics.json").write_text(json.dumps({"macro_f1": macro_f1}) + "\n")
