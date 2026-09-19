#!/usr/bin/env python3
"""Create a project from the governed MLflow/KServe golden template."""
import argparse
import re
import json
import subprocess
import shutil
from pathlib import Path

NAME = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("--display-name", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--owner", required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    if not NAME.fullmatch(args.name):
        parser.error("name must be a Kubernetes DNS label")
    source = Path(__file__).resolve().parents[1] / "templates/mlflow-kserve-model"
    target = args.output / args.name
    target = target.resolve()
    platform_root = source.parents[1].resolve()
    if target == platform_root or platform_root in target.parents:
        parser.error("model repositories must be outside the platform repository")
    if target.exists():
        parser.error(f"{target} already exists")
    shutil.copytree(source, target)
    replacements = {
        "__MODEL_NAME__": args.name,
        "__DISPLAY_NAME__": args.display_name,
        "__DESCRIPTION__": args.description,
        "__OWNER__": args.owner,
    }
    for path in target.rglob("*"):
        if path.is_file():
            text = path.read_text()
            for old, new in replacements.items():
                value = json.dumps(new)[1:-1] if path.suffix == ".json" else new
                text = text.replace(old, value)
            path.write_text(text)
    subprocess.run(["git", "init", "-b", "main", str(target)], check=True)
    print(target)
    print("Next: install requirements-dev.txt, implement training, run dvc repro,")
    print("commit and publish this independent repo; submit a separate platform catalog PR.")


if __name__ == "__main__":
    main()
