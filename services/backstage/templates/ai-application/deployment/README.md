# ${{ values.name }} deployment configuration

Application source: https://github.com/${{ values.githubOwner }}/${{ values.name }}

1. Review and merge the application PR first. Its main-branch CI publishes the
   image to GHCR and records the digest in the workflow summary.
2. On this repository's initial PR branch, replace REPLACE_WITH_REVIEWED_DIGEST
   in base/deployment.yaml with that digest (64 lowercase hexadecimal characters).
   The initial deployment check intentionally fails until a real image is selected.
3. Require `deployment-ci` and approval from @${{ values.reviewer }} before merge.
4. Submit platform-onboarding.yaml as a separate PR to the platform GitOps repo.
   The platform administrator creates namespace `${{ values.name }}-dev`, adds a
   `ghcr-pull` registry Secret with read-only access to the private image, and adds
   read credentials for this private repository to Argo CD. Secrets stay outside Git.
5. After platform review, enroll the AppProject and Application. Argo reconciles
   only environments/dev on main into this application's namespace. It cannot
   create cluster-scoped resources or use other repositories/namespaces.

Validate locally with `pip install PyYAML==6.0.3` and `python scripts/validate.py`.
For local testing, `kubectl -n ${{ values.name }}-dev port-forward svc/${{ values.name }} 8000:80`.
The golden path exposes an internal service; ingress/authentication is a separate
reviewed platform decision. Application CI has no Kubernetes credentials.

Every subsequent release is a digest update on a feature branch and another PR.
Rollback uses a reviewed PR restoring the previous known-good image digest.
Do not point Argo at a feature branch or enable direct pushes to main.
