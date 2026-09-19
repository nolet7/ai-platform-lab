"""Render a tenant-scoped KServe release from validated immutable lineage."""

import re
from uuid import UUID

from .config import GITHUB_BRANCH, GITHUB_REPOSITORY
from .model_catalog import get_model_config
from .model_registry import GIT_SHA, MODEL_ID, RUN_ID, VERSION


DNS_LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z")


class ModelReleaseError(ValueError):
    pass


def render_model_release_files(payload):
    name = payload.get("model_name")
    tenant = payload.get("tenant_id")
    environment = payload.get("environment")
    version = payload.get("model_version")
    reference = payload.get("model_reference")
    model_config = get_model_config(name)
    if model_config is None:
        raise ModelReleaseError("Model is not registered in the platform catalog")
    if not isinstance(tenant, str) or not DNS_LABEL.fullmatch(tenant):
        raise ModelReleaseError("Invalid tenant")
    if environment not in set(model_config["environments"]):
        raise ModelReleaseError("Environment is not enabled for this model")
    if not isinstance(version, str) or not VERSION.fullmatch(version):
        raise ModelReleaseError("Version must be numeric")
    try:
        request_id = str(UUID(str(payload["request_id"])))
    except (KeyError, TypeError, ValueError) as error:
        raise ModelReleaseError("Invalid request ID") from error
    if not isinstance(reference, dict):
        raise ModelReleaseError("Missing immutable model reference")
    macro_f1 = reference.get("macro_f1")
    minimum_macro_f1 = model_config["minimum_macro_f1"]
    if (
        not isinstance(macro_f1, (int, float))
        or macro_f1 < minimum_macro_f1
    ):
        raise ModelReleaseError(
            f"Model macro F1 does not meet required {minimum_macro_f1}"
        )
    model_id = reference.get("model_id")
    if not isinstance(model_id, str) or not MODEL_ID.fullmatch(model_id):
        raise ModelReleaseError("Invalid immutable model ID")
    if (
        reference.get("model_name") != name
        or reference.get("model_version") != version
    ):
        raise ModelReleaseError("Registry reference does not match request")
    run_id = reference.get("run_id")
    source_sha = reference.get("source_git_sha")
    dataset = reference.get("dataset_version")
    if not isinstance(run_id, str) or not RUN_ID.fullmatch(run_id):
        raise ModelReleaseError("Invalid run ID")
    if not isinstance(source_sha, str) or not GIT_SHA.fullmatch(source_sha):
        raise ModelReleaseError("Invalid source Git SHA")
    if not isinstance(dataset, str) or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._-]{0,62}", dataset
    ):
        raise ModelReleaseError("Invalid dataset version")
    uri = reference.get("storage_uri")
    if not isinstance(uri, str) or not re.fullmatch(
        r"s3://mlflow-artifacts/[0-9]+/models/"
        + re.escape(model_id)
        + r"/artifacts",
        uri,
    ):
        raise ModelReleaseError("Storage URI does not match model ID")
    release = f"{name}-{tenant}-{environment}"
    if len(release) > 63 or not DNS_LABEL.fullmatch(release):
        raise ModelReleaseError("Release name is too long")
    serving_name = release
    if len(serving_name + "-predictor-ml-platform") > 63:
        suffix = {"staging": "stg"}.get(environment, environment)
        serving_name = f"{name}-{tenant}-{suffix}"
    if len(serving_name + "-predictor-ml-platform") > 63:
        raise ModelReleaseError("Release name exceeds KServe hostname limit")
    root = f"gitops/ml-platform/releases/{name}/{tenant}/{environment}"
    namespace = "ml-platform"

    inference = f"""\
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: {serving_name}
  labels:
    app.kubernetes.io/name: {name}
    app.kubernetes.io/component: serving
    ai-platform.io/tenant: {tenant}
    ai-platform.io/environment: {environment}
    ai-platform.io/model-version: "{version}"
    ai-platform.io/model-id: {model_id}
    ai-platform.io/dataset-version: {dataset}
  annotations:
    serving.kserve.io/deploymentMode: Standard
    serving.kserve.io/secretName: {model_config["storage_secret"]}
    ai-platform.io/request-id: "{request_id}"
    ai-platform.io/run-id: "{run_id}"
    ai-platform.io/source-git-sha: "{source_sha}"
spec:
  predictor:
    serviceAccountName: {model_config["service_account"]}
    model:
      modelFormat:
        name: {model_config["model_format"]}
      runtime: {model_config["runtime"]}
      protocolVersion: v2
      storageUri: {uri}
      resources:
        requests:
          cpu: 100m
          memory: 512Mi
        limits:
          cpu: "1"
          memory: 2Gi
"""
    policy = f"""\
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: {serving_name}
spec:
  podSelector:
    matchLabels:
      serving.kserve.io/inferenceservice: {serving_name}
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: ai-platform
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8080
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: observability
      ports:
        - protocol: TCP
          port: 8082
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
    - to:
        - podSelector:
            matchLabels:
              app.kubernetes.io/name: minio
      ports:
        - protocol: TCP
          port: 9000
    - to:
        - podSelector:
            matchLabels:
              app.kubernetes.io/name: mlflow
      ports:
        - protocol: TCP
          port: 5000
"""
    workspace = f"""\
apiVersion: platform.ai/v1alpha1
kind: ModelWorkspace
metadata:
  name: {release}
  labels:
    ai-platform.io/tenant: {tenant}
    ai-platform.io/environment: {environment}
  annotations:
    ai-platform.io/request-id: "{request_id}"
spec:
  modelName: {name}
  environment: {environment}
  storage: 1Gi
  crossplane:
    compositionRef:
      name: model-workspace-local
"""
    kustomization = """\
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: ml-platform
resources:
  - inferenceservice.yaml
  - networkpolicy.yaml
  - workspace.yaml
"""
    app_name = f"{release}-serving"
    if len(app_name) > 63:
        raise ModelReleaseError("Argo application name is too long")
    application = f"""\
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: {app_name}
  namespace: argocd
spec:
  project: ai-platform-ml
  source:
    repoURL: https://github.com/{GITHUB_REPOSITORY}.git
    targetRevision: {GITHUB_BRANCH}
    path: {root}
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
        f"{root}/inferenceservice.yaml": inference,
        f"{root}/networkpolicy.yaml": policy,
        f"{root}/workspace.yaml": workspace,
        f"{root}/kustomization.yaml": kustomization,
        f"gitops/argocd/applications/{app_name}.yaml": application,
    }
    metadata = {
        "application": app_name,
        "namespace": namespace,
        "workload": serving_name,
        "workspace": release,
        "environment": environment,
        "workload_path": root,
        "model_id": model_id,
        "model_version": version,
        "storage_uri": uri,
    }
    return files, metadata
