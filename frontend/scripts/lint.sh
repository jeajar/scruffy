#!/usr/bin/env bash

set -e
set -x

npm run lint
npm run format:check
npm run typecheck
