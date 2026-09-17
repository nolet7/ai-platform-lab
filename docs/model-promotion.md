# Tax classifier model lifecycle

## Candidate validation

Run in Ubuntu WSL from the repository:

```bash
python3 scripts/ml-platform/validate-tax-classifier-candidate.py
```

The command resolves the live MLflow `candidate` alias, then checks that the
registered version is READY, its source identifies an immutable logged model,
and the logged model and registered version point to the same run. It verifies
the source Git commit, dataset version, macro F1, and the immutable MinIO
artifact prefix, including `MLmodel`. It prints an evidence record with the
model ID and S3 URI. A missing alias, inconsistent lineage, inadequate metric,
or incomplete artifact prefix fails closed.

The current dataset is `synthetic-demo-v1`; its measured macro F1 of 1.0 is
a demonstration check, not evidence of production model quality. This command
does not approve a deployment or change a production alias. Staging and
production promotion still require the Platform API approval workflow,
immutable GitOps manifests, post-deploy health checks, and rollback records.

The serving baseline uses the immutable model ID recorded in
`gitops/ml-platform/tax-classifier-serving/inferenceservice.yaml`.
Run `scripts/ml-platform/verify-tax-classifier-v2.py` after any serving
change to verify V2 readiness and sample predictions.

## Worker registry connectivity

The deployment worker has a scoped NetworkPolicy egress rule to the MLflow
pod on TCP 5000 and receives the in-cluster tracking URI from its ConfigMap.
On 2026-09-17 a live lookup of registered model version 1 from the worker
returned READY. This is a prerequisite for immutable release resolution; the
worker still renders a generic Deployment and does not yet promote a model.

## Immutable version resolver

The worker source now includes `app/model_registry.py`. It accepts a
positive numeric MLflow model version, checks the READY registry record,
immutable logged model ID, download URI, run ID, source Git SHA, dataset
lineage, and macro F1, then returns a pinned S3 URI. Unit tests reject aliases,
unsafe versions, artifact mismatches, and lineage mismatches. A live version 1
lookup returned the same immutable URI as the candidate validator on
2026-09-17. The resolver is not yet wired into the worker publishing path;
approved jobs still render a generic Deployment.
