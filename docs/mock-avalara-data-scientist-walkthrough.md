# Mock Avalara data scientist walkthrough

This walkthrough shows how a data scientist develops, uploads, and requests
deployment of a fictional transaction tax-category model. All records are
synthetic. The example does not represent real tax rules and must not be used
for tax or compliance decisions.

## 1. Enter the authoritative repository

Run commands in Ubuntu WSL:

    cd /home/lateef/ai-platform-lab
    git switch main
    git pull --ff-only
    git switch -c model/mock-avalara-tax-category

The example project is services/mock-avalara-tax-code.

## 2. Understand the synthetic dataset

Generate 600 deterministic fictional transactions:

    cd services/mock-avalara-tax-code
    python3 src/generate_data.py \
      --output data/mock-tax-transactions-v1.csv \
      --rows 600

Each row contains:

| Column | Use |
|---|---|
| transaction_id | Fictional row identifier beginning with MOCK |
| item_description | Short synthetic product or service description |
| product_category | Synthetic normalized product category |
| amount | Fictional transaction amount |
| destination_state | Example US state code |
| exemption_certificate | Synthetic true or false feature |
| customer_type | Commercial, government, or nonprofit |
| label | Demonstration target class |

The generator deliberately omits names, email addresses, street addresses,
taxpayer identifiers, payment details, and source-system identifiers.

Inspect the distribution:

    python3 - <<'PY'
    import pandas as pd
    frame = pd.read_csv("data/mock-tax-transactions-v1.csv")
    print(frame.head())
    print(frame["label"].value_counts())
    print(frame.groupby("label")["amount"].describe())
    PY

## 3. Create the development environment

    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
    .venv/bin/pytest -q

The test verifies that data is balanced and synthetic, validates the training
schema, fits the pipeline, and makes predictions.

## 4. Develop the model

The sample pipeline applies:

- TF-IDF to item_description
- one-hot encoding to product, state, exemption, and customer categories
- scaling to amount
- balanced logistic regression

Data scientists can replace this implementation while preserving:

- the input column contract
- deterministic preprocessing
- the three example output labels, or a reviewed catalog contract change
- MLflow lineage tags
- a numeric registered model version
- the configured minimum macro F1
- KServe V2-compatible model packaging

## 5. Train and upload to MLflow

Set immutable lineage and the platform MLflow address:

    export MODEL_NAME=mock-avalara-tax-code
    export DATASET_VERSION=mock-tax-transactions-v1
    export SOURCE_GIT_SHA="$(git rev-parse HEAD)"
    export MLFLOW_TRACKING_URI=https://mlflow.ai-platform.local

Run training:

    .venv/bin/python src/train.py \
      --data data/mock-tax-transactions-v1.csv \
      --minimum-macro-f1 0.80

The job validates the dataset, trains and evaluates the model, rejects a
model below the threshold, logs metrics and a classification report, uploads
the model artifacts, and creates a registered MLflow model version.

Open <https://mlflow.ai-platform.local/> and verify:

1. The experiment is mock-avalara-tax-category.
2. The run contains source.git.commit and dataset.version tags.
3. accuracy and macro_f1 are present.
4. The registered model is mock-avalara-tax-code.
5. The numeric version is Ready.

## 6. Register the application with the platform

After successful MLflow registration, append the object in
model-template.json to the models array in platform/model-catalog.json.
Then run from the repository root:

    python3 scripts/sync_model_catalog.py
    python3 scripts/validate_model_catalog.py
    git diff --check

Commit the model project and catalog update, push the branch, and open a pull
request. CI validates the catalog, API, worker, agents, and GitOps manifests.
A platform maintainer rolls out the catalog-bearing API and worker images.

Do not add the generated CSV to Git. It is reproducible and should remain a
local training artifact or be placed in an approved versioned data store.

## 7. Request deployment

After the catalog rollout:

1. Open <https://api.ai-platform.local/portal/>.
2. Sign in as demo-requester or demo-ml-engineer.
3. Select Mock Avalara tax category classifier.
4. Enter the Ready numeric MLflow version.
5. Select Development.
6. Submit the request.
7. Sign out.
8. Sign in as demo-approver.
9. Review the model, version, environment, owner, and quality evidence.
10. Approve with a meaningful reason.

The worker validates the immutable MLflow model and lineage, then generates
KServe, NetworkPolicy, Crossplane workspace, Kustomize, and Argo CD desired
state. Argo CD reconciles it and CAIPE agents report Argo and Crossplane
status to the portal.

## 8. Validate the deployment

The deployment is accepted only when:

- the portal reports healthy or deployed
- the serving Argo Application is Synced and Healthy
- the request-linked ModelWorkspace is Ready
- the KServe InferenceService is Ready
- a V2 inference request returns one of the reviewed labels
- audit events show different requester and approver identities

Staging follows the same workflow after development acceptance. Production
remains gated in this lab.

## 9. Replace synthetic data safely

Before using organizational data, define an approved data contract, owner,
classification, retention period, permitted purpose, access group, lineage,
quality checks, and deletion process. Remove or tokenize direct identifiers,
keep credentials outside notebooks and Git, and use an approved versioned
data store. A privacy and tax-domain review is required before any real
transaction data or production use.
