#!/usr/bin/env python3
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
source = root / "platform/model-catalog.json"
for target in (
    root / "services/platform-api/model-catalog.json",
    root / "services/deployment-worker/model-catalog.json",
):
    shutil.copyfile(source, target)
print("Synchronized model catalog into API and worker image contexts")
