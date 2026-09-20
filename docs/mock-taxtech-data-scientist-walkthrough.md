# Mock TaxTech: independent model development with DVC

Create the fictional example repository `mock-taxtech-tax-model` through
Backstage before using the clone commands below. Existing repositories and
persisted MLflow/DVC resources must be migrated separately if reusing old data.
Data scientists and ML engineers commit model work there. The platform owns
shared templates, policy, catalog and deployment orchestration. It does not
host each team's source tree. These synthetic labels are not actual tax rules.

## 1. Clone and prepare

```bash
git clone https://github.com/nolet7/mock-taxtech-tax-model.git
cd mock-taxtech-tax-model
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
git switch -c model/improve-features
```

## 2. Generate and qualify

```bash
dvc repro
pytest -q
dvc metrics show
```

`params.yaml` controls 600 rows, the seed and the minimum macro F1.
`dvc.yaml` generates data/raw/mock-tax-transactions-v1.csv, evaluates a
TF-IDF + one-hot + scaled amount logistic regression, and caches the dataset
and models/model.joblib. dvc.lock records hashes of inputs and outputs.
reports/metrics.json is small and committed for review.

The data scientist uses the CSV for exploration, feature engineering,
training and held-out evaluation. It contains transaction_id,
item_description, product_category, amount, destination_state,
exemption_certificate, customer_type and label. No customer identities are
included. The three demonstration classes are TAXABLE_TANGIBLE,
TAXABLE_SAAS and EXEMPT_PROFESSIONAL_SERVICE. Their deliberately simple
patterns yield perfect scores; this demonstrates plumbing, not real-world
accuracy. Use independent and time-aware evaluation for a real model.

```bash
python -c 'import pandas as pd; d=pd.read_csv("data/raw/mock-tax-transactions-v1.csv"); print(d.head()); print(d.label.value_counts())'
```

## 3. Use MinIO DVC storage

The default remote is s3://ai-platform-dvc/tax-ml-team/mock-taxtech-tax-model
at https://minio.127.0.0.1.nip.io. Obtain the team-scoped MinIO credentials and
CA certificate from the platform administrator. Set AWS_ACCESS_KEY_ID,
AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION=us-east-1 and AWS_CA_BUNDLE.
Run `dvc push` to share artifacts and `dvc pull` from another checkout.
Never commit credentials or .dvc/config.local.

For WSL without access to the Windows HTTPS forward, run a MinIO port-forward
on 19000 and `dvc remote modify --local minio endpointurl http://127.0.0.1:19000`.
Verify MinIO push and fresh-clone recovery for the new project prefix.

New projects can be requested at https://backstage.127.0.0.1.nip.io/create.

## 4. Commit model changes in the model repository

```bash
git add src tests params.yaml dvc.yaml dvc.lock reports/metrics.json .dvc/config
git commit -m "Qualify transaction classifier"
git push -u origin model/improve-features
```

Review code, metrics and data hashes in the model PR. Datasets and model
binaries stay in DVC storage. For a changed experiment, run dvc repro,
review dvc metrics diff and dvc params diff, then dvc push before sharing.

## 5. Register a qualified version in MLflow

From a clean, committed model checkout with the qualified DVC outputs:

```bash
export MODEL_NAME=mock-taxtech-tax-code
export DATASET_VERSION=mock-tax-transactions-v1
export SOURCE_GIT_SHA="$(git rev-parse HEAD)"
export MLFLOW_TRACKING_URI=https://mlflow.ai-platform.local
python src/train.py --data data/raw/mock-tax-transactions-v1.csv --minimum-macro-f1 0.80
```

This records the independent source repository/commit, dataset SHA256,
dataset version, DVC lock hash, metrics, dvc.lock and params.yaml in MLflow.
Record the new numeric version from the output. Register and qualify the
TaxTech model before deploying it; previous registry names are not aliases.

## 6. Register with the platform

In a separate platform checkout/PR, add the object in model-template.json
to platform/model-catalog.json. Run scripts/sync_model_catalog.py and
scripts/validate_model_catalog.py. The platform maintainer rolls out the
catalog-bearing API and worker images. Do not copy model source into the
platform repository. The sample catalog name is mock-taxtech-tax-code. Ensure model-template.json
uses this same name if the repository template default differs.

## 7. Request and verify deployment

Open https://api.ai-platform.local/portal/, sign in as demo-ml-engineer,
select the model, a Ready numeric MLflow version and Development, and submit.
A different demo-approver identity reviews and approves. The worker checks
quality/lineage and writes GitOps resources. Require Argo Synced/Healthy,
ModelWorkspace Ready and KServe InferenceService Ready, then run a V2
prediction acceptance test before promotion. New repository requests are provided by Backstage at
https://backstage.127.0.0.1.nip.io/create; the deployment portal separately
governs model deployment requests.
