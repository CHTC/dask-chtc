FROM daskdev/dask:latest

COPY entrypoint.sh /.entrypoint.sh
RUN chmod +x /.entrypoint.sh

COPY logging.yaml ${HOME}/.config/dask/logging.yaml

RUN : \
 && conda install -y dask-ml \
 && conda clean --all -y \
 && :

ENTRYPOINT ["tini", "-g", "--", "/.entrypoint.sh"]
