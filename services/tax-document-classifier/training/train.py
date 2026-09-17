#!/usr/bin/env python3

import argparse
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
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "http://mlflow.ml-platform.svc.cluster.local:5000",
)

EXPERIMENT_NAME = os.getenv(
    "MLFLOW_EXPERIMENT_NAME",
    "tax-document-classifier-training",
)

MODEL_NAME = os.getenv(
    "REGISTERED_MODEL_NAME",
    "tax-document-classifier",
)

MODEL_ALIAS = os.getenv(
    "MODEL_ALIAS",
    "candidate",
)

DATASET_VERSION = os.getenv(
    "DATASET_VERSION",
    "synthetic-demo-v1",
)

SOURCE_GIT_COMMIT = os.getenv(
    "APP_GIT_COMMIT_SHA",
    "unknown",
)

SOURCE_REPOSITORY = os.getenv(
    "SOURCE_REPOSITORY",
    "https://github.com/nolet7/ai-platform-lab.git",
)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--data",
        required=True,
    )

    args = parser.parse_args()

    data_path = Path(args.data)

    if not data_path.exists():
        raise FileNotFoundError(
            f"Dataset does not exist: {data_path}"
        )

    frame = pd.read_csv(data_path)

    required_columns = {
        "document_id",
        "text",
        "label",
    }

    missing = required_columns - set(frame.columns)

    if missing:
        raise ValueError(
            f"Dataset missing columns: {sorted(missing)}"
        )

    if frame.empty:
        raise ValueError(
            "Dataset contains no rows"
        )

    print(
        f"Dataset rows: {len(frame)}"
    )

    print(
        f"Labels: {sorted(frame['label'].unique())}"
    )

    X = frame[["text"]]
    y = frame["label"]

    X_train, X_test, y_train, y_test = (
        train_test_split(
            X,
            y,
            test_size=0.25,
            random_state=42,
            stratify=y,
        )
    )

    text_transformer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        sublinear_tf=True,
        max_features=5000,
    )

    preprocessing = ColumnTransformer(
        transformers=[
            (
                "document_text",
                text_transformer,
                "text",
            ),
        ],
        remainder="drop",
    )

    classifier = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        random_state=42,
    )

    model = Pipeline(
        steps=[
            ("preprocessing", preprocessing),
            ("classifier", classifier),
        ]
    )

    mlflow.set_tracking_uri(
        TRACKING_URI
    )

    mlflow.set_experiment(
        EXPERIMENT_NAME
    )

    run_name = (
        f"tax-document-classifier-"
        f"{DATASET_VERSION}"
    )

    with mlflow.start_run(
        run_name=run_name
    ) as run:

        mlflow.set_tags(
            {
                "platform": "ai-platform-lab",
                "workload": "tax-document-classifier",
                "dataset.version": DATASET_VERSION,
                "dataset.type": "synthetic-demo",
                "source.repository": SOURCE_REPOSITORY,
                "source.git.commit": SOURCE_GIT_COMMIT,
                "model.lifecycle": "candidate",
                "environment": "dev",
            }
        )

        mlflow.log_params(
            {
                "algorithm": "logistic-regression",
                "feature_extractor": "tfidf",
                "ngram_range": "1,2",
                "max_features": 5000,
                "test_size": 0.25,
                "random_state": 42,
                "training_rows": len(X_train),
                "test_rows": len(X_test),
                "dataset_version": DATASET_VERSION,
            }
        )

        model.fit(
            X_train,
            y_train,
        )

        predictions = model.predict(
            X_test
        )

        accuracy = accuracy_score(
            y_test,
            predictions,
        )

        macro_f1 = f1_score(
            y_test,
            predictions,
            average="macro",
        )

        weighted_f1 = f1_score(
            y_test,
            predictions,
            average="weighted",
        )

        mlflow.log_metrics(
            {
                "accuracy": float(accuracy),
                "macro_f1": float(macro_f1),
                "weighted_f1": float(weighted_f1),
            }
        )

        labels = sorted(
            frame["label"].unique()
        )

        report = classification_report(
            y_test,
            predictions,
            labels=labels,
            output_dict=True,
            zero_division=0,
        )

        matrix = confusion_matrix(
            y_test,
            predictions,
            labels=labels,
        )

        reports_directory = Path(
            "/tmp/tax-classifier-reports"
        )

        reports_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        classification_report_path = (
            reports_directory
            / "classification_report.json"
        )

        confusion_matrix_path = (
            reports_directory
            / "confusion_matrix.csv"
        )

        with classification_report_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                report,
                file,
                indent=2,
            )

        confusion_frame = pd.DataFrame(
            matrix,
            index=labels,
            columns=labels,
        )

        confusion_frame.to_csv(
            confusion_matrix_path
        )

        mlflow.log_artifact(
            str(classification_report_path),
            artifact_path="evaluation",
        )

        mlflow.log_artifact(
            str(confusion_matrix_path),
            artifact_path="evaluation",
        )

        mlflow.log_artifact(
            str(data_path),
            artifact_path="dataset",
        )

        signature = infer_signature(
            X_test,
            predictions,
        )

        input_example = (
            X_test
            .head(5)
            .reset_index(drop=True)
        )

        model_info = (
            mlflow.sklearn.log_model(
                sk_model=model,
                name="model",
                signature=signature,
                input_example=input_example,
                registered_model_name=MODEL_NAME,
                serialization_format="cloudpickle",
                metadata={
                    "business_domain": "tax-document-processing",
                    "dataset_version": DATASET_VERSION,
                    "source_git_commit": SOURCE_GIT_COMMIT,
                },
            )
        )

        version = (
            model_info.registered_model_version
        )

        if version is None:
            raise RuntimeError(
                "MLflow did not return a "
                "registered model version"
            )

        client = MlflowClient()

        client.set_registered_model_alias(
            name=MODEL_NAME,
            alias=MODEL_ALIAS,
            version=str(version),
        )

        client.set_registered_model_tag(
            MODEL_NAME,
            "owner",
            "ai-platform-team",
        )

        client.set_registered_model_tag(
            MODEL_NAME,
            "business-domain",
            "tax-document-processing",
        )

        client.set_model_version_tag(
            name=MODEL_NAME,
            version=str(version),
            key="validation-status",
            value="candidate",
        )

        client.set_model_version_tag(
            name=MODEL_NAME,
            version=str(version),
            key="dataset-version",
            value=DATASET_VERSION,
        )

        client.set_model_version_tag(
            name=MODEL_NAME,
            version=str(version),
            key="source-git-commit",
            value=SOURCE_GIT_COMMIT,
        )

        print()
        print("===== TRAINING RESULT =====")
        print(f"RUN_ID={run.info.run_id}")
        print(f"ACCURACY={accuracy:.4f}")
        print(f"MACRO_F1={macro_f1:.4f}")
        print(
            f"WEIGHTED_F1={weighted_f1:.4f}"
        )
        print(
            f"REGISTERED_MODEL={MODEL_NAME}"
        )
        print(
            f"MODEL_VERSION={version}"
        )
        print(
            f"MODEL_ALIAS={MODEL_ALIAS}"
        )
        print(
            "MODEL_ALIAS_URI="
            f"models:/{MODEL_NAME}@{MODEL_ALIAS}"
        )
        print(
            f"SOURCE_GIT_COMMIT={SOURCE_GIT_COMMIT}"
        )
        print("===========================")


if __name__ == "__main__":
    main()
