#!/usr/bin/env bash

set -x

echo "entrypoint"
echo "incoming command is"
echo "$@"
echo

if [[ -f $_CONDOR_JOB_AD ]]; then
  PORT=$(cat $_CONDOR_JOB_AD | grep HostPort | tr -d '"' | awk '{print $NF;}')
  HOST=$(cat $_CONDOR_JOB_AD | grep RemoteHost | tr -d '"' | tr '@' ' ' | awk '{print $NF;}')
fi

if [[ "$*" == *'distributed.cli.dask_worker'* ]]; then
  exec $@ --contact-address tcp://$HOST:$PORT --listen-address tcp://0.0.0.0:8787
else
  exec $@
fi
