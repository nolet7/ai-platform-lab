from uuid import UUID

from .config import MLFLOW_TRACKING_URI
from .model_registry import resolve_model_version

from .gitops_writer import (
    publish_gitops_manifests,
)
from .repository import (
    claim_job,
    complete_gitops_job,
    fail_job,
)


VALID_ENVIRONMENTS = {
    "dev",
    "staging",
    "prod",
}


def process_deployment_job(
    job_id: str,
):
    """
    Process one approved deployment job and
    publish its desired state to Git.

    Argo CD, not this worker, performs the
    Kubernetes reconciliation.
    """

    parsed_job_id = UUID(job_id)

    payload = claim_job(
        parsed_job_id
    )

    if payload is None:
        return {
            "status": "ignored",
            "job_id": job_id,
        }

    try:
        environment = payload[
            "environment"
        ]

        model_name = payload[
            "model_name"
        ]

        model_version = payload[
            "model_version"
        ]

        if (
            environment
            not in VALID_ENVIRONMENTS
        ):
            raise ValueError(
                "Unsupported deployment environment"
            )

        if not model_name:
            raise ValueError(
                "model_name is required"
            )

        if not model_version:
            raise ValueError(
                "model_version is required"
            )

        if model_name == "tax-document-classifier":
            reference = resolve_model_version(
                model_name, model_version, MLFLOW_TRACKING_URI
            )
            if reference["macro_f1"] < 0.8:
                raise ValueError("Model validation threshold was not met")
            payload = {**payload, "model_reference": reference}
        else:
            reference = None

        desired_spec = {
            "apiVersion": (
                "platform.ai/v1alpha1"
            ),
            "kind": (
                "ModelDeploymentRequest"
            ),
            "metadata": {
                "requestId": (
                    payload["request_id"]
                ),
                "tenant": (
                    payload["tenant_id"]
                ),
            },
            "spec": {
                "model": {
                    "name": model_name,
                    "version": model_version,
                },
                "environment": environment,
                "deploymentMode": (
                    "gitops"
                ),
                "immutableModel": reference,
            },
        }

        gitops_result = (
            publish_gitops_manifests(
                payload
            )
        )

        result_payload = {
            "desired_state": desired_spec,
            "gitops": gitops_result,
            "nextAction": (
                "argocd_reconcile"
            ),
        }

        complete_gitops_job(
            job_id=parsed_job_id,
            result_payload=result_payload,
        )

        return {
            "status": "gitops_committed",
            "job_id": job_id,
            "request_id": (
                payload["request_id"]
            ),
            "commit_sha": (
                gitops_result[
                    "commit_sha"
                ]
            ),
            "application": (
                gitops_result[
                    "application"
                ]
            ),
        }

    except Exception as error:
        fail_job(
            job_id=parsed_job_id,
            error=str(error),
        )
        raise
