import argparse
import json
from pathlib import Path

import joblib
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split

from train import build_pipeline, load_dataset


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--model-output", type=Path, required=True)
    parser.add_argument("--metrics-output", type=Path, required=True)
    parser.add_argument("--minimum-macro-f1", type=float, required=True)
    args = parser.parse_args()
    frame = load_dataset(args.data)
    features = frame.drop(columns=["label", "transaction_id"])
    labels = frame["label"]
    x_train, x_test, y_train, y_test = train_test_split(
        features, labels, test_size=0.25, random_state=42, stratify=labels
    )
    model = build_pipeline().fit(x_train, y_train)
    predictions = model.predict(x_test)
    metrics = {
        "accuracy": float(accuracy_score(y_test, predictions)),
        "macro_f1": float(f1_score(y_test, predictions, average="macro")),
    }
    if metrics["macro_f1"] < args.minimum_macro_f1:
        raise RuntimeError("model did not pass the macro-F1 quality gate")
    args.model_output.parent.mkdir(parents=True, exist_ok=True)
    args.metrics_output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, args.model_output)
    args.metrics_output.write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
