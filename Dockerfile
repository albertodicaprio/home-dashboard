FROM ghcr.io/astral-sh/uv:0.13.5 AS uv

FROM python:3.12-slim
COPY --from=uv /uv /uvx /bin/
RUN apt-get update && apt-get install -y --no-install-recommends libusb-1.0-0 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY station/upstream/ws3000mqtt.py ./station/ws3000mqtt.py
COPY station/upstream/LICENSE ./station/LICENSE
COPY exporter/mqtt_exporter.py ./exporter/mqtt_exporter.py
ENV PATH="/app/.venv/bin:${PATH}" PYTHONUNBUFFERED=1

