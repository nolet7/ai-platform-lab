FROM python:3.11-slim-bookworm

ARG GIT_COMMIT_SHA=unknown

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_GIT_COMMIT_SHA=${GIT_COMMIT_SHA}

LABEL org.opencontainers.image.title="AI Platform Tax Document Classifier Training"
LABEL org.opencontainers.image.revision="${GIT_COMMIT_SHA}"

RUN apt-get update \
    && apt-get install -y \
       --no-install-recommends \
       git \
       ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install \
    --no-cache-dir \
    -r requirements.txt

COPY generate_sample_data.py .
COPY train.py .

RUN useradd \
      --uid 10001 \
      --create-home \
      appuser \
    && mkdir -p /app/data \
    && chown -R 10001:10001 /app

USER 10001

CMD ["/bin/sh","-c","python generate_sample_data.py --output /app/data/tax_documents.csv --rows-per-class 60 && python train.py --data /app/data/tax_documents.csv"]
