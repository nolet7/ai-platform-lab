# Platform acceptance checkpoint — 2026-09-17

Historical checkpoint. Superseded by [the 2026-09-18 report](acceptance-progress-2026-09-18.md). This is a progress record, not a declaration that the project is complete. Evidence was collected from the Windows host and the existing Ubuntu WSL KIND cluster. PR #1 remains a draft.

## Ownership and health

| Component | Git path | Live resource | Evidence | Status |
|---|---|---|---|---|
| Local CA | `gitops/platform-infrastructure/pki/` | `ClusterIssuer/ai-platform-ca` | `kubectl get clusterissuer ai-platform-ca`: Ready=True | Verified |
| API certificate | `gitops/platform-edge/api.yaml` | `ai-platform/Certificate/ai-platform-api-tls` | Ready=True; Windows curl TLS verify result 0 | Verified |
| Edge routes | `gitops/platform-edge/` | `argocd/Application/platform-edge` | Synced/Healthy from feature branch | Verified on branch |
| Monitoring | `gitops/argocd/applications/platform-monitoring.yaml` and `observability/kube-prometheus-stack/values.yaml` | `argocd/Application/platform-monitoring` | Same Helm release name, namespace, and chart version 90.0.0; no-prune sync Synced/Healthy | Verified on branch |
| Keycloak proxy | `gitops/security/identity/keycloak/deployment.yaml` | `security/Deployment/keycloak` | Feature revision rolled out; OIDC issuer returned `https://keycloak.ai-platform.local/realms/ai-platform`; root app then restored `main` | Validated temporarily |
| MLflow external host | `gitops/ml-platform/mlflow/deployment.yaml` | `ml-platform/Deployment/mlflow` | Feature revision rolled out; UI 200 and registered model `tax-document-classifier` returned; root app then restored `main` | Validated temporarily |
| GitOps CI | `.github/workflows/gitops-validate.yaml` | PR #1 check | Kustomize render, whitespace, PEM key check, YAML and inline Secret payload scan | Latest check passed at checkpoint |

The monitoring chart was rendered with the same release name, namespace, chart version, and Git values as the live Helm release. Excluding Helm hooks, the rendered manifest differed from the release manifest only by Grafana public URL variables and the Prometheus external URL. A Kubernetes dry-run diff against live resources showed only Grafana environment variable ordering. Argo then synced the existing resources without pruning. The old Helm release record still exists; routine changes should go through Argo after PR merge, and direct `helm upgrade` must be retired to avoid competing writers.

## Windows HTTPS checks

All requests used `curl.exe --ssl-no-revoke --noproxy '*'`; the three names missing from the Windows hosts file also used `--resolve name:443:127.0.0.1`. TLS verification result was 0 for every request.

| URL/path | Result |
|---|---|
| `https://api.ai-platform.local/health/ready` | 200 |
| `https://argocd.ai-platform.local/` | 200 |
| `https://keycloak.ai-platform.local/realms/ai-platform/.well-known/openid-configuration` | 200 |
| `https://mlflow.ai-platform.local/health` | 200 |
| `https://grafana.ai-platform.local/login` | 200 |
| `https://prometheus.ai-platform.local/-/ready` | 200 |
| `https://tax-classifier.ai-platform.local/v2/health/ready` | 200 |
| `https://tax-classifier.ai-platform.local/v2/models/tax-document-classifier/infer` | W-2 prediction returned for W-2 sample |

`--ssl-no-revoke` is needed because this isolated private CA does not publish a revocation endpoint. It retains trust-chain, signature, hostname, and expiry checks. Do not use `-k` as the normal acceptance test.

## Remaining gates

1. Run `C:\Users\user\Downloads\ai-platform-admin.ps1` from Windows PowerShell as Administrator. It adds missing hosts entries for Grafana, Prometheus, and tax-classifier. Codex did not execute the script.
2. Verify the seven hostnames resolve to 127.0.0.1 without `--resolve`.
3. Wait for the latest PR CI run, then merge PR #1 only after the clean URL and live reconciliation gates pass. The feature-branch edge and monitoring Applications currently use the feature revision for validation; root GitOps points to `main`.
4. Revalidate Keycloak, MLflow, API, Argo, monitoring, and inference after `main` reconciliation.
5. Verify authenticated API paths, Argo API listing, Grafana datasource health, Prometheus targets, and worker registry connectivity. Basic HTTP checks are not substitutes.
6. Continue the broader control-plane scope: CAIPE supervisor and purpose-specific agents, A2A schema, scoped MCP tools backed by the real Argo API, Crossplane local composition, connected self-service frontend, policy and audit workflow, rollback, security review, and end-to-end demonstration.

No CA private key was copied into Git. The local API certificate's former OpenSSL creation script now exits with a cert-manager instruction. Accidental zero-byte shell artifacts were removed from version control.