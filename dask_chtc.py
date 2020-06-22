import shutil
import sys
import contextlib

from dask.distributed import Client, performance_report
from dask_jobqueue import HTCondorCluster
import dask.array as da


@contextlib.contextmanager
def CHTCCluster():
    shutil.rmtree("logs", ignore_errors=True)

    worker_image, scheduler_port = sys.argv[1:]
    scheduler_port = int(scheduler_port)

    with HTCondorCluster(
        cores=1,
        memory="1 GB",
        disk="1 GB",
        log_directory="logs",
        python="python3",
        scheduler_options={"dashboard_address": "3400", "port": scheduler_port},
        job_extra={
            "universe": "docker",
            "docker_image": worker_image,
            "container_service_names": "dask",
            "dask_container_port": "8787",
            "requirements": "(Target.HasCHTCStaging)",
            "keep_claim_idle": "3600",
        },
    ) as cluster:
        yield cluster
