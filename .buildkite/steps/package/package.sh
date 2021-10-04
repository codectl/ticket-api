#!/usr/bin/env bash

set -euo pipefail

# package repository into tar.gz file
tarfile="${IMAGE_NAME}:${IMAGE_TAG}.tar.gz"
git archive --verbose --format tar.gz --output "$tarfile" HEAD

jfrog rt upload \
--url "https://${REGISTRY}" \
--user "$REGISTRY_USER" \
--apikey "$REGISTRY_TOKEN" \
--insecure-tls \
-- "$tarfile" "artifactory/${REGISTRY_REPOSITORY}/${tarfile}"

# upload to buildkite artifactory (for reference only)
buildkite-agent artifact upload "$tarfile"
