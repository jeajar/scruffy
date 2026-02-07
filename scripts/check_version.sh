#!/usr/bin/env bash
# Version check script for CI (GitLab MR / GitHub PR).
# Ensures: version not already tagged, frontend in sync, optional SemVer + monotonic bump checks.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# Read version from pyproject.toml (source of truth)
VERSION=$(grep -m1 '^version = ' pyproject.toml | cut -d'"' -f2)

if [[ -z "$VERSION" ]]; then
  echo "ERROR: Could not read version from pyproject.toml"
  exit 1
fi

echo "Checking version: $VERSION"

# 1. SemVer format check (optional but recommended)
SEMVER_REGEX='^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.-]+)?(\+[a-zA-Z0-9.-]+)?$'
if ! [[ "$VERSION" =~ $SEMVER_REGEX ]]; then
  echo "ERROR: Version '$VERSION' does not follow SemVer format (e.g. 1.2.3)"
  exit 1
fi

# 2. Tag already used check
if git rev-parse "v$VERSION" >/dev/null 2>&1; then
  echo "ERROR: Version $VERSION already exists as tag v$VERSION"
  echo "Bump version in pyproject.toml and frontend/package.json before merging."
  exit 1
fi

# 3. Frontend version must match (single source of truth: pyproject.toml)
FRONTEND_VERSION=$(grep -m1 '"version"' frontend/package.json | cut -d'"' -f4)
if [[ "$FRONTEND_VERSION" != "$VERSION" ]]; then
  echo "ERROR: frontend/package.json version ($FRONTEND_VERSION) does not match pyproject.toml ($VERSION)"
  echo "Keep both in sync."
  exit 1
fi

# 4. Version must be greater than latest tag (no downgrades)
LATEST_TAG=$(git tag -l 'v*' 2>/dev/null | sort -V | tail -1 || true)
if [[ -n "$LATEST_TAG" ]]; then
  # sort -V: if v$VERSION sorts before or equal to LATEST_TAG, we have a problem
  SORTED=$(printf '%s\n%s\n' "v$VERSION" "$LATEST_TAG" | sort -V)
  FIRST=$(echo "$SORTED" | head -1)
  if [[ "$FIRST" == "v$VERSION" ]] && [[ "v$VERSION" != "$LATEST_TAG" ]]; then
    echo "ERROR: Version $VERSION is lower than latest tag $LATEST_TAG"
    echo "Bump to a version greater than $LATEST_TAG"
    exit 1
  fi
fi

echo "Version check passed: $VERSION"
