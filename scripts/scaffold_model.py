#!/usr/bin/env python3
"""Create a project from the governed MLflow/KServe golden template."""
import argparse
import re
import shutil
from pathlib import Path

NAME = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("--display-name", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--output", type=Path, default=Path("services"))
    args = parser.parse_args()
    if not NAME.fullmatch(args.name):
        parser.error("name must be a Kubernetes DNS label")
    source = Path(__file__).resolve().parents[1] / "templates/mlflow-kserve-model"
    target = args.output / args.name
    if target.exists():
        parser.error(f"{target} already exists")
    shutil.copytree(source, target)
    replacements = {
        "__MODEL_NAME__": args.name,
        "__DISPLAY_NAME__": args.display_name,
        "__DESCRIPTION__": args.description,
    }
    for path in target.rglob("*"):
        if path.is_file():
            text = path.read_text()
            for old, new in replacements.items():
                text = text.replace(old, new)
            path.write_text(text)
    print(target)
    print("Next: implement training, test, register the MLflow version, and")
    print("add model-template.json to platform/model-catalog.json")


if __name__ == "__main__":
    main()
