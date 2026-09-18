# Local deployment demo

Open `https://api.ai-platform.local/portal/` in a browser and sign in
with the demo accounts in
`C:\Users\user\Downloads\ai-platform-demo-credentials.txt`.
Use `demo-requester` to create and submit a development request for
`tax-document-classifier`, version `1`. Sign out of the portal, then
use `demo-approver` to approve with a reason. A requester cannot
approve their own request. Refresh the selected request to view audit,
worker status, and Argo state.

The control API, portal, Keycloak, Argo, MLflow, Grafana, Prometheus,
and classifier use the existing shared ingress and trusted local CA.
No per-application forward is needed for browser use. The portal
sign-in uses Keycloak Authorization Code with PKCE. The two demo
identities are separate from existing users. The provisioning script
`scripts/bootstrap_demo_users.py` requires a temporary Keycloak
administration connection and writes newly created passwords only to
a temporary file; move them to the Windows Downloads location outside
Git before removing the temporary file.

A GitOps write can briefly show Argo `Pending` while its root
Application discovers the new commit. The status reconciler rechecks
every 30 seconds. It reports `healthy` when the requested commit is
current, or `deployed` when Argo history proves it was applied but
the app now tracks a newer repository commit. Check the Application's
actual sync/health and the tenant KServe InferenceService before
treating the deployment as serving.

For a direct inference check on the tenant release, use a temporary
Kubernetes service forward during validation and run the existing
`scripts/ml-platform/verify-tax-classifier-v2.py` against model name
`tax-document-classifier-tax-ml-team-dev`. This was executed on
2026-09-18 and all three expected labels passed.
