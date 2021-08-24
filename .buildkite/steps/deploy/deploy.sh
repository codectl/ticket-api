#!/usr/bin/env bash

set -euo pipefail

if ! kubectl get deployment --selector app=ticket-api ||
  ! kubectl get pod --selector app=ticket-bridge; then
  echo "--- :boom: Missing resources"
  exit 1
fi

# create kustomization context
cwd=$(pwd)
tmpdir=$(mktemp -dt tmp.deploy.XXXXXX)
cd "$tmpdir"

basedir=".kustomization/components"
rsync "${cwd}/${basedir}/api/deployment.yaml" api/
rsync "${cwd}/${basedir}/bridge/pod.yaml" bridge/
newImage="${REGISTRY}/${REGISTRY_REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG}"

# set kustomization file used to restart services
kustomize create
kustomize edit add resource api/deployment.yaml
kustomize edit add resource bridge/pod.yaml
kustomize edit set image "${IMAGE_NAME}=${newImage}"

# restart api & bridge service
kustomize build . | kubectl replace --force -f -

# wait service conclusion
kubectl wait --for condition=ready --timeout=300s --selector app=ticket-api pod
kubectl wait --for condition=ready --timeout=300s --selector app=ticket-bridge pod

# print out initial logs
kubectl logs --selector app=ticket-api
kubectl logs --selector app=ticket-bridge

# cleanup
cd "$cwd"
rm -rf -- "$tmpdir"
