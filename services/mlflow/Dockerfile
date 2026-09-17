FROM ghcr.io/mlflow/mlflow:v3.16.0

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir \
       psycopg2-binary==2.9.10 \
       'boto3>=1.34,<2'

EXPOSE 5000
