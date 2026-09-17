FROM ghcr.io/mlflow/mlflow:v3.16.0@sha256:470607da2a70fa38724d3d7db0a54a78b50fac708f7291bfebe1935fa95259ae
COPY requirements.txt /tmp/serving-requirements.txt
RUN pip install --no-cache-dir -r /tmp/serving-requirements.txt \
    && useradd --uid 10001 --create-home mlserver
ENV HOME=/home/mlserver \
    MLSERVER_MODELS_DIR=/mnt/models \
    PYTHONUNBUFFERED=1
WORKDIR /home/mlserver
USER 10001
CMD ["mlserver", "start", "/mnt/models"]
