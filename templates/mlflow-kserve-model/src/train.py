"""Golden-path training entry point.

Implement the two project functions and retain the lineage contract.
"""
import os
import mlflow

MODEL_NAME = os.environ["MODEL_NAME"]
DATASET_VERSION = os.environ["DATASET_VERSION"]
SOURCE_GIT_SHA = os.environ["SOURCE_GIT_SHA"]


def load_training_data():
    raise NotImplementedError("Load versioned training data")


def build_and_evaluate(training_data):
    raise NotImplementedError("Return an MLflow-compatible model and macro F1")


def main():
    data = load_training_data()
    model, macro_f1 = build_and_evaluate(data)
    if not 0 <= macro_f1 <= 1:
        raise ValueError("macro F1 must be between zero and one")
    with mlflow.start_run():
        mlflow.set_tags({
            "source.git.commit": SOURCE_GIT_SHA,
            "dataset.version": DATASET_VERSION,
            "dataset.type": "replace-me",
        })
        mlflow.log_param("dataset_version", DATASET_VERSION)
        mlflow.log_metric("macro_f1", macro_f1)
        mlflow.sklearn.log_model(
            model, "model", registered_model_name=MODEL_NAME
        )


if __name__ == "__main__":
    main()
