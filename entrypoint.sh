#!/usr/bin/env bash

set -x

echo "Entrypoint executing..."
echo "Incoming command is:"
echo "$@"
echo

# wait for the job ad to be updated with <service>_HostPort
echo "Waiting for HostPort information..."
while true; do
  if grep HostPort "$_CONDOR_JOB_AD"; then
    break
  fi
  sleep 0.1
done
echo "Got HostPort, proceeding..."
echo

echo "JobAd contents:"
cat "$_CONDOR_JOB_AD"
echo

# Get host and port information from the job ad.
# Because we are inside a Docker container and not on the host network,
# we need to tell the scheduler how to contact us.
HOST=$(cat "$_CONDOR_JOB_AD" | grep RemoteHost | tr -d '"' | tr '@' ' ' | awk '{print $NF;}')
PORT=$(cat "$_CONDOR_JOB_AD" | grep HostPort | tr -d '"' | awk '{print $NF;}')
echo "HOST is $HOST"
echo "PORT is $PORT"
echo

# Add contact address to tell the scheduler where to contact us.
exec $@ --contact-address tcp://"$HOST":"$PORT"
