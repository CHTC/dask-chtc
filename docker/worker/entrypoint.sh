#!/usr/bin/env bash

set -x

echo "entrypoint"
echo "incoming command is"
echo "$@"
echo

if [[ "$*" == *'distributed.cli.dask_worker'* ]]; then
  if [[ -f $_CONDOR_JOB_AD ]]; then
    echo "job ad is"
    cat $_CONDOR_JOB_AD
    echo

    HOST=$(cat $_CONDOR_JOB_AD | grep RemoteHost | tr -d '"' | tr '@' ' ' | awk '{print $NF;}')
    echo "HOST is $HOST"
    echo
  fi

  # strip off "/bin/sh -c"
  shift
  shift

  exec $@ --contact-address tcp://$HOST:8787 --listen-address tcp://0.0.0.0:8787
else
  exec $@
fi
