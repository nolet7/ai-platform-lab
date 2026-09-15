import os


DATABASE_URL = os.environ["DATABASE_URL"]

REDIS_HOST = os.getenv(
    "REDIS_HOST",
    "platform-redis",
)

REDIS_PORT = int(
    os.getenv(
        "REDIS_PORT",
        "6379",
    )
)

REDIS_PASSWORD = os.environ[
    "REDIS_PASSWORD"
]

QUEUE_NAME = os.getenv(
    "QUEUE_NAME",
    "deployments",
)

DISPATCH_INTERVAL_SECONDS = int(
    os.getenv(
        "DISPATCH_INTERVAL_SECONDS",
        "5",
    )
)

DISPATCH_LEASE_SECONDS = int(
    os.getenv(
        "DISPATCH_LEASE_SECONDS",
        "60",
    )
)

RETRY_DELAY_SECONDS = int(
    os.getenv(
        "RETRY_DELAY_SECONDS",
        "15",
    )
)
