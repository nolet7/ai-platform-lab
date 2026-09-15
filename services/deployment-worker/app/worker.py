import logging
import socket

from rq import Worker

from .queue import (
    queue,
    redis_connection,
)


logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s %(levelname)s "
        "%(name)s %(message)s"
    ),
)


def main():
    redis_connection.ping()

    worker = Worker(
        [queue],
        connection=redis_connection,
        name=(
            "deployment-worker-"
            + socket.gethostname()
        ),
    )

    worker.work(
        with_scheduler=False
    )


if __name__ == "__main__":
    main()
