# ${{ values.name }}

${{ values.description }}

This is a runnable demonstration AI service with a synthetic training pipeline,
FastAPI inference API, Docker image, CI, DVC/MinIO data versioning and MLflow support.
Replace the fictional classifier with your own model; its labels are not tax advice.

## Review and develop

Accept the repository invitation. Review the initial PR and obtain approval from
@${{ values.reviewer }}. Required `application-ci` must pass. Direct pushes to main,
stale approvals and self-approval of the latest push do not satisfy the gate.
Only the minimal repository governance was bootstrapped directly on main.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest -q
dvc repro
uvicorn app.main:app --port 8000
```

POST /predict accepts item_description, product_category, amount, destination_state, exemption_certificate and customer_type. The Docker
build trains its synthetic demonstration model and includes the trusted artifact.
For a real project, replace that build stage with a verified versioned artifact.

DVC remote: MinIO `ai-platform-dvc/${{ values.team }}/${{ values.name }}`. Obtain
team-scoped credentials and the platform CA out of band; never commit credentials.
The existing lab provisions tax-ml-team. Provision a separate scoped bucket prefix
and credentials before a developers-owned project uses DVC. Run `dvc push` and
commit the resulting lock file from a feature branch; a fresh clone uses `dvc pull`.

## Release and deployment

After review and merge, CI publishes a private GHCR image tagged by commit SHA and
prints its immutable digest. Open a PR in
https://github.com/${{ values.githubOwner }}/${{ values.name }}-gitops to replace
`REPLACE_WITH_REVIEWED_DIGEST` with that digest. CI validates the manifests and a
reviewer approves the deployment change. Platform onboarding is a separate reviewed
PR; Argo CD then reconciles only the deployment repository's main branch.
No credentials or automatic deployment access are granted to pull-request CI.
