FROM python:3.13-slim

# Set working directory
WORKDIR /app

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

# Create healthcheck script
RUN echo '#!/bin/sh\nuv run python -m scruffy.app.cli validate' > /healthcheck.sh
RUN chmod +x /healthcheck.sh

# Create entrypoint script
RUN echo '#!/bin/sh\n\
# Run validation check\n\
/healthcheck.sh || exit 1\n\
\n\
# Setup cron schedule from env vars or defaults\n\
PROCESS_SCHEDULE=${PROCESS_SCHEDULE:-"0 19 * * *"}\n\
CHECK_SCHEDULE=${CHECK_SCHEDULE:-"0 */6 * * *"}\n\
\n\
# Create cron jobs\n\
echo "$CHECK_SCHEDULE cd /app && uv run python -m scruffy.app.cli check >> /var/log/cron.log 2>&1" > /etc/cron.d/scruffy\n\
echo "$PROCESS_SCHEDULE cd /app && uv run python -m scruffy.app.cli process >> /var/log/cron.log 2>&1" >> /etc/cron.d/scruffy\n\
chmod 0644 /etc/cron.d/scruffy\n\
\n\
# Start cron and follow logs\n\
cron && tail -f /var/log/cron.log' > /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create log file
RUN touch /var/log/cron.log

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]