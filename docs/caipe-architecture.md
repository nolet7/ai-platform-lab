# CAIPE request observation and recovery

## Live path

The Platform API authenticates Keycloak bearer tokens, checks the tenant and
role, records a request, and requires a different identity to approve it. The
dispatcher queues an approved job. The worker resolves an immutable MLflow
model reference and commits the KServe release and Crossplane `ModelWorkspace`
to Git. Argo CD reconciles that revision. The worker and dispatcher use the
CAIPE supervisor to observe the resulting state and update the request and
audit trail. The portal renders the resulting status and message.

The supervisor in `services/deployment-worker/app/supervisor.py` sends A2A v1
JSON-RPC `SendMessage` tasks to the Argo and Crossplane agents over internal
services. It puts a UUID request ID and the same correlation ID in the JSON
text part. An agent returns a completed task with one `observation` artifact;
the supervisor verifies the JSON-RPC ID, task state, artifact identity,
application, revision or workspace, and request ID. Failed or malformed
responses are treated as unavailable. The dispatcher can retry the read-only
observation on its next status pass. The Git commit and request ID make the
state observation repeatable; agent tasks themselves use an in-memory store
and are not a durable queue.

Each agent invokes its own MCP Streamable HTTP tool with an internal bearer
token. The Argo agent exposes `inspect_deployment(application,
expected_revision)`; the Crossplane agent exposes
`inspect_model_workspace(application, workspace, namespace, request_id)`.
These are read-only, input-validated calls to the real Argo CD API. The
Crossplane tool reads the Application resource view and verifies the
request-linked XR before returning Ready/Synced and PVC phase. The Argo
agent reports sync, health, and revision/history evidence. Neither exposes
arbitrary shell or Kubernetes API access.

Only the two agent pods hold the restricted Argo API token and private-CA
bundle. The worker and dispatcher receive the CAIPE internal token through
an out-of-band Kubernetes Secret. Namespace NetworkPolicies limit ingress to
the agents and outbound access from the worker and dispatcher to the agents.
The agent logs record tool calls and completed or failed task correlation IDs.
The API audit trail records request, approval, Git commit, infrastructure
readiness and deployment readiness. The internal token and the Argo token
must never be committed to Git or displayed in runbook output.

## Verification on the local cluster

On 2026-09-18 request `5e6ed6ca-8af0-4cd1-9398-ac1ab49daf8a` was created
by `demo-requester` for `tax-ml-team`, immutable model version `1`, staging.
Self-approval returned 403; `demo-approver` approved it. Worker image `0.3.8`
committed revision `8e3200a6060d6aa74255e1b014be6dd12090d008`.
The initial Argo observation reported the revision applied while sync was
still settling. A later dispatcher pass reported `healthy` with the message
"Argo CD and Crossplane are ready". The serving Application was Synced and
Healthy. Both agent logs recorded completed A2A tasks with that request ID.
The workspace was previously verified Ready, with its 1Gi PVC Bound and
initializer Job Complete. CI for PR #21 passed all four jobs before merge.

To inspect this request using a tenant-authorized token:

```text
GET https://api.ai-platform.local/deployments/5e6ed6ca-8af0-4cd1-9398-ac1ab49daf8a
GET https://api.ai-platform.local/deployments/5e6ed6ca-8af0-4cd1-9398-ac1ab49daf8a/audit
```

From WSL, `kubectl -n argocd get application
tax-document-classifier-tax-ml-team-staging-serving` and `kubectl -n
ml-platform get modelworkspace tax-document-classifier-tax-ml-team-staging`
show reconciler state. In the portal, sign in with a tenant account to view
the request, policy decision, Argo/Crossplane status and audit events.

## Recovery and rollback boundaries

If an agent is unavailable, preserve the Git commit and request ID. Restore
the agent or its network/credential path, then let the dispatcher reobserve;
do not mark a deployment healthy from a stale observation. If the release is
unhealthy, stop promotion and inspect the Argo Application, KServe service,
Crossplane XR, worker audit and agent logs before changing desired state.

To return to a known good immutable model version, submit a new request for
that exact registered version and obtain independent approval. This uses the
same GitOps path and retains an audit trail. Check the resolved model ID and
artifact URI, then wait for Argo, Crossplane and inference readiness. Do not
delete the workspace/PVC or revert an unrelated platform commit. The current
demo registry only establishes version `1`; a different-version rollback has
not yet been exercised and automated rollback is not implemented. This is a
remaining acceptance gap.
