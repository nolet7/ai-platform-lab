import logging
import time
from uuid import uuid4

from .config import (
    DISPATCH_INTERVAL_SECONDS,
)
from .queue import (
    queue,
    redis_connection,
)
from .repository import (
    list_dispatch_candidates,
    mark_dispatch_error,
    mark_dispatch_intent,
)
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

            rq_job_id = (
                f"deployment:"
                f"{job_id}:"
                f"{uuid4()}"
            )

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
