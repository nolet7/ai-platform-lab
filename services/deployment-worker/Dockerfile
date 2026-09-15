FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOME=/tmp

WORKDIR /app

COPY requirements.txt .

RUN python -m pip install \
    --no-cache-dir \
    -r requirements.txt

COPY app ./app

RUN useradd \
    --uid 10002 \
    --create-home \
    --shell /usr/sbin/nologin \
    deploymentworker

USER 10002:10002

CMD ["python", "-m", "app.worker"]
