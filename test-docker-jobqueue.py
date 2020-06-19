import time
import shutil
from pprint import pprint
import sys

import dask
from dask.distributed import Client, performance_report, progress
from dask_jobqueue import HTCondorCluster
import dask.array as da

if __name__ == "__main__":
    shutil.rmtree("logs", ignore_errors=True)

    with HTCondorCluster(
        cores=1,
        memory="1 GB",
        disk="1 GB",
        log_directory="logs",
        silence_logs="debug",
        python="python3",
        # dealing with CHTC quirks:
        # we happen to have these ports open on submit3 for connection from machines that can see staging
        scheduler_options={"dashboard_address": "3456", "port": 3457},
        job_extra={
            "universe": "docker",
            "docker_image": sys.argv[1],
            "container_service_names": "dask",
            "dask_container_port": "8787",
            "requirements": "(Target.HasCHTCStaging)",
        },
    ) as cluster, Client(cluster) as client:
        cluster.scale(10)
        time.sleep(5)

        print(cluster)

        print(client)

        with performance_report(filename="report.html"):
            x = da.random.random((10000, 10000), chunks=(100, 100))

            y = (x ** 2).sum()

            print(y)

            z = y.compute()
            progress(z)

            print(z)

        time.sleep(5)
