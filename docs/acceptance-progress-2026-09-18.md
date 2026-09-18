# Platform acceptance checkpoint - 2026-09-18

This is a progress report. The full project is not yet complete. All commands
below ran against the existing three-node KIND cluster and the real WSL
repository. The Windows clean URL checks used `curl.exe --ssl-no-revoke
--noproxy '*'` and validated the private CA, hostname, and certificate
expiry.

## Verified deployment demonstration

Request `8ccb1a9d-d3e1-4e18-b2a5-051688525f46` was submitted by
`demo-requester` for tenant `tax-ml-team`, model
`tax-document-classifier`, immutable version `1`, environment `dev`.
The API rejected requester self-approval with 403. `demo-approver`
approved the request. The worker resolved the MLflow model, committed
GitOps desired state at `fb4d783a41e9d7dd644f2d1bafae4eb86e1e8305`,
and the root Argo application created
`tax-document-classifier-tax-ml-team-dev-serving`.
That Application is Synced/Healthy; the KServe InferenceService
`ml-platform/tax-document-classifier-tax-ml-team-dev` is Ready.
Synthetic V2 requests to the tenant predictor returned W-2, INVOICE,
and RECEIPT. Argo history records the requested commit. Later platform
commits advanced the Application revision, so the control API correctly
reports `deployed` with current Argo sync/health rather than claiming
that the requested commit is still the current revision. Its audit trail
includes `deployment.execution.deployed`.

From Windows, the authenticated clean URL
`https://api.ai-platform.local/deployments/8ccb1a9d-d3e1-4e18-b2a5-051688525f46`
returned `deployed` and `Synced/Healthy` using a Keycloak token with
tenant `tax-ml-team`. The self-service portal and JavaScript asset
returned 200 at `https://api.ai-platform.local/portal/`; anonymous
`/me` and `/deployments` returned 401.

The first demo attempt uncovered an RQ 2.12 job ID incompatibility.
PR #8 changed IDs to supported characters and bounded dispatch retries.
That initial attempt produced repeated dispatch failure audit records.
The records were retained as evidence; the queued job resumed after the
fix and succeeded.

## Crossplane staging demonstration

Request `bac9633d-8021-42cb-93cb-ea8d5847aeb3` was approved by a
separate user after self-approval returned 403. Worker image `0.3.6`
committed the staging release. The new `ModelWorkspace` selected
`model-workspace-local`; its PVC became Bound and initializer Job
completed. An initial KServe generated hostname exceeded 63 characters;
PR #16 shortened only the serving resource to `-stg` while retaining the
Ready workspace and PVC. The corrected InferenceService is Ready and its
Argo Application is Synced/Healthy. Worker image `0.3.7` then read the
XR through the restricted Argo API, verified the request ID, and
persisted Crossplane `ready=true`, storage `Bound`, and audit event
`deployment.infrastructure.ready`. Platform API image `0.4.3` serves
that status to the portal. PRs #12 through #18 passed CI before merge.

## Requirements and evidence

| Requirement | Status | Git path or resource | Evidence / remaining gap |
|---|---|---|---|
| Kubernetes foundation | Verified | KIND `ai-platform` | Three nodes, workloads ready |
| Argo CD GitOps | Verified | `gitops/argocd/` | Root, API, edge, Argo chart, and demo release Synced/Healthy |
| PKI and seven clean URLs | Verified | `gitops/platform-edge/` | Windows TLS checks; private CA trusted with local revocation limitation |
| Identity, audience, tenant, RBAC | Verified for demo | `services/platform-api/app/security.py`, `scripts/configure_portal_oidc.py` | Two users authenticated; self-approval 403; tenant claim and API audience checked |
| Platform API | Verified for demo | `services/platform-api/` | Create, submit, approve, list, detail, and audit requests returned expected results |
| MLflow registry and immutable model | Verified for demo | `services/deployment-worker/app/model_registry.py` | Worker resolved version 1 and wrote immutable lineage |
| KServe serving and inference | Verified | `gitops/ml-platform/releases/` | Tenant InferenceService Ready; three sample predictions passed |
| Observability and ownership | Partially verified | `observability/`, `platform-monitoring` | Grafana datasources and 25/25 Prometheus targets verified earlier; demo trace-to-audit correlation not yet tested |
| CI | Verified | `.github/workflows/gitops-validate.yaml` | PR #10 worker, API/portal, GitOps checks passed |
| Argo real API integration | Verified | `services/deployment-worker/app/argo_api.py` | Restricted account read deployment app 200, control-plane app 403; live TLS and revision/history checks passed |
| Crossplane request workflow | Verified for staging demo | `services/deployment-worker/app/model_release_writer.py`, `app/argo_api.py`, `gitops/platform-infrastructure/crossplane/` | Request-linked XR Synced/Ready, PVC Bound, Job Complete; restricted Argo resource read 200, status and infrastructure audit persisted |
| Connected portal | Partially verified | `services/platform-api/app/portal/` | Served over trusted URL; Argo and Crossplane fields backed by API; interactive browser sign-in/sign-out not yet verified |
| Approval and audit | Verified for demo | `services/platform-api/app/repository.py` | Separate requester/approver, denial, decision, worker and Argo audit events |
| CAIPE supervisor and A2A | Open | - | Explicit supervisor/task protocol and routing not yet implemented |
| MCP tool surface | Open | - | Narrow Argo REST client exists; MCP wire interface not yet implemented |
| Crossplane in request workflow | Open | - | Sample XR reconciles independently |
| Rollback | Open | - | No authorized rollback workflow or tested rollback yet |
| Security hardening | Partial | NetworkPolicies and scoped Argo token | Broader RBAC, pod, secret, rate-limit, tenant and failure audit pending |
| Repository hygiene | Partial | `.gitignore`, CI secret scan | Final sweep and stale docs cleanup pending |

## Local credential handling

The two demo account passwords are stored outside Git at
`C:\Users\user\Downloads\ai-platform-demo-credentials.txt`. The
restricted Argo API token is in the out-of-band Kubernetes Secret
`ai-platform/argocd-api-observer`. The CA private key remains only in
Kubernetes. No Windows Administrator action is currently required.
