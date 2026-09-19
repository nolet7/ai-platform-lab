# ${{ values.displayName }}

Owned by tax-ml-team. This independent model repository was created by AI Platform.

## Develop

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
dvc repro
pytest -q
dvc metrics show
```

The starter uses fictional tax transactions to demonstrate a complete training
pipeline. Replace the synthetic generator, features and tests with your project.
The demonstration labels and accuracy are not real tax or compliance guidance.

## Version data and models in MinIO

The default DVC remote is the project prefix in the team's ai-platform-dvc bucket.
Obtain the team's DVC credentials and lab CA from the platform administrator.
Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION=us-east-1
and AWS_CA_BUNDLE to the trusted CA file. No credentials belong in Git.

Run `dvc push`, then commit source, params.yaml, dvc.yaml, dvc.lock and
reports/metrics.json. Teammates run `dvc pull`. Use `dvc metrics diff`
and `dvc params diff` to review experiments. MinIO is persistent local lab
storage; it must be reachable over your lab connection.

## Register and deploy

Commit and review the model code, then set SOURCE_GIT_SHA to the clean commit,
MODEL_NAME=${{ values.name }}, DATASET_VERSION=mock-tax-transactions-v1,
and MLFLOW_TRACKING_URI=https://mlflow.ai-platform.local. Run:

```bash
python src/train.py --data data/raw/mock-tax-transactions-v1.csv --minimum-macro-f1 0.80
```

Submit model-template.json in a separate platform catalog PR. Once rolled out,
request deployment at https://api.ai-platform.local/portal/ and obtain approval
from another identity. Model development remains in this repository.
