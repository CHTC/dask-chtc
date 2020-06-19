import time

from dask_jobqueue import HTCondorCluster
from dask.distributed import Client, performance_report, progress
import dask.array as da

if __name__ == "__main__":
    with HTCondorCluster(
        cores=1, memory="1 GB", disk="1 GB", log_directory="logs", silence_logs="debug",
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
