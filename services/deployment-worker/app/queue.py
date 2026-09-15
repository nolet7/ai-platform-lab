from redis import Redis
from rq import Queue

from .config import (
    QUEUE_NAME,
    REDIS_HOST,
    REDIS_PASSWORD,
    REDIS_PORT,
)


redis_connection = Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    socket_connect_timeout=3,
    socket_timeout=5,
    health_check_interval=30,
)


queue = Queue(
    QUEUE_NAME,
    connection=redis_connection,
)
