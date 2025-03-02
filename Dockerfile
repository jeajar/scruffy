FROM python:3.13-slim

# Set working directory
WORKDIR /app

RUN mkdir -p /data && \
    chmod 777 /data

# Install cron and curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    curl && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /data && \
    chmod 777 /data && \
    touch /var/log/cron.log

# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

# Copy project files
COPY . .

# Install dependencies using uv
RUN uv venv
RUN uv pip install -e .

COPY scripts/crontab /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab
RUN crontab /etc/cron.d/crontab

COPY scripts/healthcheck.sh /healthcheck.sh
COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /healthcheck.sh /entrypoint.sh

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]