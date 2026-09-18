import logging
import time

from .config import (
    DISPATCH_INTERVAL_SECONDS, ARGO_API_URL, ARGO_API_TOKEN, ARGO_CA_BUNDLE,
)
from .queue import (
    queue,
    redis_connection,
)
from .repository import (
    list_dispatch_candidates,
    mark_dispatch_error,
    mark_dispatch_intent,
    list_pending_argo_jobs,
    record_argo_observation,
)
from .dispatch_ids import make_rq_job_id
from .argo_api import ArgoAPIError, inspect_application
from .tasks import (
    process_deployment_job,
)


logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s %(levelname)s "
        "%(name)s %(message)s"
    ),
)

logger = logging.getLogger(
    "deployment-dispatcher"
)


def dispatch_once():
    redis_connection.ping()

    candidates = (
        list_dispatch_candidates()
    )

    for job_id in candidates:
        try:
            if not mark_dispatch_intent(
                job_id
            ):
                continue

            rq_job_id = make_rq_job_id(job_id)

            queue.enqueue(
                process_deployment_job,
                str(job_id),
                job_id=rq_job_id,
                job_timeout=180,
                result_ttl=300,
                failure_ttl=3600,
            )

            logger.info(
                "Queued deployment job %s",
                job_id,
            )

        except Exception as error:
            logger.exception(
                "Failed to dispatch job %s",
                job_id,
            )

            mark_dispatch_error(
                job_id=job_id,
                error=str(error),
            )

    for pending in list_pending_argo_jobs():
        key = f"argo-observe:{pending['job_id']}"
        if not redis_connection.set(key, "1", nx=True, ex=30):
            continue
        try:
            observation = inspect_application(
                pending["application"],
                base_url=ARGO_API_URL,
                token=ARGO_API_TOKEN,
                expected_revision=pending["commit_sha"],
                ca_bundle=ARGO_CA_BUNDLE,
            )
            record_argo_observation(pending["job_id"], observation)
        except ArgoAPIError:
            logger.info("Argo application %s is not readable yet", pending["application"])


def main():
    logger.info(
        "Deployment dispatcher starting"
    )

    while True:
        try:
            dispatch_once()

        except Exception:
            logger.exception(
                "Dispatcher iteration failed"
            )

        time.sleep(
            DISPATCH_INTERVAL_SECONDS
        )


if __name__ == "__main__":
    main()
