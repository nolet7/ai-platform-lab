# Enterprise requirements verification matrix

Checkpoint: 2026-09-17. Source: Ubuntu WSL repository /home/lateef/ai-platform-lab and live kind-ai-platform. A running pod is not proof of a complete workflow. PARTIAL includes untested paths. KServe monitoring is GitOps-managed and Prometheus scrape up=1 was verified after an HTTP port regression was repaired.

## Foundation

Evidence key: **R** = infra/kind/cluster.yaml; infra/terraform; automation/ansible/inventory.ini; **L** = WSL tools responded; 3 Ready KIND nodes; Helm releases deployed; **V** = version commands; terraform fmt -check and validate; kubectl get nodes.

| Requirement | Existing implementation | Repository evidence | Runtime evidence | Validation performed | Status | Gap | Action required |
|---|---|---|---|---|---|---|---|
| WSL environment | Yes | R | L | V | COMPLETE | None | None |
| Docker | Yes | R | L | V | COMPLETE | None | None |
| KIND | Yes | R | L | V | COMPLETE | None | None |
| kubectl | Yes | R | L | V | COMPLETE | None | None |
| Helm | Yes | R | L | V | COMPLETE | None | None |
| Terraform | Yes | R | L | V | COMPLETE | None | None |
| Ansible | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |

## Kubernetes

Evidence key: **R** = infra/kind; gitops/platform/namespaces; GitOps PVC and workload manifests; **L** = 3 Ready nodes; env namespaces Active; nginx ingresses; 4 PVCs Bound; **V** = kubectl get nodes,namespaces,ingress,pvc,pv,storageclass.

| Requirement | Existing implementation | Repository evidence | Runtime evidence | Validation performed | Status | Gap | Action required |
|---|---|---|---|---|---|---|---|
| control plane | Yes | R | L | V | COMPLETE | None | None |
| workers | Yes | R | L | V | COMPLETE | None | None |
| namespaces | Yes | R | L | V | COMPLETE | None | None |
| ingress | Yes | R | L | V | COMPLETE | None | None |
| storage | Yes | R | L | V | COMPLETE | None | None |
| resource requests/limits | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |

## Identity / security

Evidence key: **R** = gitops/security/identity; services/platform-api/app/security.py and repository.py; GitOps ServiceAccounts and policies; **L** = Keycloak Running; API Running; dedicated accounts and policies present; **V** = pod, ServiceAccount and NetworkPolicy inventory; source review.

| Requirement | Existing implementation | Repository evidence | Runtime evidence | Validation performed | Status | Gap | Action required |
|---|---|---|---|---|---|---|---|
| Keycloak | Yes | R | L | V | COMPLETE | None | None |
| OIDC | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| JWT validation | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| RBAC | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| roles | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| tenant isolation | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| approval separation of duties | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| Kubernetes ServiceAccounts | Yes | R | L | V | COMPLETE | None | None |
| NetworkPolicies | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| Secrets handling | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |

## Platform control plane

Evidence key: **R** = services/platform-api; services/deployment-worker; gitops/platform/control-api; **L** = API, PostgreSQL, Redis, dispatcher and worker Running; worker emits generic nginx; **V** = source review; kubectl get pods; worker unit tests.

| Requirement | Existing implementation | Repository evidence | Runtime evidence | Validation performed | Status | Gap | Action required |
|---|---|---|---|---|---|---|---|
| FastAPI Platform API | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| PostgreSQL desired state | Yes | R | L | V | COMPLETE | None | None |
| Redis queue | Yes | R | L | V | COMPLETE | None | None |
| deployment dispatcher | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| deployment worker | Incorrect | R | L | V | BROKEN | Wrong workload | Replace with immutable release |
| request validation | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| audit records | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| deployment status | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| approval workflow | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |

## GitOps

Evidence key: **R** = gitops/argocd; gitops/platform/namespaces; gitops/workloads; **L** = 18 Applications Synced Healthy; env namespaces Active; serving app reconciled; **V** = push/Argo revision; kubectl get applications,namespaces.

| Requirement | Existing implementation | Repository evidence | Runtime evidence | Validation performed | Status | Gap | Action required |
|---|---|---|---|---|---|---|---|
| Argo CD root app | Yes | R | L | V | COMPLETE | None | None |
| child applications | Yes | R | L | V | COMPLETE | None | None |
| automated reconciliation | Yes | R | L | V | COMPLETE | None | None |
| self-heal | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| prune where appropriate | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| environment separation | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| Git-driven deployment | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |

## ML platform

Evidence key: **R** = gitops/ml-platform; services/tax-document-classifier/training; scripts/ml-platform/validate-tax-classifier-candidate.py; **L** = MLflow/MinIO/Postgres Running; training Job Completed; version 1 candidate with 7 artifacts; **V** = live candidate validator; MLflow registry and run query; kubectl get pods,pvc.

| Requirement | Existing implementation | Repository evidence | Runtime evidence | Validation performed | Status | Gap | Action required |
|---|---|---|---|---|---|---|---|
| MLflow | Yes | R | L | V | COMPLETE | None | None |
| PostgreSQL backend | Yes | R | L | V | COMPLETE | None | None |
| MinIO artifact store | Yes | R | L | V | COMPLETE | None | None |
| model training | Yes | R | L | V | COMPLETE | None | None |
| experiment tracking | Yes | R | L | V | COMPLETE | None | None |
| model registry | Yes | R | L | V | COMPLETE | None | None |
| model aliases | Yes | R | L | V | COMPLETE | None | None |
| immutable model lineage | Yes | R | L | V | COMPLETE | None | None |
| source Git SHA | Yes | R | L | V | COMPLETE | None | None |
| synthetic dataset documentation | Yes | R | L | V | COMPLETE | None | None |

## Model serving

Evidence key: **R** = gitops/platform-infrastructure; gitops/ml-platform/tax-classifier-serving; scripts/ml-platform/verify-tax-classifier-v2.py; **L** = controller/cert-manager Running; InferenceService Ready; V2 sample predictions pass; serving app Healthy; **V** = kubectl get isvc,apps,networkpolicy; V2 verification.

| Requirement | Existing implementation | Repository evidence | Runtime evidence | Validation performed | Status | Gap | Action required |
|---|---|---|---|---|---|---|---|
| cert-manager | Yes | R | L | V | COMPLETE | None | None |
| KServe | Yes | R | L | V | COMPLETE | None | None |
| Standard mode | Yes | R | L | V | COMPLETE | None | None |
| MLServer | Yes | R | L | V | COMPLETE | None | None |
| immutable MinIO model artifact | Yes | R | L | V | COMPLETE | None | None |
| InferenceService | Yes | R | L | V | COMPLETE | None | None |
| readiness | Yes | R | L | V | COMPLETE | None | None |
| prediction | Yes | R | L | V | COMPLETE | None | None |
| network policy | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| GitOps deployment | Yes | R | L | V | COMPLETE | None | None |

## Model lifecycle

Evidence key: **R** = training/train.py; candidate validator; Platform API approval; generic worker writer; **L** = candidate alias live; no staging/prod model ISVC or rollback; API/worker Running; **V** = MLflow query; source review; kubectl get pods -A.

| Requirement | Existing implementation | Repository evidence | Runtime evidence | Validation performed | Status | Gap | Action required |
|---|---|---|---|---|---|---|---|
| candidate | Yes | R | L | V | COMPLETE | None | None |
| validation | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| approval | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| staging | No | R | L | V | MISSING | Absent | Implement and test |
| production | No | R | L | V | MISSING | Absent | Implement and test |
| immutable promotion | No | R | L | V | MISSING | Absent | Implement and test |
| rollback | No | R | L | V | MISSING | Absent | Implement and test |
| audit trail | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |

## Observability

Evidence key: **R** = observability/phase-2p; observability/kube-prometheus-stack; services/ai-platform-api/k8s/observability; gitops/ml-platform/tax-classifier-serving/podmonitor.yaml and prometheusrule.yaml; **L** = all backends Running; predictor scrape up=1 and four alert rules loaded; **V** = verify-tax-classifier-monitoring.py; V2 inference; kubectl get pods,servicemonitor,prometheusrule,configmap.

| Requirement | Existing implementation | Repository evidence | Runtime evidence | Validation performed | Status | Gap | Action required |
|---|---|---|---|---|---|---|---|
| Prometheus | Yes | R | L | V | COMPLETE | None | None |
| Grafana | Yes | R | L | V | COMPLETE | None | None |
| Alertmanager | Yes | R | L | V | COMPLETE | None | None |
| Loki | Yes | R | L | V | COMPLETE | None | None |
| Tempo | Yes | R | L | V | COMPLETE | None | None |
| Alloy | Yes | R | L | V | COMPLETE | None | None |
| OpenTelemetry | Yes | R | L | V | COMPLETE | None | None |
| application metrics | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| inference metrics | Yes | R | L | V | COMPLETE | None | None |
| model metrics | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| dashboards | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| alerts | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| SLOs | Partial | R | L | V | PARTIAL | Objectives defined; achievement not measured | Add recording and burn-rate evaluation |
| runbooks | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| log correlation | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| trace correlation | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |

## Self-service experience

Evidence key: **R** = Platform API /me, deployment and decision routes; no portal in tracked files; **L** = API and Keycloak Running; no portal deployment/Ingress; **V** = git ls-files; kubectl get deployments,ingress; API source review.

| Requirement | Existing implementation | Repository evidence | Runtime evidence | Validation performed | Status | Gap | Action required |
|---|---|---|---|---|---|---|---|
| user-facing frontend/portal | No | R | L | V | MISSING | Absent | Implement and test |
| Keycloak login | No | R | L | V | MISSING | Absent | Implement and test |
| profile/role display | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| model list | No | R | L | V | MISSING | Absent | Implement and test |
| model version | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| environment | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| deployment request | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| promotion request | No | R | L | V | MISSING | Absent | Implement and test |
| approvals | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| deployment status | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| audit history | No | R | L | V | MISSING | Absent | Implement and test |
| health summary | No | R | L | V | MISSING | Absent | Implement and test |

## Enterprise hardening

Evidence key: **R** = securityContext and Secret refs in GitOps; no policy/CI manifests; **L** = dedicated serving identity; no Kyverno/Gatekeeper or equivalent policy deployment; **V** = webhook/CRD list; Git inventory; manifest and S3 policy review.

| Requirement | Existing implementation | Repository evidence | Runtime evidence | Validation performed | Status | Gap | Action required |
|---|---|---|---|---|---|---|---|
| admission policy | No | R | L | V | MISSING | Absent | Implement and test |
| non-root enforcement | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| no privileged workloads | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| no latest image tags | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| resource requirements | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| image scanning | No | R | L | V | MISSING | Absent | Implement and test |
| dependency scanning | No | R | L | V | MISSING | Absent | Implement and test |
| manifest validation | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| SBOM | No | R | L | V | MISSING | Absent | Implement and test |
| secret protection | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| least privilege | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |

## CI/CD

Evidence key: **R** = Dockerfiles and local tests; no .github/workflows; **L** = images Running; no CI run evidence; **V** = git ls-files; unittest; kustomize and dry-run; terraform checks.

| Requirement | Existing implementation | Repository evidence | Runtime evidence | Validation performed | Status | Gap | Action required |
|---|---|---|---|---|---|---|---|
| Python lint | No | R | L | V | MISSING | Absent | Implement and test |
| tests | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| container build | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| security scan | No | R | L | V | MISSING | Absent | Implement and test |
| Kustomize validation | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| Kubernetes schema validation | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| Terraform fmt/validate | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| GitHub Actions | No | R | L | V | MISSING | Absent | Implement and test |

## Agentic control plane

Evidence key: **R** = no agent service/schema; ai-platform-api has tracing; deployment audit is separate; **L** = no agent deployment or MCP endpoint; **V** = git ls-files; kubectl get deployments -A.

| Requirement | Existing implementation | Repository evidence | Runtime evidence | Validation performed | Status | Gap | Action required |
|---|---|---|---|---|---|---|---|
| CAIPE supervisor | No | R | L | V | MISSING | Absent | Implement and test |
| intent routing | No | R | L | V | MISSING | Absent | Implement and test |
| Argo CD sub-agent | No | R | L | V | MISSING | Absent | Implement and test |
| Kubernetes sub-agent | No | R | L | V | MISSING | Absent | Implement and test |
| MLflow sub-agent | No | R | L | V | MISSING | Absent | Implement and test |
| Observability sub-agent | No | R | L | V | MISSING | Absent | Implement and test |
| GitOps/GitHub sub-agent | No | R | L | V | MISSING | Absent | Implement and test |
| Security sub-agent | No | R | L | V | MISSING | Absent | Implement and test |
| Crossplane sub-agent | No | R | L | V | MISSING | Absent | Implement and test |
| explicit A2A message schema | No | R | L | V | MISSING | Absent | Implement and test |
| MCP tool surfaces | No | R | L | V | MISSING | Absent | Implement and test |
| correlation IDs | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| authorization propagation | No | R | L | V | MISSING | Absent | Implement and test |
| approval gates | No | R | L | V | MISSING | Absent | Implement and test |
| audit logs | No | R | L | V | MISSING | Absent | Implement and test |

## Crossplane

Evidence key: **R** = no Crossplane manifests/Argo application; **L** = no Crossplane pods or CRDs; **V** = git ls-files; kubectl get pods,crd,applications.

| Requirement | Existing implementation | Repository evidence | Runtime evidence | Validation performed | Status | Gap | Action required |
|---|---|---|---|---|---|---|---|
| Crossplane installed | No | R | L | V | MISSING | Absent | Implement and test |
| provider | No | R | L | V | MISSING | Absent | Implement and test |
| Claim | No | R | L | V | MISSING | Absent | Implement and test |
| Composition | No | R | L | V | MISSING | Absent | Implement and test |
| managed resource | No | R | L | V | MISSING | Absent | Implement and test |
| status propagation | No | R | L | V | MISSING | Absent | Implement and test |
| GitOps ownership | No | R | L | V | MISSING | Absent | Implement and test |

## Final demonstration

Evidence key: **R** = Keycloak scripts, training, API, serving V2 script; no end-to-end demo; **L** = training and serving live; no full approval-to-model release or agent flow; **V** = MLflow validator; V2 inference; Argo and pod inventory.

| Requirement | Existing implementation | Repository evidence | Runtime evidence | Validation performed | Status | Gap | Action required |
|---|---|---|---|---|---|---|---|
| login | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| train/register model | Yes | R | L | V | COMPLETE | None | None |
| candidate alias | Yes | R | L | V | COMPLETE | None | None |
| deployment request | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| approval | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| GitOps change | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| Argo sync | Yes | R | L | V | COMPLETE | None | None |
| KServe Ready | Yes | R | L | V | COMPLETE | None | None |
| prediction | Yes | R | L | V | COMPLETE | None | None |
| metrics/logs/traces | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| audit event | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| rollback | No | R | L | V | MISSING | Absent | Implement and test |
| agent status interaction | No | R | L | V | MISSING | Absent | Implement and test |

## Failure tests

Evidence key: **R** = JWT/RBAC/approval code; candidate validator; no failure suite; **L** = missing alias rejected; other failure flows not observed; **V** = source review; live negative alias test; runtime inventory.

| Requirement | Existing implementation | Repository evidence | Runtime evidence | Validation performed | Status | Gap | Action required |
|---|---|---|---|---|---|---|---|
| invalid token | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| unauthorized role | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| missing approval | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| invalid model reference | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| serving readiness failure | No | R | L | V | MISSING | Absent | Implement and test |
| network policy block | No | R | L | V | MISSING | Absent | Implement and test |
| rollback | No | R | L | V | MISSING | Absent | Implement and test |

## Documentation

Evidence key: **R** = docs/platform-audit.md; docs/model-promotion.md; docs/kserve-serving.md; Keycloak README; **L** = core platform and KServe live; full workflow absent; **V** = git ls-files; document review; live serving check.

| Requirement | Existing implementation | Repository evidence | Runtime evidence | Validation performed | Status | Gap | Action required |
|---|---|---|---|---|---|---|---|
| architecture | No | R | L | V | MISSING | Absent | Implement and test |
| platform overview | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| deployment workflow | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| MLflow lifecycle | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| KServe serving | Yes | R | L | V | COMPLETE | None | None |
| security | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| GitOps | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| observability | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| agent architecture | No | R | L | V | MISSING | Absent | Implement and test |
| A2A | No | R | L | V | MISSING | Absent | Implement and test |
| MCP | No | R | L | V | MISSING | Absent | Implement and test |
| Crossplane | No | R | L | V | MISSING | Absent | Implement and test |
| operations runbook | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| incident runbook | Partial | R | L | V | PARTIAL | Serving alerts covered only | Add control-plane and storage incidents |
| troubleshooting | Partial | R | L | V | PARTIAL | Incomplete | Finish and test |
| final demo | No | R | L | V | MISSING | Absent | Implement and test |
| interview walkthrough | No | R | L | V | MISSING | Absent | Implement and test |

## Next smallest safe unit

The inference metrics and alert unit is complete: PodMonitor target up=1, four alert rules loaded, KServe V2 health and three predictions pass. The worker now reaches MLflow through a scoped GitOps NetworkPolicy; a live version 1 lookup returned READY. Next, replace the worker generic nginx output with an approval-bound immutable staging model release, then implement production promotion and rollback.
