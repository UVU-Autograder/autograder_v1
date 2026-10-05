FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app \
    REPO_ROOT=/app

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY backend ./
COPY docs ./docs

RUN useradd --create-home --shell /usr/sbin/nologin autograder \
    && mkdir -p /data/artifacts /data/workspaces \
    && chown -R autograder:autograder /app /data

ENV UVICORN_HOST=127.0.0.1 \
    UVICORN_PORT=8000

USER autograder

ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]
CMD ["sh", "-c", "exec uvicorn app.main:app --host ${UVICORN_HOST:-127.0.0.1} --port ${UVICORN_PORT:-8000}"]
