FROM daskdev/dask:latest

COPY entrypoint.sh /.entrypoint.sh
RUN chmod +x /.entrypoint.sh

ENTRYPOINT ["tini", "-g", "--", "/.entrypoint.sh"]
