#!/bin/sh

# Run validation check
/healthcheck.sh || exit 1

# Validate cron schedule function
validate_cron() {
    local schedule="$1"
    local name="$2"
    
    # Check if valid cron expression (5 fields)
    if ! echo "$schedule" | grep -P "^(\S+\s+){4}\S+$" > /dev/null 2>&1; then
        echo "Error: Invalid cron schedule for $name: $schedule"
        echo "Format should be: minute hour day month weekday"
        return 1
    fi
}

# Setup cron schedule from env vars or defaults
PROCESS_SCHEDULE=${PROCESS_SCHEDULE:-"0 19 * * *"}
CHECK_SCHEDULE=${CHECK_SCHEDULE:-"0 */6 * * *"}

# Validate schedules
validate_cron "$PROCESS_SCHEDULE" "PROCESS_SCHEDULE" || exit 1
validate_cron "$CHECK_SCHEDULE" "CHECK_SCHEDULE" || exit 1

# Create crontab with proper environment
cat << EOF > /etc/cron.d/scruffy
SHELL=/bin/sh
PATH=/usr/local/bin:/usr/bin:/bin:/app/venv/bin
DATA_DIR=/data
PYTHONPATH=/app

$CHECK_SCHEDULE root cd /app && uv run python -m scruffy.app.cli check >> /var/log/cron.log 2>&1
$PROCESS_SCHEDULE root cd /app && uv run python -m scruffy.app.cli process >> /var/log/cron.log 2>&1
EOF

# Set proper permissions
chmod 0644 /etc/cron.d/scruffy

# Verify crontab syntax
if ! crontab -u root /etc/cron.d/scruffy; then
    echo "Error: Invalid crontab configuration"
    exit 1
fi

# Start cron and follow logs
cron && tail -f /var/log/cron.log