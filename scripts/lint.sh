#!/usr/bin/env bash

set -e
set -x

mypy scruffy
ruff check scruffy
ruff format scruffy --check