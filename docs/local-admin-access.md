# Local administrator access

The lab uses the username `admine` for its overall administrator. Its
password is supplied out of band and must never be committed to Git.

This is a shared username and password across separate local identity stores,
not single sign-on:

| Service | Identity | Privilege |
|---|---|---|
| Self-service portal and protected Platform API | Keycloak `ai-platform` realm | `platform-admin`, `approver`, `data-scientist`, `viewer`; tenant attribute `tax-ml-team` |
| Keycloak admin console | Keycloak `master` realm | `admin` |
| Argo CD | Local Argo CD account | `role:admin` |
| Grafana | Local Grafana administrator | Server administrator |

The portal and Keycloak realm user records live in Keycloak's database.
Argo CD's account declaration and RBAC live in
`gitops/platform-infrastructure/argocd/values.yaml`; its password hash
and password modification time live in the out-of-band
`argocd/argocd-secret` Secret. Grafana's administrator username and
password live in the out-of-band `observability/grafana-admin` Secret.
The Grafana lab uses ephemeral pod storage, so the bootstrap administrator
is recreated from that Secret when its pod restarts.

MLflow and Prometheus have no separate interactive login in this local lab.
The tax classifier is a KServe inference endpoint, not a login page.
The Platform API requires an `ai-platform` realm bearer token for protected
routes. A `platform-admin` can view requests across tenants, but the
portal still requires a tenant claim in its token.

Changing the shared password requires updating both Keycloak realm users,
the Argo CD password hash, and the Grafana bootstrap Secret. Verify all
four logins after rotation. Do not place plaintext credentials or hashes
in Git, screenshots, logs, or this document.
