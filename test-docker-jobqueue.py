import shutil
import sys

from dask.distributed import Client, performance_report
from dask_jobqueue import HTCondorCluster
import dask.array as da

if __name__ == "__main__":
    shutil.rmtree("logs", ignore_errors=True)

    worker_image, scheduler_port, num_workers = sys.argv[1:]
    scheduler_port = int(scheduler_port)
    num_workers = int(num_workers)

    with HTCondorCluster(
        cores=1,
        memory="1 GB",
        disk="1 GB",
        log_directory="logs",
        python="python3",
        scheduler_options={"dashboard_address": "3456", "port": scheduler_port},
        job_extra={
            "universe": "docker",
            "docker_image": worker_image,
            "container_service_names": "dask",
            "dask_container_port": "8787",
            "requirements": "(Target.HasCHTCStaging)",
            "keep_claim_idle": "3600",
        },
    ) as cluster, Client(cluster) as client:
        cluster.scale(num_workers)

        print(cluster)

        print(client)

        with performance_report(filename="report.html"):
            x = da.random.random((10000, 10000), chunks=1000)

            y = (x ** 2).sum()

            print("\nCOMPUTATION", y, "\n")

            z = y.compute()

            print("\nRESULT", z, "\n")
