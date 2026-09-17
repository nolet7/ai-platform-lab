# Platform audit - 2026-09-17

Source of truth: `/home/lateef/ai-platform-lab` in Ubuntu WSL.
Kubernetes context: `kind-ai-platform`; KIND cluster: `ai-platform`.

## Verified baseline

- Three Kubernetes v1.37.0 nodes are Ready (one control plane, two workers).
- Seventeen Argo CD Applications were Synced and Healthy at audit start.
- Keycloak, PostgreSQL, Redis, Platform API, MLflow, MinIO, cert-manager,
  KServe controller, Prometheus, Grafana, Alertmanager, Loki, Tempo, Alloy,
  and OTel Collector pods were running.
- MLflow alias `tax-document-classifier@candidate` resolves to version 1,
  run `c7f6f3a7fb36426385ca9e0ec6949eb3`, and immutable model ID
  `m-021e2255280449de897f0b2981283d79`.
- The model artifact prefix in MinIO contains seven objects, including
  `MLmodel` and `model.pkl`. The training data is synthetic demo data.
- The stock KServe MLServer 1.5 image contains MLflow 2.10.2 and
  scikit-learn 1.4.1.post1. Its inference failed with HTTP 500. A namespace
  runtime using MLServer 1.7.1 and the model's pinned dependencies passed
  V2 health and W-2, invoice, and receipt inference on 2026-09-17.
- Metrics API is unavailable; `kubectl top` and KServe HPA CPU metrics fail.
  WSL had 54 GiB available memory at the resource check.
- No InferenceService existed before Phase 5C-3 work began.

## Gaps and risks

1. Phase 5C-3 passed a temporary live test. Its GitOps application still
   needs a push and Argo CD reconciliation before the phase is complete.
2. KServe ingress config had `disableIstioVirtualHost=false` despite an
   ingress-nginx setup without Istio. The local fix is commit `d597d34`;
   GitHub authentication blocked its push.
3. The KServe storage initializer requires bucket-level `ListBucket` for
   `HeadBucket`. The user approved listing the `mlflow-artifacts` bucket;
   object reads remain restricted to the resolved immutable model prefix.
4. The stock MLServer package mismatch was repaired with a namespace-scoped
   runtime. The local image must be published or loaded after cluster rebuild.
5. Metrics Server is absent, so HPA cannot compute CPU utilization.
6. The initial worktree contained an untracked `scripts/` directory. Preserve
   and review those files before staging. Local `.env` and Terraform state
   files exist; they are not tracked by Git and must not be committed.
7. GitHub push currently lacks usable Ubuntu WSL credentials. Argo CD cannot
   reconcile local commits until that is fixed.

## Completion sequence

1. Finish Phase 5C-3: commit and push GitOps state, then verify Argo CD Synced
   and Healthy with the live V2 test.
2. Implement immutable candidate validation, approval, staging and production
   promotion, and rollback with recorded lineage.
3. Extend existing Prometheus/Grafana/OTel/Loki/Tempo coverage with platform,
   inference and model metrics, SLOs, alerts and runbooks.
4. Build a lightweight OIDC-backed self-service portal on the Platform API.
5. Add admission policy, namespace and workload guardrails without weakening
   existing RBAC or NetworkPolicies.
6. Expand CI checks for Python, manifests, Terraform, dependencies, images
   and SBOMs.
7. Add the supervisor, specialized agents, explicit A2A wire schema and
   permissioned MCP tools against actual platform APIs.
8. Demonstrate Crossplane with local resources if capacity permits.
9. Integrate the UI and agents, complete end-to-end and failure demos, and
   produce architecture, operations and interview documentation.
10. Run final verification and report only results observed in the cluster.
