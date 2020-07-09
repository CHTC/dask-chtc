FROM pytorch/pytorch:1.5.1-cuda10.1-cudnn7-runtime

# Install various extra Python packages we want to be available
RUN : \
 && conda install --yes \
    dask \
    dask-ml \
    lz4 \
    python-blosc \
    tini \
 && conda install --yes \
    -c conda-forge \
    skorch \
 && conda clean --yes --all \
 && :

# Without tini, condor_rm will fail to clean up worker jobs because
# they never see the signal.
ENTRYPOINT ["tini", "--"]
