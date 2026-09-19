# Model application golden path

This is the supported route for a data scientist or ML engineer to onboard
and deploy a new MLflow model through the AI Platform.

## 1. Scaffold the model project

From the repository root:

    python3 scripts/scaffold_model.py fraud-risk-model \
      --display-name "Fraud risk model" \
      --description "Scores transactions for fraud review" \
      --owner tax-ml-team

The command creates an independent sibling Git/DVC repository fraud-risk-model from the
templates/mlflow-kserve-model directory. The generated project contains the
training contract, DVC pipeline, starter dependencies, model CI, a lineage
contract test, and a catalog entry template. Use --output to choose an external
parent directory; targets inside the platform checkout are rejected.

Install requirements-dev.txt, implement the project training functions,
track your approved input using DVC, configure a project-scoped DVC remote,
and run dvc repro. Commit code, DVC metadata and metrics in the model repo;
push dataset/model artifacts with dvc push. Publish the model repository
with gh repo create OWNER/REPO --private --source . --push after a first
commit. Remote creation is explicit; the scaffold initializes local Git.

## 2. Implement and qualify the model

Implement the generated training functions and add tests for feature schema,
data quality, deterministic preprocessing, model quality, and V2 inference
input/output. Training must record the source Git commit, immutable dataset
version and type, macro_f1, and an MLflow registered model name matching the
Kubernetes DNS-label name.

The registered model version must be numeric and Ready. The platform resolves
it to an immutable MLflow model ID and rejects missing or inconsistent
lineage.

## 3. Register the application

Copy the generated model-template.json (including owner and minimum macro F1) object into
platform/model-catalog.json, then run:

    python3 scripts/sync_model_catalog.py
    python3 scripts/validate_model_catalog.py

Submit model code in the independent model repository. Submit only the catalog
change through a separate platform pull request. Platform CI validates
the catalog and service tests. A platform maintainer builds and rolls out the
new API and worker images. The portal then obtains models from the
authenticated /catalog/models endpoint.

Catalog fields select the MLflow format, KServe runtime, storage identity,
service account, and enabled environments. Development and staging are the
current supported environments. Production remains gated until a verified
promotion and rollback policy is implemented.

## 4. Request deployment

1. Sign in to <https://api.ai-platform.local/portal/> as a data scientist or
   ML engineer.
2. Select the catalog model, numeric immutable version, and environment.
3. Submit the request.
4. A different user with the approver role reviews and approves it.

The worker resolves registry lineage and commits a tenant-scoped
InferenceService, NetworkPolicy, Crossplane ModelWorkspace, Kustomization,
and Argo CD Application. Users do not hand-write Kubernetes YAML.

## 5. Verify serving

The request is complete only when the portal reports healthy or deployed,
the serving Argo Application is Synced/Healthy, the ModelWorkspace is Ready,
and the KServe InferenceService is Ready. Run the model's V2 inference
acceptance test against the generated service before promotion.

Every request retains requester, approver, reason, model version, immutable
model ID, run ID, source commit, dataset version, GitOps commit, observed
Argo/Crossplane state, and correlated logs.

## Ownership boundary

Data scientists and ML engineers own model code, tests, data/model lineage,
and the deployment request. Approvers own the policy decision. Platform
maintainers own catalog review, shared runtimes, identities, Secrets,
network policy defaults, and production promotion policy.
