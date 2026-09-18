# Self-service portal

Open `https://api.ai-platform.local/portal/`. The portal uses Keycloak
Authorization Code with PKCE S256. The public `ai-platform-portal` client
has exact sign-in and sign-out return URLs, an exact web origin, API audience mapper, and
`tenant_id` mapper. Run `scripts/configure_portal_oidc.py` with a
temporary Keycloak port-forward on local port 19084 to reproduce its
bootstrap configuration. The script reads the existing cluster bootstrap
Secret and prints no credentials.

Access tokens stay in browser memory. The API validates their Keycloak
signature, issuer, audience, tenant, and roles. A requester can create and
submit a model release. Another user with the `approver` realm role can
approve or reject it, and the API writes audit events. The portal reads
tenant-scoped deployment history, request detail, worker job result,
Argo and Crossplane observations, and audit events from the real control API.

The demo form defaults to `tax-document-classifier`, immutable version
`1`, and the development environment. Approval queues the existing
deployment worker; GitOps and Argo reconcile the release. Refresh shows
the latest database-backed state. An initial Argo observation can be
pending while Argo discovers a newly published Git commit.

For the local KIND lab, build and load `ai-platform-api:0.4.3` on every
node before syncing the GitOps Deployment. Do not commit demo passwords
or the Keycloak bootstrap Secret.

Sign out sends the browser to Keycloak RP-initiated logout before returning to the portal, so separate requester and approver identities can use the same browser session.
