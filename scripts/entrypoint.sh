#!/bin/sh

# Run validation check
/healthcheck.sh || exit 1

# Setup cron schedule from env vars or defaults
PROCESS_SCHEDULE=${PROCESS_SCHEDULE:-"0 19 * * *"}
CHECK_SCHEDULE=${CHECK_SCHEDULE:-"0 */6 * * *"}

# Create cron jobs
echo "$CHECK_SCHEDULE cd /app && uv run python -m scruffy.app.cli check >> /var/log/cron.log 2>&1" > /etc/cron.d/scruffy
echo "$PROCESS_SCHEDULE cd /app && uv run python -m scruffy.app.cli process >> /var/log/cron.log 2>&1" >> /etc/cron.d/scruffy
chmod 0644 /etc/cron.d/scruffy

# Start cron and follow logs
cron && tail -f /var/log/cron.log