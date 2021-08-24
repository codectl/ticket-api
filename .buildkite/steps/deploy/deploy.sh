#!/usr/bin/env bash

set -euo pipefail

if ! kubectl get deployment --selector app=ticket-api ||
  ! kubectl get pod --selector app=ticket-bridge; then
  echo "--- :boom: Missing resources"
  exit 1
else
  # base location for services
  basedir=.kustomization/components/

  # restart services
  kubectl replace --force -f "${basedir}/api/deployment.yaml"
  kubectl replace --force -f "${basedir}/bridge/pod.yaml"
fi
