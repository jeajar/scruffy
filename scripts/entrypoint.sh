#!/bin/bash
/healthcheck.sh
if [ $# -gt 0 ]; then
  exec "$@"
else
  exec scruffy-api
fi