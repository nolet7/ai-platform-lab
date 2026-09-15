from uuid import UUID

from .repository import (
    claim_job,
    complete_job,
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
    Process one approved deployment orchestration job.

    Phase 2K stops at producing validated desired state.
    Phase 3 will consume this desired state and generate
    GitOps manifests for Argo CD.
    """

    parsed_job_id = UUID(
        job_id
    )

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
                "deploymentMode": "gitops",
            },
            "nextAction": (
                "generate_gitops_manifest"
            ),
        }

        complete_job(
            job_id=parsed_job_id,
            result_payload=desired_spec,
        )

        return {
            "status": (
                "ready_for_gitops"
            ),
            "job_id": job_id,
            "request_id": (
                payload["request_id"]
            ),
        }

    except Exception as error:
        fail_job(
            job_id=parsed_job_id,
            error=str(error),
        )

        raise
