# Request an ML project in Backstage

## Data scientist workflow

1. Open https://backstage.127.0.0.1.nip.io/create and sign in with Keycloak.
   Use the existing demo-requester or demo-ml-engineer account. The existing
   demo credentials file is in the Windows Downloads folder.
2. Choose **Create an ML project**. Enter a unique repository/model name,
   a project title and purpose. Review the request and click **Create**.
3. Backstage creates a private repository under nolet7 and registers its
   Component in the catalog. The task output links to both results.
4. Clone that repository, install requirements-dev.txt in a virtual environment,
   run `dvc repro`, `pytest -q`, and `dvc metrics show`.
5. Obtain the team's MinIO access from the platform administrator. Run
   `dvc push` and commit model source, tests, DVC metadata and metrics in the
   new repository. Open model development PRs there.
6. Register a qualified numeric MLflow version with source/DVC/data lineage.
   Submit the model-template.json catalog entry in a separate platform PR.
   After its rollout, request deployment in the existing deployment portal.

A duplicate GitHub repository name fails without modifying the existing repo.
If publication succeeds but catalog registration fails, retain the repository
link from the task log and have a platform maintainer register its catalog-info.yaml.
Do not blindly resubmit the same create request.

## MinIO DVC storage

The DVC remote uses `s3://ai-platform-dvc/tax-ml-team/PROJECT_NAME`, with
endpoint `https://minio.127.0.0.1.nip.io`. The bucket has versioning enabled.
The dedicated dvc-tax-ml-team account can access this team's project objects;
it cannot access MLflow artifacts or other teams' objects. The account is
shared within the lab ML team; it is not per-project credential isolation.

Keep AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY outside Git. Set
AWS_DEFAULT_REGION=us-east-1 and AWS_CA_BUNDLE to the platform CA certificate.
The lab administrator's WSL credentials are in ~/.config/ai-platform/dvc.env
(mode 0600), and the CA is in ~/.config/ai-platform/ca.crt.

WSL users whose Windows HTTPS forwarding is not reachable can run
`kubectl -n ml-platform port-forward svc/minio 19000:9000` and set
`dvc remote modify --local minio endpointurl http://127.0.0.1:19000`.
Load the environment securely with `set -a; source ~/.config/ai-platform/dvc.env; set +a`.
This override stays in .dvc/config.local. Do not disable TLS verification.

MinIO, Backstage and the generated model repos have separate responsibilities:
GitHub stores source and DVC pointers; MinIO stores dataset/model blobs; MLflow
stores experiment/registered-model metadata; Backstage provisions repositories;
the control API governs model deployment. Creating a repo does not deploy a model.

## Platform operator setup

The Backstage app is in services/backstage. The canonical model template is
in templates/mlflow-kserve-model. Run scripts/sync_backstage_template.py
following template edits. It produces the Backstage fetch:template skeleton.

Use the existing MinIO and Keycloak port-forwards on 19000 and 19084, then run:

```bash
python3 scripts/bootstrap_dvc_minio.py
python3 scripts/bootstrap_backstage.py
```

The scripts use the existing lab administrator's Kubernetes/GitHub access and
store runtime secrets outside Git. Backstage uses a server-side GitHub token;
users cannot choose another owner or public visibility. The token is a lab
integration; a shared deployment should use a scoped GitHub App installation.
Repository access for actual GitHub collaborators is managed by the owner;
Keycloak demo identities do not automatically grant GitHub account access.

Build with Node 22 and the committed Yarn release:

```bash
cd services/backstage
node .yarn/releases/yarn-4.13.0.cjs install --immutable
node .yarn/releases/yarn-4.13.0.cjs tsc
node .yarn/releases/yarn-4.13.0.cjs build:backend
docker build -f packages/backend/Dockerfile -t ai-platform-backstage:0.1.2 .
kind load docker-image ai-platform-backstage:0.1.2 --name ai-platform
```

Deploy gitops/platform/backstage and the MinIO edge ingress. Runtime Secrets
and CA ConfigMap are bootstrapped first. PostgreSQL persists catalog/tasks.
The Backstage pod's Keycloak host alias uses the local ingress service IP;
update it when rebuilding the cluster. The nip.io names resolve to loopback
and use the lab CA, avoiding administrator changes to Windows hosts.

Only cataloged Keycloak identities can sign in. ML team members can submit
requests. Template/identity registration, deletion and template dry-run management are
restricted to platform maintainers. ML team members can register Component locations; dynamic locations cannot register
Template, User or Group entities. Permission tests cover these gates.
