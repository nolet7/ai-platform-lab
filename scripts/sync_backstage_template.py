"""Build Backstage skeleton from the shared golden template (no credentials)."""
from pathlib import Path
import json
ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "templates/mlflow-kserve-model"
target = ROOT / "services/backstage/templates/ml-project/skeleton"
replacements = {"__MODEL_NAME__":"${{ values.name }}", "__DISPLAY_NAME__":"${{ values.displayName }}", "__DESCRIPTION__":"${{ values.description }}", "__OWNER__":"tax-ml-team"}
for path in source.rglob("*"):
    if not path.is_file() or any(part in {"__pycache__", ".pytest_cache", ".venv"} for part in path.parts):
        continue
    text = path.read_text()
    for old, new in replacements.items():
        if path.suffix == ".json" and old != "__OWNER__":
            text = text.replace(json.dumps(old), new[:-3] + " | dump }}")
        else:
            text = text.replace(old,new)
    out = target / path.relative_to(source)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(text)
print("Synchronized Backstage skeleton")
