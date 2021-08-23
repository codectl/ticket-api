#!/usr/bin/env bash

set -euo pipefail

# validate env parameters
if [[ ! -v NAMESPACE ]]; then
  echo "--- :boom: Missing 'NAMESPACE'" 1>&2
  exit 1
fi

# temporary files
tmpdir=$(mktemp -d)
manifest="${tmpdir}/manifest.yaml"

# setup kustomization file
NAMESPACE="$NAMESPACE" \
  envsubst <"$(dirname "$0")/templates/kustomization.yaml" >"${manifest}"

kubectl kustomize "$manifest" | kubectl replace -f -
