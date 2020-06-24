FROM pytorch/pytorch:1.1.0-cuda10.0-cudnn7.5-runtime

COPY entrypoint.sh /.entrypoint.sh
RUN chmod +x /.entrypoint.sh

COPY logging.yaml ${HOME}/.config/dask/logging.yaml

ENTRYPOINT ["tini", "-g", "--", "/.entrypoint.sh"]

RUN : \
 && conda install --yes \
#    -c conda-forge \
    python=3.8 \
    python-blosc \
#    cytoolz \
    dask \
    dask-ml \
    lz4 \
#    pandas \
    tini==0.18.0 \
 && conda clean --all -y \
 && :
