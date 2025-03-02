#!/bin/bash
/healthcheck.sh
printenv > /etc/environment
chmod 0644 /etc/cron.d/crontab
cron -f