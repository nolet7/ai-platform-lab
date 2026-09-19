import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def scaffold(output, name="example-model"):
    return subprocess.run([
        "python3", str(ROOT / "scripts/scaffold_model.py"), name,
        "--display-name", 'A "quoted" model', "--description", "Test",
        "--owner", "test-team", "--output", str(output),
    ], text=True, capture_output=True)

def test_scaffold_creates_independent_git_and_dvc_repo(tmp_path):
    result = scaffold(tmp_path)
    assert result.returncode == 0, result.stderr
    project = tmp_path / "example-model"
    assert (project / ".git").is_dir()
    assert (project / ".dvc/config").is_file()
    assert (project / "dvc.yaml").is_file()
    assert (project / ".github/workflows/model-ci.yaml").is_file()
    catalog = json.loads((project / "model-template.json").read_text())
    assert catalog["display_name"] == 'A "quoted" model'
    assert scaffold(tmp_path).returncode != 0

def test_scaffold_rejects_platform_subdirectory():
    result = scaffold(ROOT / "services")
    assert result.returncode != 0
    assert "outside the platform" in result.stderr
