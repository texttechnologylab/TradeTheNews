#!/usr/bin/env bash
set -euo pipefail

export ANNOTATOR_NAME=llm-impact-scorer
export ANNOTATOR_VERSION=0.1
export DOCKER_REGISTRY="org.ttlab/"

docker build \
  -t ${DOCKER_REGISTRY}${ANNOTATOR_NAME}:${ANNOTATOR_VERSION} \
  -f Dockerfile .

docker tag \
  ${DOCKER_REGISTRY}${ANNOTATOR_NAME}:${ANNOTATOR_VERSION} \
  ${DOCKER_REGISTRY}${ANNOTATOR_NAME}:latest