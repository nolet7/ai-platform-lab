import re
from uuid import UUID

import httpx

from .model_release_writer import render_model_release_files

from .config import (
    GITHUB_API_URL,
    GITHUB_BRANCH,
    GITHUB_REPOSITORY,
    GITHUB_TOKEN,
    GITOPS_BASE_IMAGE,
)


ENVIRONMENTS = {
    "dev": {
        "namespace": "ai-platform-dev",
        "project": "ai-platform-dev",
        "replicas": 1,
    },
    "staging": {
        "namespace": "ai-platform-staging",
        "project": "ai-platform-staging",
        "replicas": 2,
    },
    "prod": {
        "namespace": "ai-platform-prod",
        "project": "ai-platform-prod",
        "replicas": 3,
    },
}


class GitOpsPublishError(RuntimeError):
    pass


DNS_LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z")
VERSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")


def validate_payload(payload: dict) -> None:
    for field in ("model_name", "tenant_id"):
        value = payload.get(field)
        if not isinstance(value, str) or not DNS_LABEL.fullmatch(value):
            raise GitOpsPublishError(f"{field} must be a DNS label")
    version = payload.get("model_version")
    if not isinstance(version, str) or not VERSION.fullmatch(version):
        raise GitOpsPublishError("model_version contains unsafe characters")
    try:
        UUID(str(payload["request_id"]))
    except (KeyError, TypeError, ValueError) as error:
        raise GitOpsPublishError("request_id must be a UUID") from error


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(
        r"[^a-z0-9-]+",
        "-",
        value,
    )
    value = re.sub(
        r"-+",
        "-",
        value,
    )
    return value.strip("-")


def render_gitops_files(
    payload: dict,
) -> tuple[dict[str, str], dict]:

    validate_payload(payload)

    if payload["model_name"] == "tax-document-classifier":
        return render_model_release_files(payload)

    environment = payload["environment"]
    config = ENVIRONMENTS.get(environment)

    if config is None:
        raise GitOpsPublishError(
            f"Unsupported environment: {environment}"
        )

    model_name = payload["model_name"]
    model_version = payload["model_version"]
    tenant_id = payload["tenant_id"]
    request_id = payload["request_id"]

    workload = slugify(model_name)
    tenant_label = slugify(tenant_id)

    namespace = config["namespace"]
    project = config["project"]
    replicas = config["replicas"]

    workload_root = (
        f"gitops/workloads/{workload}"
    )

    app_name = (
        f"{workload}-{environment}"
    )

    deployment = f"""\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {workload}
  labels:
    app.kubernetes.io/name: {workload}
    platform.ai/model: {workload}
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: {workload}
  template:
    metadata:
      labels:
        app.kubernetes.io/name: {workload}
        platform.ai/model: {workload}
    spec:
      containers:
        - name: model-runtime
          image: {GITOPS_BASE_IMAGE}
          ports:
            - name: http
              containerPort: 80
          env:
            - name: MODEL_NAME
              value: "{model_name}"
            - name: MODEL_VERSION
              value: "{model_version}"
            - name: PLATFORM_TENANT
              value: "{tenant_id}"
            - name: PLATFORM_REQUEST_ID
              value: "{request_id}"
          resources:
            requests:
              cpu: 25m
              memory: 32Mi
            limits:
              cpu: 100m
              memory: 64Mi
          readinessProbe:
            httpGet:
              path: /
              port: http
            initialDelaySeconds: 2
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /
              port: http
            initialDelaySeconds: 5
            periodSeconds: 10
"""

    service = f"""\
apiVersion: v1
kind: Service
metadata:
  name: {workload}
spec:
  selector:
    app.kubernetes.io/name: {workload}
  ports:
    - name: http
      port: 80
      targetPort: http
  type: ClusterIP
"""

    base_kustomization = """\
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml
  - service.yaml
"""

    overlay = f"""\
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

namespace: {namespace}

nameSuffix: -{environment}

replicas:
  - name: {workload}
    count: {replicas}

labels:
  - pairs:
      platform.example.com/environment: {environment}
      platform.example.com/tenant: {tenant_label}
      platform.example.com/model-version: "{model_version}"
"""

    repo_url = (
        "https://github.com/"
        f"{GITHUB_REPOSITORY}.git"
    )

    application = f"""\
apiVersion: argoproj.io/v1alpha1
kind: Application

metadata:
  name: {app_name}
  namespace: argocd

spec:
  project: {project}

  source:
    repoURL: {repo_url}
    targetRevision: {GITHUB_BRANCH}
    path: {workload_root}/overlays/{environment}

  destination:
    server: https://kubernetes.default.svc
    namespace: {namespace}

  syncPolicy:
    automated:
      prune: true
      selfHeal: true

    syncOptions:
      - CreateNamespace=false
"""

    files = {
        (
            f"{workload_root}/base/"
            "deployment.yaml"
        ): deployment,
        (
            f"{workload_root}/base/"
            "service.yaml"
        ): service,
        (
            f"{workload_root}/base/"
            "kustomization.yaml"
        ): base_kustomization,
        (
            f"{workload_root}/overlays/"
            f"{environment}/kustomization.yaml"
        ): overlay,
        (
            "gitops/argocd/applications/"
            f"{app_name}.yaml"
        ): application,
    }

    metadata = {
        "application": app_name,
        "namespace": namespace,
        "workload": workload,
        "environment": environment,
        "workload_path": (
            f"{workload_root}/overlays/"
            f"{environment}"
        ),
    }

    return files, metadata


def publish_gitops_manifests(
    payload: dict,
) -> dict:

    if not GITHUB_TOKEN:
        raise GitOpsPublishError(
            "GITHUB_TOKEN is not configured"
        )

    files, metadata = render_gitops_files(
        payload
    )

    headers = {
        "Authorization": (
            f"Bearer {GITHUB_TOKEN}"
        ),
        "Accept": (
            "application/vnd.github+json"
        ),
        "X-GitHub-Api-Version": (
            "2022-11-28"
        ),
    }

    base_url = (
        f"{GITHUB_API_URL}/repos/"
        f"{GITHUB_REPOSITORY}"
    )

    try:
        with httpx.Client(
            headers=headers,
            timeout=30.0,
        ) as client:

            ref_response = client.get(
                f"{base_url}/git/ref/"
                f"heads/{GITHUB_BRANCH}"
            )
            ref_response.raise_for_status()

            parent_sha = (
                ref_response.json()
                ["object"]["sha"]
            )

            commit_response = client.get(
                f"{base_url}/git/commits/"
                f"{parent_sha}"
            )
            commit_response.raise_for_status()

            base_tree_sha = (
                commit_response.json()
                ["tree"]["sha"]
            )

            tree_entries = []

            for path, content in files.items():

                blob_response = client.post(
                    f"{base_url}/git/blobs",
                    json={
                        "content": content,
                        "encoding": "utf-8",
                    },
                )
                blob_response.raise_for_status()

                tree_entries.append(
                    {
                        "path": path,
                        "mode": "100644",
                        "type": "blob",
                        "sha": (
                            blob_response.json()
                            ["sha"]
                        ),
                    }
                )

            tree_response = client.post(
                f"{base_url}/git/trees",
                json={
                    "base_tree": (
                        base_tree_sha
                    ),
                    "tree": tree_entries,
                },
            )
            tree_response.raise_for_status()

            new_tree_sha = (
                tree_response.json()["sha"]
            )

            message = (
                "feat(gitops): deploy "
                f"{metadata['workload']} "
                f"to {metadata['environment']} "
                f"[{payload['request_id']}]"
            )

            new_commit_response = client.post(
                f"{base_url}/git/commits",
                json={
                    "message": message,
                    "tree": new_tree_sha,
                    "parents": [
                        parent_sha,
                    ],
                },
            )
            new_commit_response.raise_for_status()

            new_commit_sha = (
                new_commit_response.json()
                ["sha"]
            )

            update_response = client.patch(
                f"{base_url}/git/refs/"
                f"heads/{GITHUB_BRANCH}",
                json={
                    "sha": new_commit_sha,
                    "force": False,
                },
            )
            update_response.raise_for_status()

    except httpx.HTTPError as error:
        raise GitOpsPublishError(
            f"GitHub GitOps publish failed: {error}"
        ) from error

    return {
        **metadata,
        "repository": GITHUB_REPOSITORY,
        "branch": GITHUB_BRANCH,
        "commit_sha": new_commit_sha,
        "files_written": sorted(files),
    }
