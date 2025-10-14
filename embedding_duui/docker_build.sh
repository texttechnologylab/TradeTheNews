#!/usr/bin/env bash
set -euo pipefail

export ANNOTATOR_NAME=embeddings
export ANNOTATOR_VERSION=1
export DOCKER_REGISTRY="org.ttlab/"

docker build \
  --build-arg ANNOTATOR_NAME \
  --build-arg ANNOTATOR_VERSION \
  -t ${DOCKER_REGISTRY}${ANNOTATOR_NAME}:${ANNOTATOR_VERSION} \
  -f Dockerfile .

docker tag \
  ${DOCKER_REGISTRY}${ANNOTATOR_NAME}:${ANNOTATOR_VERSION} \
  ${DOCKER_REGISTRY}${ANNOTATOR_NAME}:latest
