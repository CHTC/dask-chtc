#!/usr/bin/env bash

set -e

TAG=maventree/dask-worker:$1

docker build --pull -t "${TAG}" docker/worker
docker push "${TAG}"
