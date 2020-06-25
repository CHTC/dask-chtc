#!/usr/bin/env bash

set -e

TAG=$1

docker build --pull -t "${TAG}" docker/worker
docker push "${TAG}"
