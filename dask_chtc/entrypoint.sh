#!/usr/bin/env bash

set -xu

echo "Dask-CHTC entrypoint executing..."
echo "Incoming command is:"
echo "$@"
echo

# Make sure we're in the _CONDOR_SCRATCH_DIR
cd "$_CONDOR_SCRATCH_DIR" || exit 1
pwd

conda create --name worker --clone base --prefix "$_CONDOR_SCRATCH_DIR"/.env
conda activate "$_CONDOR_SCRATCH_DIR"/.env

# Install extra user-specified packages
conda_env=$(grep CondaEnv "$_CONDOR_JOB_AD" | cut -d'"' -f2)
if [ -n "$conda_env" ]; then
    echo "Updating conda environment..."
    env_file="$_CONDOR_SCRATCH_DIR"/environment.yml
    echo -e "$conda_env" > "$env_file"
    echo "Conda environment for update:"
    cat "$env_file"
    echo
    conda env update --file "$env_file"
fi

conda_packages=$(grep ExtraCondaPackages "$_CONDOR_JOB_AD" | cut -d'"' -f2)
if [ -n "$conda_packages" ]; then
    echo "Installing extra conda packages..."
    # We want the packages split into separate args
    # shellcheck disable=SC2086
    conda install --yes $conda_packages
fi

conda clean --all --yes

pip_packages=$(grep ExtraPipPackages "$_CONDOR_JOB_AD" | cut -d'"' -f2)
if [ -n "$pip_packages" ]; then
    echo "Installing extra pip packages..."
    # We want the packages split into separate args
    # shellcheck disable=SC2086
    pip install --user --no-cache-dir $pip_packages
fi

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
