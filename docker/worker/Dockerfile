FROM pytorch/pytorch:1.5.1-cuda10.1-cudnn7-runtime

COPY logging.yaml ${HOME}/.config/dask/logging.yaml

RUN : \
 && conda install --yes \
    dask \
    dask-ml \
    lz4 \
    python-blosc \
    tini \
 && conda clean --yes --all \
 && :
