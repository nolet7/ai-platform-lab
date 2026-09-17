# Tax classifier serving

The tax classifier uses MLflow Registry as its source of truth. Run
`scripts/ml-platform/resolve-tax-classifier-model.sh` in Ubuntu WSL to resolve
`tax-document-classifier@candidate` to an immutable logged-model ID. The
resolver checks the MinIO prefix for `MLmodel` and other objects, and prints
the exact S3 URI and lineage without exposing credentials.

The InferenceService pins the immutable URI and model ID. Promotion must first
resolve the approved model, validate it, then update the URI and labels in Git.
A mutable alias must never appear in `storageUri`.

## Credential bootstrap

KServe reads `tax-classifier-s3` through the `tax-classifier-serving`
ServiceAccount. The Secret is runtime credential state and is excluded from
Git. Run `python3 scripts/ml-platform/bootstrap-tax-classifier-s3.py` after
MinIO and MLflow are healthy. It creates a dedicated MinIO identity, verifies
read access to `MLmodel`, and writes the Kubernetes Secret without printing
credentials. It uses reserved localhost port 19000 only during bootstrap and
checks availability first.

KServe's storage initializer calls S3 `HeadBucket`, which needs `ListBucket`
on the artifact bucket. The serving identity can list object names in
`mlflow-artifacts`; `GetObject` is limited to the resolved immutable model
prefix. The user approved this scope on 2026-09-17. Re-running bootstrap
updates the policy for the current alias while preserving the Secret keys.
A production deployment should use a dedicated serving bucket or a storage
initializer that can operate with prefix-scoped listing.

## Compatible serving image

The stock KServe MLServer 1.5 runtime includes MLflow 2.10.2 and
scikit-learn 1.4.1.post1. It loaded the MLflow 3.16/scikit-learn 1.7.2
artifact but returned HTTP 500 on inference due to an incompatible TF-IDF
transformer. The namespace-scoped `kserve-mlserver` ServingRuntime overrides
the stock cluster runtime for this workload only. Its image pins Python 3.11,
MLflow 3.16, scikit-learn 1.7.2, MLServer 1.7.1, and uvloop 0.21.0.

Build and load the image into the existing KIND workers with
`scripts/ml-platform/load-tax-classifier-serving-image.sh`. This uses KIND's
single-platform image archive workaround for Docker's containerd image store.
A production deployment should publish and pin an image digest in a registry.

## Validation

1. Run the resolver and confirm `MODEL_OBJECT_COUNT` is greater than one.
2. Run the credential bootstrap and image load script.
3. Validate `kubectl apply --server-side --dry-run=server -k gitops/ml-platform/tax-classifier-serving`.
4. Commit and push the reviewed manifests; Argo CD then owns the resources.
5. Confirm the Argo application is Synced and Healthy and the InferenceService
   reports Ready True.
6. Run `python3 scripts/ml-platform/verify-tax-classifier-v2.py`. It checks
   both V2 readiness endpoints and synthetic W-2, invoice, and receipt
   predictions on reserved localhost port 18082.
7. Inspect predictor and storage initializer logs. MLServer metrics are on
   port 8082. Prometheus scraping should be verified separately.

The live temporary test on 2026-09-17 passed all three predictions. Argo CD
reconciliation still requires the repository changes to reach GitHub.
