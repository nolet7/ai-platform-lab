# Argo CD API observation

The deployment worker publishes an immutable Git commit, then the CAIPE
Argo observer calls the real Argo CD REST API for only the application it
published. It requests a hard refresh and records the current revision, deployment
history, sync state, health state, and application URL in the deployment job
result. A new application may not exist during the first query; that state
is recorded as pending. The dispatcher revisits pending observations every
30 seconds. It records `healthy` when the requested commit is current and
Synced/Healthy, or `deployed` when Argo history proves the commit was
applied but a newer repository commit is current. Argo automated sync
remains responsible for applying the Git commit.

The observer uses HTTPS to the in-cluster Argo CD service. cert-manager
issues `argocd-server-tls` with service DNS names from the local CA. The
worker mounts the public CA certificate and httpx validates the certificate.
The CA private key remains in Kubernetes.

`platform-argocd` adopts the existing Helm release (same chart 10.9.0,
release name, namespace, and resource set). It has no automated sync and
pruning is disabled. Before manual sync, compare its Argo diff with the
live release. The only intended data changes are the public URL, a local
API account, and read-only RBAC for deployment applications. The chart
render comparison against the current Helm values showed 59 resources in
each render, no additions or removals; changes were the three intended
ConfigMaps and config checksum changes on the Argo workloads.

After the chart app is synced, generate an API token for
`caipe-observer` through Argo CD administration and create the
`ai-platform/argocd-api-observer` bootstrap Secret with a single
`ARGO_API_TOKEN` key. Keep that token out of Git. The account has
`applications,get` only in the dev, staging, prod, and ML projects.
The worker's NetworkPolicy permits traffic to the Argo server only.
Until the Secret exists, the worker records Argo observation as pending.

The observer does not mutate Applications, sync them, execute shell
commands, or grant Kubernetes permissions. Its API call is tied to the
published application name and 40-character Git revision. Each worker
result retains the request ID, Git commit, and observed Argo state for
audit correlation.
