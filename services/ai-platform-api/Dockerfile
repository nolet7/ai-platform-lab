FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN groupadd --gid 10001 appgroup \
    && useradd \
       --uid 10001 \
       --gid 10001 \
       --no-create-home \
       --shell /usr/sbin/nologin \
       appuser

COPY requirements.txt /app/requirements.txt

RUN python -m pip install --upgrade pip \
    && pip install -r /app/requirements.txt

COPY --chown=10001:10001 app /app/app

RUN mkdir -p /tmp \
    && chown -R 10001:10001 /tmp

USER 10001:10001

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
