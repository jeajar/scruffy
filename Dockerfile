FROM python:3.13-slim

# Set working directory
WORKDIR /app

RUN mkdir -p /data && \
    chmod 777 /data

# Install cron and curl
RUN apt-get update && apt-get install -y cron curl

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

COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY scripts/healthcheck.sh /healthcheck.sh
RUN chmod +x /healthcheck.sh

# Create log file
RUN touch /var/log/cron.log

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]