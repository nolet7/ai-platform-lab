# Platform acceptance checkpoint - 2026-09-18

## Data scientist and ML engineer golden path

PR #26 aligned the portal and API with the deployment worker's supported
contract. The UI and API now accept only the registered
`tax-document-classifier`, positive integer model versions, valid tenant
labels, and the currently supported development and staging environments.
The portal hides the request form from identities without a data scientist,
ML engineer, or platform administrator role. A dedicated
`demo-ml-engineer` identity was added alongside the data scientist and
independent approver identities.

After CI passed, two live deployments exercised the complete path:

| Requester role | Request | Environment | Result |
|---|---|---|---|
| Data scientist (`demo-requester`) | `48cf0c07-99ee-42db-9cbd-8a2ed975864f` | Development | Execution healthy; Argo Synced/Healthy; Crossplane Ready |
| ML engineer (`demo-ml-engineer`) | `bc227b98-3b8c-457e-9922-f84a77ed2c55` | Staging | Execution healthy; Argo Synced/Healthy; Crossplane Ready |

Both requests used immutable model version `1` and were approved by the
separate `demo-approver` identity. The resulting development and staging
KServe InferenceServices reported Ready, both request-linked
`ModelWorkspace` resources reported Synced and Ready, and both serving
Argo Applications reported Synced and Healthy. Portal/API tests verify that
both requester roles may create requests and that unsupported production,
model, version, and tenant inputs are rejected before dispatch.

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

## CAIPE A2A/MCP staging demonstration

PRs #20 and #21 passed CAIPE, worker, API/portal and GitOps CI. The live
agents use A2A v1 JSON-RPC and MCP Streamable HTTP tools backed by the real
restricted Argo CD API. Worker and dispatcher images `0.3.8` use the CAIPE
supervisor; API image `0.4.4` renders the result. The worker and dispatcher
no longer hold the Argo API token or CA bundle.

Request `5e6ed6ca-8af0-4cd1-9398-ac1ab49daf8a` passed separate-identity
approval after requester self-approval returned 403. The worker committed
`8e3200a6060d6aa74255e1b014be6dd12090d008`; the first A2A Argo result
found that revision in history while sync was settling. The dispatcher later
reported `healthy` and "Argo CD and Crossplane are ready". The serving
Application is Synced/Healthy and both agent logs recorded completed tasks
with that request ID as correlation ID. See `docs/caipe-architecture.md` for
the protocol, authorization and recovery path.
Loki returned API and agent logs for that request ID; Tempo returned no
CAIPE trace from the search checked. Distributed trace correlation remains
open.

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
| Observability and ownership | Partially verified | `observability/`, `platform-monitoring`, `docs/caipe-architecture.md` | Grafana datasources and 25/25 Prometheus targets verified earlier; Loki returned API, A2A and MCP logs for the same request ID; CAIPE distributed traces remain unverified |
| CI | Verified | `.github/workflows/gitops-validate.yaml` | PR #10 worker, API/portal, GitOps checks passed |
| Argo real API integration | Verified | `services/caipe-agent/app/argo_rest.py` | Agent's restricted account read deployment app; control-plane app denied; live TLS and revision/history checks passed |
| Crossplane request workflow | Verified for staging demo | `services/deployment-worker/app/model_release_writer.py`, `services/caipe-agent/app/argo_rest.py`, `gitops/platform-infrastructure/crossplane/` | Request-linked XR Synced/Ready, PVC Bound, Job Complete; agent status and infrastructure audit persisted |
| Connected portal | Partially verified | `services/platform-api/app/portal/` | Served over trusted URL; Argo and Crossplane fields backed by API; interactive browser sign-in/sign-out not yet verified |
| Approval and audit | Verified for demo | `services/platform-api/app/repository.py` | Separate requester/approver, denial, decision, worker and Argo audit events |
| CAIPE supervisor and A2A | Verified for staging demo | `services/deployment-worker/app/supervisor.py`, `services/caipe-agent/` | Both purpose-specific agents completed request-correlated A2A tasks; dispatcher produced healthy result |
| MCP tool surface | Verified for staging demo | `services/caipe-agent/app/main.py` | Authenticated, scoped Argo and Crossplane MCP tools exercised through A2A; anonymous A2A returned 401 |
| Crossplane in request workflow | Verified for staging demo | `services/deployment-worker/app/model_release_writer.py` | Request-linked XR and storage reconciled, status propagated through the agent |
| Rollback | Partial | `docs/caipe-architecture.md` | Approved immutable-version redeployment is described; no alternate version or automated rollback exercised |
| Security hardening | Partial | NetworkPolicies and scoped Argo token | Broader RBAC, pod, secret, rate-limit, tenant and failure audit pending |
| Repository hygiene | Partial | `.gitignore`, CI secret scan | Final sweep and stale docs cleanup pending |

## Local credential handling

The two demo account passwords are stored outside Git at
`C:\Users\user\Downloads\ai-platform-demo-credentials.txt`. The
restricted Argo API token is in the out-of-band Kubernetes Secret
`ai-platform/argocd-api-observer`. The CA private key remains only in
Kubernetes. No Windows Administrator action is currently required.
