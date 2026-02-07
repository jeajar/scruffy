#!/bin/bash
# Skip validation when external services (Overseerr, etc.) are not available (e.g. test stack with Mailpit only)
if [ -z "${SKIP_VALIDATE}" ]; then
  /healthcheck.sh
fi
if [ $# -gt 0 ]; then
  exec "$@"
else
  exec scruffy-api
fi