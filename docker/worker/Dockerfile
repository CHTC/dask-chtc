FROM daskdev/dask:latest

COPY entrypoint.sh /.entrypoint.sh
RUN chmod +x /.entrypoint.sh

COPY logging.yaml ${HOME}/.config/dask/logging.yaml

ENTRYPOINT ["tini", "-g", "--", "/.entrypoint.sh"]

RUN : \
 && conda install -y -c conda-forge dask-ml skorch \
 && conda install -y -c pytorch pytorch cudatoolkit=10.1  \
 && conda clean --all -y \
 && :
