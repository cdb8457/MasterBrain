# MasterBrain — Shared External Agent Brain (MVP container)
#
# Core principle: THE CONTAINER IS REPLACEABLE, THE MOUNTED VAULT IS SACRED.
# This image contains ONLY the application code under /app. All durable memory
# lives in /data, which is a bind-mounted host volume provided at runtime and is
# NEVER baked into the image. Rebuilding/replacing this image must not lose data.

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    MASTERBRAIN_DATA_DIR=/data \
    MASTERBRAIN_API_HOST=0.0.0.0 \
    MASTERBRAIN_API_PORT=8077

WORKDIR /app

# Install (optional) API deps first for layer caching. CLI needs none of these.
COPY app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy ONLY the application code. The vault (/data) is mounted, never copied.
COPY app/ /app/

# Declare the durable data mount point. Bind a host share here at runtime.
VOLUME ["/data"]

EXPOSE 8077

# Healthcheck (stdlib only — no curl needed in the slim image). Works for both
# `docker run` and Unraid templates; docker-compose.yml declares the same one.
# If you override CMD to a CLI-only idle container, disable with --no-healthcheck.
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=10s \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8077/health')"]

# Default: run the lightweight FastAPI service. For a CLI-only deployment,
# override the command, e.g.:  docker run ... masterbrain python -m masterbrain stats
# SECURITY: the API has NO AUTH. Keep it LAN-only; never port-forward or
# reverse-proxy it to the internet.
CMD ["python", "-m", "masterbrain.api"]
