# Architecture reflection review

Date: 2026-09-18

## Method

The review iterated through intended behavior, implementation evidence,
failure and abuse cases, corrective changes, and verification. It covered
API and catalog contracts, identity and tenancy, approval policy, immutable
lineage, GitOps reconciliation, infrastructure provisioning, serving,
observability, supply chain, and operational recovery.

## Decisions and findings

| Area | Assessment | Decision or correction |
|---|---|---|
| Identity | Sound | Keep Keycloak OIDC, short-lived bearer tokens, explicit audience/issuer checks, and role dependencies |
| Separation of duties | Sound | Continue to reject self-approval and record requester, approver, and reason |
| Tenancy | Sound for the local lab | Retain tenant claims, API filtering, and tenant labels; broader namespace-level tenant isolation remains future work |
| Model onboarding | Improved | Use a versioned declarative catalog and generated project instead of Python allowlists or copied services |
| Public catalog API | Corrected | Return user-facing model metadata only; do not expose Kubernetes service accounts or Secret names |
| Environment policy | Corrected | Populate the portal environment selector from the selected catalog model and validate it again in the API and worker |
| Model quality | Corrected | Enforce the catalog minimum macro F1 before rendering a release instead of recording the metric without a gate |
| Immutable lineage | Sound | Require numeric Ready MLflow versions, immutable model and run IDs, source commit, dataset version, and matching artifact URI |
| GitOps | Sound | Generate desired state and let Argo CD reconcile; workers do not apply workload manifests directly |
| Runtime privilege | Sound | Worker pods use non-root, read-only filesystems, dropped capabilities, no mounted Kubernetes token, and scoped agent access |
| Agent boundary | Sound | Keep A2A/MCP tools read-only, authenticated, input constrained, and backed by scoped Argo permissions |
| Catalog packaging | Acceptable with guardrail | The catalog is copied into two image contexts; CI compares both copies to the authoritative file to prevent drift |
| Production | Intentionally gated | Development and staging are supported. Production requires verified promotion, rollback, capacity, and recovery controls |
| Availability | Appropriate for a lab | API and worker replicas exist, but PostgreSQL, Redis, MLflow, MinIO, ingress forwarding, and the KIND cluster are local single-machine dependencies |
| Observability | Partial | Metrics and correlated logs are available. End-to-end CAIPE distributed tracing remains open |
| Secret management | Appropriate for a local lab | Secrets remain out of Git in Kubernetes bootstrap Secrets; an external secret manager is required for a shared or production environment |
| Supply chain | Partial | Base images are pinned and CI tests manifests and code. Signed images, SBOM attestations, and admission verification remain future work |

## Resulting contract

A deployable model must be present in catalog schema 1.0, have an owning team,
use an approved MLflow/KServe runtime and storage identity, declare enabled
environments and a minimum macro F1, and publish a Ready immutable MLflow
version with complete lineage. The portal exposes only safe catalog metadata.
The API and worker independently enforce the catalog. Approval, GitOps,
Crossplane, KServe readiness, and audit evidence remain required.

## Remaining production gates

- Automated promotion and rollback with a tested alternate model version
- Highly available state stores and externally managed persistent storage
- External Secrets or equivalent secret lifecycle management
- Image signing, SBOM/provenance attestations, and admission policy
- Network and namespace isolation appropriate for multiple untrusted tenants
- Load, capacity, disaster recovery, backup, and restore tests
- Complete distributed tracing and alert-to-runbook validation
