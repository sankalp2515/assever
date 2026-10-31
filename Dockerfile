# Abide: one image with the Gateway API, the Delegate service, the Console (served at /), the content
# filter (engine + local classifier, baked in) and the Gemini agents (Google ADK). Runs as an unprivileged user.
#
#   docker compose up --build -d        # gateway + PostgreSQL (docker-compose.yml), Console on http://localhost:8000
#
# Configuration is environment only (.env.example). The Console's read-only key is the build argument VITE_API_KEY and
# must equal the gateway's INTENTSEAL_PUBLIC_KEY (docker-compose.yml passes both).

FROM node:22-slim AS console
WORKDIR /console
COPY apps/console/package.json apps/console/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY apps/console ./
ARG VITE_API_KEY=""
ENV VITE_API_BASE="" VITE_API_KEY=$VITE_API_KEY VITE_PRODUCT_NAME=Assever
RUN npm run build


FROM python:3.11-slim AS build
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
WORKDIR /src
COPY requirements.lock ./
COPY packages/core/pyproject.toml packages/core/README.md packages/core/LICENSE packages/core/NOTICE ./packages/core/
COPY packages/sdk/pyproject.toml packages/sdk/README.md packages/sdk/LICENSE packages/sdk/NOTICE ./packages/sdk/
COPY services/gateway/pyproject.toml ./services/gateway/
# Runtime dependencies only, at the exact versions of requirements.lock (a constraints file: nothing extra installed).
RUN --mount=type=cache,target=/root/.cache/pip pip install -c requirements.lock "./packages/core[engine,classifiers,ocr,postgres]" ./packages/sdk ./services/gateway openai
# Abide's Gemini agents run on Google ADK (it brings google-genai and a newer FastAPI; tested together).
RUN --mount=type=cache,target=/root/.cache/pip pip install "google-adk==2.12.0" "google-genai==2.34.0"
RUN --mount=type=cache,target=/root/.cache/pip pip install "psycopg_pool==3.3.0" "PyJWT==2.10.1" "cryptography==46.0.3" "pytest==9.1.1" "pytest-asyncio==1.4.0" "respx==0.23.1" "anthropic==1.12.0"
# Bake the Tier 1 classifier into the image so a cold start never runs without it.
ENV HF_HOME=/opt/models/hf
RUN --mount=type=cache,target=/root/hf-cache HF_HOME=/root/hf-cache python -c "from huggingface_hub import snapshot_download; snapshot_download('protectai/deberta-v3-base-prompt-injection-v2',allow_patterns=['onnx/*','*.json'])" \
 && mkdir -p /opt/models/hf && cp -a /root/hf-cache/. /opt/models/hf/


FROM python:3.11-slim AS runtime
# OpenCV runtime libraries for the OCR extractor; DejaVu for Unicode PDF rendering in the demo fixtures.
RUN apt-get update \
 && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 fonts-dejavu-core \
 && rm -rf /var/lib/apt/lists/* \
 && useradd --create-home --uid 1000 intentseal \
 && mkdir -p /data && chown intentseal:intentseal /data
COPY --from=build /opt/venv /opt/venv
COPY --from=build --chown=intentseal:intentseal /opt/models /opt/models
WORKDIR /app
COPY packages ./packages
COPY services/gateway ./services/gateway
COPY config ./config
COPY policies ./policies
COPY tests ./tests
COPY eval ./eval
COPY pytest.ini ./
COPY scripts/assever_integrated_study.py ./scripts/
COPY scripts/sync_package_data.py ./scripts/
COPY --from=console /console/dist ./console
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/opt/models/hf \
    HF_HUB_OFFLINE=1 \
    INTENTSEAL_HOME=/app \
    INTENTSEAL_DB_PATH=/data/intentseal.db \
    INTENTSEAL_POLICY_DIR=/data/policies \
    INTENTSEAL_STORE_PREVIEWS=0 \
    INTENTSEAL_CONSOLE_DIR=/app/console \
    PORT=8000
ENV PYTHONPATH=/app/packages/core:/app/packages/sdk:/app/services/gateway:/app/eval
COPY LICENSE NOTICE ./
USER intentseal
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/readyz' % os.environ.get('PORT', '8000'), timeout=4)"
CMD ["python", "-m", "intentseal_gateway"]
