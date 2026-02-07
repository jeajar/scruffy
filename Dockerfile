# Build stage: install dependencies and application
FROM python:3.13-slim AS builder

WORKDIR /app

# Install curl for uv installer, then uv
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

# Copy only what's needed for the install (smaller context, no frontend/tests)
COPY pyproject.toml uv.lock README.md ./
COPY scruffy/ ./scruffy/

# Create venv and install production dependencies only (no dev deps, no editable)
RUN uv venv && uv pip install .
# Strip caches and bytecode to reduce size
RUN find /app/.venv -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true \
    && find /app/.venv -name "*.pyc" -delete \
    && rm -rf /root/.cache/uv

# Production stage: minimal runtime
FROM python:3.13-slim

WORKDIR /app

# Runtime deps only (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /data \
    && chmod 777 /data

# Copy venv from builder (no uv, no build tools)
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy scripts
COPY scripts/healthcheck.sh /healthcheck.sh
COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /healthcheck.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
