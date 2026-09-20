# Reviewed AI application requests

Data scientists and developers use Backstage **Create → Request an AI application**.
This creates two private repositories under the selected GitHub owner (default `nolet7`):
`<name>` for the service/model and `<name>-gitops` for deployment desired state.
The existing Create an ML project template remains the earlier model-only workflow;
use the new request template for the reviewed application/deployment path.

## Required setup

- The GitHub owner must support protected private repositories. The current nolet7
  account returned HTTP 403 for that feature during implementation; its planned
  upgrade must complete before a production request can succeed.
- The Backstage GitHub integration currently uses its configured token. It needs
  private repository creation, contents/workflows, PR and collaborator access, and
  repository Administration permission to set/read branch protection. Keep it in
  the existing Kubernetes Secret. This custom action currently expects the same
  PAT-based integration as the lab; GitHub App credential providers require an adapter.
- Specify an independent GitHub reviewer, different from the token identity that
  creates the PR. The reviewer receives write access and must accept the collaborator
  invitation before acting as code owner. Do not use the publishing identity as reviewer.
- Catalog users in `tax-ml-team` or `developers` can request/register applications.
  Add real developers as User entities with `memberOf: [developers]` and matching
  Keycloak usernames. Keycloak login alone does not grant Backstage group membership.
  Platform-team retains template administration; other groups cannot manage templates.

## Request and review sequence

1. Enter name, purpose, GitHub owner, owning team and reviewer.
2. Backstage creates a minimal main branch containing README, CODEOWNERS and catalog
   metadata. This bootstrap is necessary to create/protect main; no application code
   or deployment manifests are committed there.
3. The platform action enables protection and reads it back. Both repositories must
   have one code-owner approval, stale-review dismissal, latest-push approval by another
   identity, administrator enforcement, resolved conversations, required up-to-date CI,
   and force-push/deletion disabled. Required jobs are application-ci and deployment-ci.
4. Only after both gates pass does Backstage open the two initial PRs. It never merges
   either. The output provides links to both repositories and both review requests.
5. Review/merge the application PR first. CI exercises the model pipeline, Python API,
   image build and live container inference. Main-branch CI publishes a SHA-tagged GHCR
   image and records its digest. Pull-request jobs have no package-write/cluster access.
6. Update the deployment PR with that immutable digest. Its initial CI failure on the
   placeholder is intentional. A reviewer approves it after deployment-ci succeeds.
7. Platform administrators review the generated platform-onboarding.yaml in the central
   platform repository, provision the dedicated namespace, private GHCR pull Secret and
   Argo repository credentials, then enroll the scoped AppProject/Application. Argo
   watches only the deployment repository main branch. No cluster credential enters CI.
8. Later releases use the same application PR → image → deployment PR sequence.

The golden application includes synthetic model training, a FastAPI inference endpoint,
DVC/MinIO configuration, MLflow lineage code, Dockerfile, tests and CI. Replace the
fictional tax classifier with a real approved model. Each team needs scoped MinIO access;
the current bootstrap provisions only tax-ml-team. Do not grant developers that credential
as a substitute for provisioning their own prefix policy.

## Failure and recovery

GitHub's bundled publisher can downgrade an unsupported-plan protection response to a
warning. The platform's separate action does not: HTTP errors or incomplete readback stop
the task before application code is published. Failed tasks may leave one or two private
bootstrap repositories. Inspect task outputs and GitHub before retrying; the publisher will
not overwrite an existing name. After resolving plan/permissions, an administrator can
recover deliberately or remove only the confirmed empty bootstrap repositories and retry.
Existing repositories are not rewritten by this feature. No repository is made public to
work around plan limitations. Admins can still deliberately change repository settings;
branch protection governs normal pushes and merges, not GitHub account ownership.

## Platform implementation and rollout

The implementation itself is reviewed in a platform PR. This PR targets Backstage image
`ai-platform-backstage:0.2.0`. Rebuild from services/backstage after
install/typecheck/test/build:backend when the code changes, and load it onto the KIND
nodes before rolling out gitops/platform/backstage/deployment.yaml. Existing Docker
build copies the complete templates directory. After approved merge and rollout, confirm
that Request an AI application appears and perform one request with the upgraded owner
and a real independent reviewer. Verify an unreviewed main merge is rejected before
acceptance. This feature has automated local tests; a live protected-repository test is
blocked until the GitHub upgrade is complete.

References: [GitHub branch protection API](https://docs.github.com/en/rest/branches/branch-protection),
[protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).
