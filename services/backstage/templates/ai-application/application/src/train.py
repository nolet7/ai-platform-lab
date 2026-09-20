#!/usr/bin/env python3
"""Train and register a fictional transaction tax-category classifier."""
import argparse
import hashlib
import json
import os
from pathlib import Path

import mlflow
import mlflow.sklearn
import pandas as pd
from mlflow import MlflowClient
from mlflow.models import infer_signature
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

MODEL_NAME = os.getenv("MODEL_NAME", "${{ values.name }}")
DATASET_VERSION = os.environ.get("DATASET_VERSION", "mock-tax-transactions-v1")
SOURCE_GIT_SHA = os.environ.get("SOURCE_GIT_SHA", "unknown")
TRACKING_URI = os.environ.get(
    "MLFLOW_TRACKING_URI", "http://mlflow.ml-platform.svc.cluster.local:5000"
)
REQUIRED_COLUMNS = {
    "transaction_id", "item_description", "product_category", "amount",
    "destination_state", "exemption_certificate", "customer_type", "label",
}


def load_dataset(path):
    frame = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"Dataset missing columns: {sorted(missing)}")
    if frame.empty or frame["label"].nunique() < 2:
        raise ValueError("Dataset must contain rows from multiple labels")
    if frame["transaction_id"].duplicated().any():
        raise ValueError("transaction_id must be unique")
    return frame


def build_pipeline():
    return Pipeline([
        ("features", ColumnTransformer([
            ("description", TfidfVectorizer(ngram_range=(1, 2)), "item_description"),
            ("categories", OneHotEncoder(handle_unknown="ignore"), [
                "product_category", "destination_state",
                "exemption_certificate", "customer_type",
            ]),
            ("amount", StandardScaler(), ["amount"]),
        ])),
        ("classifier", LogisticRegression(
            max_iter=1000, class_weight="balanced", random_state=42
        )),
    ])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--minimum-macro-f1", type=float, default=0.80)
    args = parser.parse_args()
    frame = load_dataset(args.data)
    features = frame.drop(columns=["label", "transaction_id"])
    labels = frame["label"]
    x_train, x_test, y_train, y_test = train_test_split(
        features, labels, test_size=0.25, random_state=42, stratify=labels
    )
    model = build_pipeline()
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    macro_f1 = float(f1_score(y_test, predictions, average="macro"))
    accuracy = float(accuracy_score(y_test, predictions))
    if macro_f1 < args.minimum_macro_f1:
        raise RuntimeError(
            f"macro F1 {macro_f1:.3f} is below {args.minimum_macro_f1:.3f}"
        )
    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment("mock-taxtech-tax-category")
    with mlflow.start_run(run_name=f"{MODEL_NAME}-{DATASET_VERSION}") as run:
        mlflow.set_tags({
            "platform": "ai-platform-lab",
            "workload": MODEL_NAME,
            "dataset.version": DATASET_VERSION,
            "dataset.sha256": hashlib.sha256(args.data.read_bytes()).hexdigest(),
            "dvc.lock.sha256": hashlib.sha256(Path("dvc.lock").read_bytes()).hexdigest(),
            "dataset.type": "synthetic-fictional-tax-transactions",
            "source.repository": "https://github.com/${{ values.githubOwner }}/${{ values.name }}.git",
            "source.git.commit": SOURCE_GIT_SHA,
            "model.lifecycle": "candidate",
            "environment": "dev",
            "data.classification": "synthetic",
        })
        mlflow.log_params({
            "algorithm": "logistic-regression",
            "dataset_version": DATASET_VERSION,
            "training_rows": len(x_train),
            "test_rows": len(x_test),
            "random_state": 42,
        })
        mlflow.log_metrics({"accuracy": accuracy, "macro_f1": macro_f1})
        report = Path("/tmp/mock-taxtech-classification-report.json")
        report.write_text(json.dumps(
            classification_report(y_test, predictions, output_dict=True),
            indent=2,
        ))
        mlflow.log_artifact(str(report), artifact_path="reports")
        mlflow.log_artifact("dvc.lock", artifact_path="lineage")
        mlflow.log_artifact("params.yaml", artifact_path="lineage")
        signature = infer_signature(x_train, model.predict(x_train))
        result = mlflow.sklearn.log_model(
            model,
            name="model",
            registered_model_name=MODEL_NAME,
            signature=signature,
            input_example=x_train.head(3),
        )
        version = result.registered_model_version
        if version is None:
            raise RuntimeError("MLflow did not return a registered model version")
        client = MlflowClient()
        client.set_registered_model_tag(MODEL_NAME, "owner", "${{ values.team }}")
        client.set_registered_model_tag(
            MODEL_NAME, "business-domain", "synthetic-tax-demonstration"
        )
        client.set_model_version_tag(
            MODEL_NAME, str(version), "validation-status", "candidate"
        )
        client.set_model_version_tag(
            MODEL_NAME, str(version), "dataset-version", DATASET_VERSION
        )
        client.set_model_version_tag(
            MODEL_NAME, str(version), "source-git-commit", SOURCE_GIT_SHA
        )
        print(json.dumps({
            "run_id": run.info.run_id,
            "registered_model": MODEL_NAME,
            "model_uri": result.model_uri,
            "model_version": str(version),
            "accuracy": accuracy,
            "macro_f1": macro_f1,
        }, indent=2))


if __name__ == "__main__":
    main()
