#!/usr/bin/env bash

set -x

echo "Dask-CHTC entrypoint executing..."
echo "Incoming command is:"
echo "$@"
echo

# Wait for the job ad to be updated with <service>_HostPort
# This happens during the first update, usually a few seconds after the job starts
echo "Waiting for HostPort information..."
while true; do
  if grep HostPort "$_CONDOR_JOB_AD"; then
    break
  fi
  sleep 1
done
echo "Got HostPort, proceeding..."
echo

echo "JobAd contents:"
cat "$_CONDOR_JOB_AD"
echo

# Get host and port information from the job ad.
# Because we are inside a Docker container and not on the host network,
# we need to tell the scheduler how to contact us.
# (It isn't the address we would naively detect from inside!)
HOST=$(grep RemoteHost "$_CONDOR_JOB_AD" | tr -d '"' | tr '@' ' ' | awk '{print $NF;}')
PORT=$(grep HostPort "$_CONDOR_JOB_AD" | tr -d '"' | awk '{print $NF;}')
echo "HOST is $HOST"
echo "PORT is $PORT"
echo

# Paths to TLS config files, transferred to the worker by HTCondor file transfer.
FILE_CA="$_CONDOR_SCRATCH_DIR/ca.pem"
FILE_CERT="$_CONDOR_SCRATCH_DIR/cert.pem"
FILE_KEY="$_CONDOR_SCRATCH_DIR/cert.pem"

# Add the contact address we calculated above to the worker arguments,
# as well as TLS configuration.
exec "$@" \
  --contact-address tls://"$HOST":"$PORT" \
  --tls-ca-file "$FILE_CA" --tls-cert "$FILE_CERT" --tls-key "$FILE_KEY"
