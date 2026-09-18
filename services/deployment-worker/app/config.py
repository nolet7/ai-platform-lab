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

GITHUB_REPOSITORY = os.getenv(
    "GITHUB_REPOSITORY",
    "nolet7/ai-platform-lab",
)

GITHUB_BRANCH = os.getenv(
    "GITHUB_BRANCH",
    "main",
)

GITHUB_TOKEN = os.getenv(
    "GITHUB_TOKEN",
    "",
)

GITOPS_BASE_IMAGE = os.getenv(
    "GITOPS_BASE_IMAGE",
    "nginx:1.31.5-alpine3.24",
)

GITHUB_API_URL = os.getenv(
    "GITHUB_API_URL",
    "https://api.github.com",
)

MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "http://mlflow.ml-platform.svc.cluster.local:5000",
)
